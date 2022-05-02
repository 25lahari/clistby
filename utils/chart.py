from datetime import datetime

from django.db.models import F, FloatField, IntegerField
from django.db.models.fields.related import RelatedField
from django.db.models.functions import Cast
from django_pivot.histogram import get_column_values, histogram

from clist.templatetags.extras import title_field
from utils.json_field import JSONF
from utils.math import get_divisors


def make_bins(src, dst, n_bins, logger=None, field=None, step=None):
    if isinstance(src, str):
        if not dst:
            logger and logger.warning(f'One of border is empty, field = {field}')
            return
        st = ord(src[0]) + 1 if src else 32
        fn = ord(dst[0])
        bins = [src] + [chr(int(round(st + (fn - st) * i / (n_bins - 1)))) for i in range(n_bins)] + [dst]
    else:
        if step is not None:
            src -= src % step
            dst += (step - dst % step) % step
            delta = (dst - src) / (n_bins - 1)
            for divisor in get_divisors(step, reverse=True):
                if divisor <= delta:
                    n_bins = (dst - src) // divisor + 1
                    break
        bins = [src + (dst - src) * i / (n_bins - 1) for i in range(n_bins)]
    if isinstance(src, int):
        bins = [int(round(b)) for b in bins]
    elif isinstance(src, float):
        bins = [round(b, 2) for b in bins]
    bins = list(sorted(set(bins)))
    if isinstance(src, int) and len(bins) < n_bins:
        bins.append(bins[-1] + 1)
    elif len(bins) == 1:
        bins.append(bins[-1])
    return bins


def make_histogram(values, n_bins=None, bins=None, src=None, dst=None, deltas=None):
    if bins is None:
        if src is None:
            src = min(values)
        if dst is None:
            dst = max(values)
        bins = make_bins(src, dst, n_bins)
    idx = 0
    ret = [0] * (len(bins) - 1)
    if deltas is None:
        deltas = [1] * len(values)
    for x, delta in sorted(zip(values, deltas)):
        while idx + 1 < len(bins) and bins[idx + 1] <= x:
            idx += 1
        if idx == len(ret):
            if bins[idx] == x:
                idx -= 1
            else:
                break
        ret[idx] += delta
    return ret, bins


def make_chart(qs, field, groupby=None, logger=None, n_bins=50, cast=None, step=None):
    context = {'title': title_field(field) + (f' (slice by {groupby})' if groupby else '')}

    if cast == 'int':
        cast = IntegerField()
    elif cast == 'float':
        cast = FloatField()
    else:
        cast = None

    if '__' in field:
        related_fields = set()
        for f in qs.model._meta.related_objects:
            related_fields.add(f.name)
        for f in qs.model._meta.many_to_many:
            related_fields.add(f.name)
        for f in qs.model._meta.fields:
            if isinstance(f, RelatedField):
                related_fields.add(f.name)

        related_field = field.split('__')[0]
        if related_field in related_fields or '___' in field:
            logger and logger.error(f'use of an invalid field = {field}')
            return
        cast = cast or IntegerField()
        qs = qs.annotate(value=Cast(JSONF(field), cast))
    else:
        if cast:
            qs = qs.annotate(value=Cast(F(field), cast))
        else:
            qs = qs.annotate(value=F(field))
    context['queryset'] = qs
    context['field'] = field

    qs = qs.filter(value__isnull=False)

    slice_on = None
    if groupby == 'resource':
        slice_on = 'resource__host'
    elif groupby == 'country':
        slice_on = 'country'

    if slice_on:
        values = get_column_values(qs, slice_on, choices='minimum')
        fields = [f for f, v in values]
        n_bins = max(2 * n_bins // len(fields) + 1, 4)
        context['fields'] = fields
        context['slice'] = slice_on

    if not qs.exists():
        logger and logger.warning(f'Empty histogram, field = {field}')
        return

    src = qs.earliest('value').value
    dst = qs.latest('value').value
    bins = make_bins(src=src, dst=dst, n_bins=n_bins, logger=logger, field=field, step=step)

    if isinstance(src, datetime):
        context['x_type'] = 'time'

    context['data'] = histogram(qs, 'value', bins=bins, slice_on=slice_on, choices='minimum')
    return context
