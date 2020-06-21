# -*- coding: utf-8 -*-

import re
import json
import requests
import html
from copy import deepcopy
from datetime import timedelta, datetime
from time import time, sleep
from hashlib import sha512
from pprint import pprint
from urllib.parse import urlencode, urljoin
from string import ascii_lowercase
from random import choice
from collections import OrderedDict

import pytz

from ranking.management.modules.common import REQ, BaseModule, FailOnGetResponse
from ranking.management.modules.excepts import ExceptionParseStandings, InitModuleException
from ranking.management.modules import conf


API_KEYS = conf.CODEFORCES_API_KEYS
DEFAULT_API_KEY = API_KEYS[API_KEYS['__default__']]


def _query(
    method,
    params,
    api_key=DEFAULT_API_KEY,
    prev_time_queries={},
    api_url_format='https://codeforces.com/api/%s'
):
    url = api_url_format % method
    key, secret = api_key
    params = dict(params)

    params.update({
        'time': int(time()),
        'apiKey': key,
        'lang': 'en',
    })

    url_encode = '&'.join(('%s=%s' % (k, v) for k, v in sorted(params.items())))

    api_sig_prefix = ''.join(choice(ascii_lowercase) for x in range(6))
    api_sig = '%s/%s?%s#%s' % (
        api_sig_prefix,
        method,
        url_encode,
        secret,
    )
    params['apiSig'] = api_sig_prefix + sha512(api_sig.encode('utf8')).hexdigest()
    url += '?' + urlencode(params)

    times = prev_time_queries.setdefault((key, secret), [])
    if len(times) == 5:
        delta = max(2 - (time() - times[0]), 0)
        sleep(delta)
        times.clear()

    md5_file_cache = url
    for k in ('apiSig', 'time', ):
        md5_file_cache = re.sub('%s=[0-9a-z]+' % k, '', md5_file_cache)
    times.append(time())
    try:
        page = REQ.get(url, md5_file_cache=md5_file_cache)
        ret = json.loads(page)
    except FailOnGetResponse as e:
        ret = json.load(e.args[0].fp)
        ret['code'] = getattr(e.args[0], 'code', None)
    times[-1] = time()
    return ret


