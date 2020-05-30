<?php
    require_once dirname(__FILE__) . '/../../config.php';

    if (!isset($URL)) $URL = 'https://www.bubblecup.org/CompetitorsCorner/Problems';
    if (!isset($HOST)) $HOST = parse_url($URL, PHP_URL_HOST);
    if (!isset($RID)) $RID = -1;
    if (!isset($LANG)) $LANG = 'RU';
    if (!isset($TIMEZONE)) $TIMEZONE = 'UTC';
    if (!isset($contests)) $contests = array();

    $url = 'https://www.bubblecup.org/_api/competitionInfo';
    $data = curlexec($url, NULL, array('json_output' => true));

    if (!isset($data['rounds'])) {
        return;
    }

    foreach ($data['rounds'] as $round) {
        if (!preg_match(
            '#
                start\s+date\s+(?:<b[^>]*>)?(?P<start_time>[^<]*)(?:</b>)?.*?
                end\s+date\s+(?:<b[^>]*>)?(?P<end_time>[^<]*)
            #ix',
            $round['description'],
            $match
        )) {
            continue;
        }

        $year = strftime('%Y', strtotime($match['start_time']));
        $month = intval(strftime('%m', strtotime($match['start_time'])));
        if ($month >= 9) {
            $year = $year + 1;
        }
        $key = ($year - 1) . "-" . $year . " " . $round['name'];

        $contests[] = array(
            'start_time' => $match['start_time'],
            'end_time' => $match['end_time'],
            'title' => $round['name'],
            'url' => $URL,
            'host' => $HOST,
            'rid' => $RID,
            'timezone' => $TIMEZONE,
            'key' => $key
        );
    }

    if ($RID === -1) {
        print_r($contests);
    }
?>