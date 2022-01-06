from collections import defaultdict
from enum import Enum


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


ONE_DAY_SECONDS = 86400.0


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
    return 2 ** (-timestamp_delta / halflife)  # exp(-0.693147180 * timestamp_delta / halflife)


def _value_at(reducer_type, x, x_timestamp, timestamp):
    assert timestamp >= x_timestamp, "timestamp < x_timestamp"
    return _reduce(reducer_type, x, x_timestamp, 0.0, timestamp)


def _reduce(reducer_type, x, x_timestamp, y, y_timestamp):
    if x_timestamp > y_timestamp:
        x, y, x_timestamp, y_timestamp = y, x, y_timestamp, x_timestamp
    return x * _calc_decay(reducer_type, float(y_timestamp - x_timestamp)) + y


class CounterKey:
    __slots__ = ("object_type", "counter_type", "reducer_type")

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


class CounterValue:
    __slots__ = ("value", "timestamp")

    def __init__(self, value=0.0, timestamp=0):
        self.value = value
        self.timestamp = timestamp

    def __repr__(self):
        return str((self.value, self.timestamp))

    def reduce(self, reducer_type, timestamp):
        self.value = self.value_at(reducer_type, timestamp)
        self.timestamp = timestamp

    def value_at(self, reducer_type, timestamp):
        if self.timestamp == timestamp:
            return self.value
        return _value_at(reducer_type, self.value, self.timestamp, timestamp)

    def update(self, reducer_type, value, timestamp):
        self.value = _reduce(reducer_type, self.value, self.timestamp, value, timestamp)
        self.timestamp = max(self.timestamp, timestamp)


class CounterValues(defaultdict):
    def __init__(self, *args):
        super(CounterValues, self).__init__(CounterValue)

    def __repr__(self):
        return str(dict(self))

    def reduce(self, reducer_type, timestamp):
        for value in self.values():
            value.reduce(reducer_type, timestamp)

    def value(self, object_id, default=None):
        counter_value = self.get(object_id)
        return counter_value.value if counter_value else default

    def value_at(self, object_id, reducer_type, timestamp, default=None):
        counter_value = self.get(object_id)
        return counter_value.value_at(reducer_type, timestamp) if counter_value else default

    def update(self, object_id, reducer_type, value, timestamp):
        counter_value = self[object_id].update(reducer_type, value, timestamp)


class Counters(defaultdict):
    def __init__(self, *args):
        super(Counters, self).__init__(CounterValues)

    def __repr__(self):
        return str(dict(self))

    def slice(self, object_type, counter_type, reducer_type):
        return self.get(CounterKey(object_type, counter_type, reducer_type), CounterValues())

    def reduce(self, timestamp):
        for key, values in self.items():
            values.reduce(key.reducer_type, timestamp)

    def value(self, object_type, counter_type, reducer_type, object_id, default=None):
        counter_values = self.get(CounterKey(object_type, counter_type, reducer_type))
        return counter_values.value(object_id, default) if counter_values else default

    def value_at(self, object_type, counter_type, reducer_type, object_id, timestamp, default=None):
        counter_values = self.get(CounterKey(object_type, counter_type, reducer_type))
        return counter_values.value_at(object_id, reducer_type, timestamp, default) if counter_values else default

    def update(self, object_type, counter_type, reducer_type, object_id, value, timestamp):
        counter_values = self[CounterKey(object_type, counter_type, reducer_type)]
        counter_values.update(object_id, reducer_type, value, timestamp)


# see https://stackoverflow.com/questions/22381939/python-calculate-cosine-similarity-of-two-dicts-faster
def counter_cosine(
    counters_1, object_type_1, counter_type_1,
    counters_2, object_type_2, counter_type_2,
    reducer_type,
    timestamp
):
    slice_1 = counters_1.slice(object_type_1, counter_type_1, reducer_type)
    slice_2 = counters_2.slice(object_type_2, counter_type_2, reducer_type)

    def calc_mod(slice, reducer_type, timestamp):
        return sum(map(lambda x: x.value_at(reducer_type, timestamp) ** 2, slice.values()))

    mod_1 = calc_mod(slice_1, reducer_type, timestamp)
    if mod_1 == 0.0:
        return 0.0

    mod_2 = calc_mod(slice_2, reducer_type, timestamp)
    if mod_2 == 0.0:
        return 0.0

    dot_prod = 0.0
    for object_id, counter_value_1 in slice_1.items():
        if object_id in slice_2:
            dot_prod += counter_value_1.value_at(reducer_type, timestamp) * slice_2.get(object_id).value_at(reducer_type, timestamp)

    return dot_prod / (mod_1 * mod_2) ** 0.5
