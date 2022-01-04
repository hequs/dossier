from array import array
from bisect import bisect_left
from collections import defaultdict
from enum import Enum
from math import exp
from numpy.linalg import norm

import numpy as np



class BaseCT(int, Enum):
    def __repr__(self):
        return 'CT_' + self.name


class BaseOT(int, Enum):
    def __repr__(self):
        return 'OT_' + self.name


class BaseRT(int, Enum):
    def __repr__(self):
        return 'RT_' + self.name


class RT(BaseRT):
    SUM = 0
    D1 = 1
    D7 = 2
    D30 = 3
    D180 = 4


ONE_DAY_SECONDS = 86400
LN_2 = 0.693147180


def _calc_decay(reducer_type, timestamp_delta):
    if reducer_type == RT.SUM or timestamp_delta == 0.0:
        return 1.0
    halflife = 0
    if reducer_type == RT.D1:
        halflife = 1 * ONE_DAY_SECONDS
    elif reducer_type == RT.D7:
        halflife = 7 * ONE_DAY_SECONDS
    elif reducer_type == RT.D30:
        halflife = 30 * ONE_DAY_SECONDS
    elif reducer_type == RT.D180:
        halflife = 180 * ONE_DAY_SECONDS
    else:
        raise 'unsupported reduce'
    return exp(-LN_2 * timestamp_delta / halflife)


def _value_at(reducer_type, x, x_timestamp, timestamp):
    assert timestamp >= x_timestamp, "timestamp < x_timestamp"
    return _reduce(reducer_type, x, x_timestamp, 0.0, timestamp)


def _reduce(reducer_type, x, x_timestamp, y, y_timestamp):
    if x_timestamp > y_timestamp:
        x, y, x_timestamp, y_timestamp = y, x, y_timestamp, x_timestamp
    return x * _calc_decay(reducer_type, float(y_timestamp - x_timestamp)) + y


class CounterKey:
    def __init__(self, object_type, counter_type, reducer_type):
        assert issubclass(type(object_type), BaseOT)
        assert issubclass(type(counter_type), BaseCT)
        assert isinstance(reducer_type, RT)
        self.object_type = object_type
        self.counter_type = counter_type
        self.reducer_type = reducer_type

    def as_tuple(self):
        return (self.object_type, self.counter_type, self.reducer_type)

    def __repr__(self):
        return str(self.as_tuple())

    def __hash__(self):
        return hash(self.as_tuple())

    def __eq__(self, other):
        return self.as_tuple() == other.as_tuple()


class CounterValues:
    def __init__(self):
        self.object_ids = list()
        self.values = array('f')
        self.timestamps = array('i')

    def __repr__(self):
        return str(dict(zip(self.object_ids, zip(self.values, self.timestamps))))

    # converts inner data to np.array type for further efficient processing
    def freeze(self):
        self.object_ids = np.array(self.object_ids)
        self.values = np.array(self.values)
        self.timestamps = np.array(self.timestamps)

    def reduce(self, reducer_type, timestamp):
        for index in range(len(self.object_ids)):
            self.values[index] = _value_at(reducer_type, self.values[index], self.timestamps[index], timestamp)
            self.timestamps[index] = timestamp

    def update(self, object_id, reducer_type, value, timestamp):
        index = bisect_left(self.object_ids, object_id)
        if index < len(self.object_ids) and self.object_ids[index] == object_id:
            self.values[index] = _reduce(reducer_type, self.values[index], self.timestamps[index], value, timestamp)
            self.timestamps[index] = max(timestamp, self.timestamps[index])
        else:
            self.object_ids.insert(index, object_id)
            self.values.insert(index, value)
            self.timestamps.insert(index, timestamp)

    def value(self, object_id, default=None):
        index = bisect_left(self.object_ids, object_id)
        if index < len(self.object_ids) and self.object_ids[index] == object_id:
            return self.values[index]
        return default

    def value_at(self, object_id, reducer_type, timestamp, default=None):
        index = bisect_left(self.object_ids, object_id)
        if index < len(self.object_ids) and self.object_ids[index] == object_id:
            return _value_at(reducer_type, self.values[index], self.timestamps[index], timestamp)
        return default


class Counters:
    def __init__(self):
        self.data = defaultdict(CounterValues)

    def __repr__(self):
        return str(dict(self.data))

    def slice(self, object_type, counter_type, reducer_type):
        return self.data.get(CounterKey(object_type, counter_type, reducer_type), CounterValues())

    def freeze(self):
        for values in self.data.values():
            values.freeze()

    def reduce(self, timestamp):
        for key, values in self.data.items():
            values.reduce(key.reducer_type, timestamp)

    def value(self, object_type, counter_type, reducer_type, object_id, default=None):
        counter_values = self.data.get(CounterKey(object_type, counter_type, reducer_type))
        return counter_values.value(object_id, default) if counter_values else default

    def value_at(self, object_type, counter_type, reducer_type, object_id, timestamp, default=None):
        counter_values = self.data.get(CounterKey(object_type, counter_type, reducer_type))
        return counter_values.value_at(object_id, reducer_type, timestamp, default) if counter_values else default

    def update(self, object_type, counter_type, reducer_type, object_id, value, timestamp):
        counter_values = self.data[CounterKey(object_type, counter_type, reducer_type)]
        counter_values.update(object_id, reducer_type, value, timestamp)


# REQUIRES input counters to be reduced and frozen beforehand
def counter_cosine(
    counters_1, object_type_1, counter_type_1,
    counters_2, object_type_2, counter_type_2,
    reducer_type
):
    values_1 = counters_1.slice(object_type_1, counter_type_1, reducer_type)
    values_2 = counters_2.slice(object_type_2, counter_type_2, reducer_type)

    mod_1 = norm(values_1.values)
    if mod_1 == 0.0:
        return 0.0

    mod_2 = norm(values_2.values)
    if mod_2 == 0.0:
        return 0.0

    _, i_1, i_2 = np.intersect1d(values_1.object_ids, values_2.object_ids, assume_unique=True, return_indices=True)
    dot_prod = np.sum(values_1.values[i_1] * values_2.values[i_2])

    return dot_prod / (mod_1 * mod_2)