class Statistic(BaseModule):
    PARTICIPANT_TYPES = ['CONTESTANT', 'OUT_OF_COMPETITION']
    SUBMISSION_URL_FORMAT_ = '{url}/submission/{sid}'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        cid = self.key
        if ':' in cid:
            cid, api = cid.split(':', 1)
            self.api_key = api.split(':') if ':' in api else API_KEYS[api]
        else:
            self.api_key = DEFAULT_API_KEY
        if not re.match('^[0-9]+$', cid):
            raise InitModuleException(f'Contest id {cid} should be number')
        self.cid = cid

    def get_standings(self, users=None, statistics=None):

        contest_url = self.url.replace('contests', 'contest')
        standings_url = contest_url.rstrip('/') + '/standings'

        is_gym = '/gym/' in self.url
        result = {}

        problems_info = OrderedDict()
        for unofficial in [True]:
            params = {
                'contestId': self.cid,
                'showUnofficial': str(unofficial).lower(),
            }
            if users:
                params['handles'] = ';'.join(users)

            data = _query(method='contest.standings', params=params, api_key=self.api_key)

            if data['status'] != 'OK':
                if data['code'] == 400:
                    return {'action': 'delete'}
                raise ExceptionParseStandings(data['status'])

            phase = data['result']['contest'].get('phase', 'FINISHED').upper()
            contest_type = data['result']['contest']['type'].upper()
            duration_seconds = data['result']['contest'].get('durationSeconds')

            result_problems = data['result']['problems']
            for p in result_problems:
                d = {'short': p['index'], 'name': p['name']}
                if 'points' in p:
                    d['full_score'] = p['points']
                elif contest_type == 'IOI':
                    d['full_score'] = 100
                tags = p.get('tags')
                if tags:
                    d['tags'] = tags
                d['url'] = urljoin(standings_url.rstrip('/'), f"problem/{d['short']}")

                problems_info[d['short']] = d

            if users is not None and not users:
                continue

            grouped = any(
                'teamId' in row['party'] and row['party']['participantType'] in self.PARTICIPANT_TYPES
                for row in data['result']['rows']
            )

            place = None
            last = None
            idx = 0
            for row in data['result']['rows']:
                party = row['party']

                if is_gym and not party['members']:
                    is_ghost_team = True
                    name = party['teamName']
                    party['members'] = [{
                        'handle': f'{name} {self.get_season()}',
                        'name': name,
                    }]
                else:
                    is_ghost_team = False

                for member in party['members']:
                    if is_gym:
                        upsolve = False
                    else:
                        upsolve = party['participantType'] not in self.PARTICIPANT_TYPES

                    handle = member['handle']

                    r = result.setdefault(handle, OrderedDict())

                    r['member'] = handle
                    if 'room' in party:
                        r['room'] = str(party['room'])

                    r.setdefault('participant_type', []).append(party['participantType'])
                    r['_no_update_n_contests'] = all(pt not in r['participant_type'] for pt in r['participant_type'])

                    if is_ghost_team:
                        r['name'] = member['name']
                        r['_no_update_name'] = True
                    elif grouped and (not upsolve and not is_gym or 'name' not in r):
                        r['name'] = ', '.join(m['handle'] for m in party['members'])
                        if 'teamId' in party:
                            r['team_id'] = party['teamId']
                            r['name'] = f"{party['teamName']}: {r['name']}"
                        r['_no_update_name'] = True

                    hack = row['successfulHackCount']
                    unhack = row['unsuccessfulHackCount']

                    problems = r.setdefault('problems', {})
                    for i, s in enumerate(row['problemResults']):
                        k = result_problems[i]['index']
                        points = float(s['points'])

                        n = s.get('rejectedAttemptCount')
                        if n is not None and contest_type == 'ICPC' and points + n > 0:
                            points = f'+{"" if n == 0 else n}' if points > 0 else f'-{n}'

                        u = upsolve
                        if s['type'] == 'FINAL' and (points or n):
                            if not points:
                                points = f'-{n}'
                                n = None
                            p = {'result': points}
                            if contest_type == 'IOI':
                                full_score = problems_info[k].get('full_score')
                                if full_score:
                                    p['partial'] = points < full_score
                            elif contest_type == 'CF' and n:
                                p['penalty_score'] = n
                        elif s['type'] == 'PRELIMINARY':
                            p = {'result': f'?{n + 1}'}
                        else:
                            continue

                        if 'bestSubmissionTimeSeconds' in s and duration_seconds:
                            time = s['bestSubmissionTimeSeconds']
                            if time > duration_seconds:
                                u = True
                            else:
                                time /= 60
                                p['time'] = '%02d:%02d' % (time / 60, time % 60)
                        a = problems.setdefault(k, {})
                        if u:
                            a['upsolving'] = p
                        else:
                            a.update(p)

                    if row['rank'] and not upsolve:
                        if unofficial:
                            if users:
                                r['place'] = '__unchanged__'
                            else:
                                idx += 1
                                value = (row['points'], row.get('penalty'))
                                if last != value:
                                    value = last
                                    place = idx
                                r['place'] = place
                        else:
                            r['place'] = row['rank']
                        r['solving'] = row['points']
                        if contest_type == 'ICPC':
                            r['penalty'] = row['penalty']

                    if hack or unhack:
                        r['hack'] = {
                            'title': 'hacks',
                            'successful': hack,
                            'unsuccessful': unhack,
                        }

        params.pop('showUnofficial')

        data = _query(method='contest.ratingChanges', params=params, api_key=self.api_key)
        if data.get('status') not in ['OK', 'FAILED']:
            raise ExceptionParseStandings(data)
        if data and data['status'] == 'OK':
            for row in data['result']:
                if str(row.pop('contestId')) != self.key:
                    continue
                handle = row.pop('handle')
                if handle not in result:
                    continue
                r = result[handle]
                old_rating = row.pop('oldRating')
                new_rating = row.pop('newRating')
                r['old_rating'] = old_rating
                r['new_rating'] = new_rating

        params = {'contestId': self.cid}
        if users:
            array_params = []
            for user in users:
                params['handle'] = user
                array_params.append(deepcopy(params))
        else:
            array_params = [params]

        submissions = []
        for params in array_params:
            data = _query('contest.status', params=params, api_key=self.api_key)
            if data.get('status') not in ['OK', 'FAILED']:
                raise ExceptionParseStandings(data)
            if data['status'] == 'OK':
                submissions.extend(data['result'])

        for submission in submissions:
            party = submission['author']

            info = {
                'submission_id': submission['id'],
                'url': Statistic.SUBMISSION_URL_FORMAT_.format(url=contest_url, sid=submission['id']),
                'external_solution': True,
            }

            if 'verdict' in submission:
                v = submission['verdict'].upper()
                info['verdict'] = ''.join(s[0] for s in v.split('_')) if len(v) > 3 else v

            if 'programmingLanguage' in submission:
                info['language'] = submission['programmingLanguage']

            if info.get('verdict') != 'OK' and 'passedTestCount' in submission:
                info['test'] = submission['passedTestCount'] + 1

            if is_gym:
                upsolve = False
            else:
                upsolve = party['participantType'] not in self.PARTICIPANT_TYPES

            if (
                'relativeTimeSeconds' in submission
                and duration_seconds
                and duration_seconds < submission['relativeTimeSeconds']
            ):
                upsolve = True

            for member in party['members']:
                handle = member['handle']
                if handle not in result:
                    continue
                r = result[handle]
                problems = r.setdefault('problems', {})
                k = submission['problem']['index']
                p = problems.setdefault(k, {})
                if upsolve:
                    p = p.setdefault('upsolving', {})
                if 'submission_id' not in p:
                    p.update(info)

        def to_score(x):
            return (
                (1 if x.startswith('+') or not x.startswith('?') and float(x) > 0 else 0)
                if isinstance(x, str) else x
            )

        def to_solve(x):
            return not x.get('partial', False) and to_score(x.get('result', 0)) > 0

        for r in result.values():
            upsolving = 0
            solving = 0
            upsolving_score = 0

            for a in r['problems'].values():
                if 'upsolving' in a and to_solve(a['upsolving']) > to_solve(a):
                    upsolving_score += to_score(a['upsolving']['result'])
                    upsolving += to_solve(a['upsolving'])
                else:
                    solving += to_solve(a)
            r.setdefault('solving', 0)
            r['upsolving'] = upsolving_score
            if abs(solving - r['solving']) > 1e-9 or abs(upsolving - r['upsolving']) > 1e-9:
                r['solved'] = {
                    'solving': solving,
                    'upsolving': upsolving,
                }

        standings = {
            'result': result,
            'url': standings_url,
            'problems': list(problems_info.values()),
            'options': {
                'fixed_fields': [('hack', 'Hacks')],
            },
        }

        if phase != 'FINISHED' and self.end_time + timedelta(hours=3) > datetime.utcnow().replace(tzinfo=pytz.utc):
            standings['timing_statistic_delta'] = timedelta(minutes=15)
        return standings

    @staticmethod
    def get_users_infos(users, resource=None, accounts=None, pbar=None):
        handles = ';'.join(users)

        len_limit = 1000
        if len(handles) > len_limit:
            s = 0
            for i in range(len(users)):
                s += len(users[i])
                if s > len_limit:
                    return Statistic.get_users_infos(users[:i], pbar) + Statistic.get_users_infos(users[i:], pbar)

        removed = []
        last_index = 0
        orig_users = list(users)
        while True:
            try:
                handles = ';'.join(users)
                data = _query(method='user.info', params={'handles': handles})
            except FailOnGetResponse as e:
                page = e.args[0].read()
                data = json.loads(page)
            if data['status'] == 'OK':
                break
            if data['status'] == 'FAILED' and data['comment'].startswith('handles: User with handle'):
                handle = data['comment'].split()[-3]
                response = requests.head(f'https://codeforces.com/profile/{handle}')
                location = response.headers['Location']
                target = location.split('/')[-1]
                index = users.index(handle)
                if location.endswith('//codeforces.com/'):
                    removed.append((index, users[index]))
                    users.pop(index)
                else:
                    users[index] = target
                if pbar is not None:
                    pbar.update(index - last_index)
                    last_index = index
            else:
                raise NameError(f'data = {data}')
        if pbar is not None:
            pbar.update(len(users) - last_index)

        infos = data['result']
        for index, user in removed:
            infos.insert(index, None)
            users.insert(index, user)

        ret = []
        assert len(infos) == len(users)
        for data, user, orig in zip(infos, users, orig_users):
            if data and data['handle'].lower() != user.lower():
                raise ValueError(f'Do not match handle name for user = {user} and data = {data}')
            ret.append({'info': data})
            if data['handle'] != orig:
                ret[-1]['rename'] = data['handle']
        return ret

    @staticmethod
    def get_source_code(contest, problem):
        if 'url' not in problem:
            raise ExceptionParseStandings('Not found url')

        page = REQ.get(problem['url'])
        match = re.search('<pre[^>]*id="program-source-text"[^>]*class="(?P<class>[^"]*)"[^>]*>(?P<source>[^<]*)</pre>', page)  # noqa
        if not match:
            raise ExceptionParseStandings('Not found source code')
        solution = html.unescape(match.group('source'))
        ret = {'solution': solution}
        for c in match.group('class').split():
            if c.startswith('lang-'):
                ret['lang_class'] = c
        return ret


if __name__ == '__main__':
    pprint(Statistic(url='https://codeforces.com/contest/1119/', key='1119').get_result('tourist'))
    pprint(Statistic(url='https://codeforces.com/contest/1270/', key='1270').get_result('CodeMazz'))
    pprint(Statistic(url='https://codeforces.com/contest/1200/', key='1200').get_result('hloya_ygrt'))
    pprint(Statistic(url='https://codeforces.com/contest/1200/', key='1200').get_result('rui-de'))
    pprint(Statistic(url='https://codeforces.com/contest/1164/', key='1164').get_result('abisheka'))
    pprint(Statistic(url='https://codeforces.com/contest/1202', key='1202').get_result('kmjp'))
    pprint(Statistic(url='https://codeforces.com/contest/1198', key='1198').get_result('yosupo'))
    pprint(Statistic(url='https://codeforces.com/contest/1198', key='1198').get_result('tourist'))
    pprint(Statistic(url='https://codeforces.com/contest/1160/', key='1160').get_result('Rafbill'))
    pprint(Statistic(url='https://codeforces.com/contest/1/', key='1').get_result('spartac'))
    pprint(Statistic(url='https://codeforces.com/contest/1250/', key='1250').get_result('maroonrk'))
    pprint(Statistic(url='https://codeforces.com/contest/1250/', key='1250').get_result('sigma425'))
