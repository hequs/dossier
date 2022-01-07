import unittest

from counters import *


class CT(BaseCT):
    TEST = 1


class OT(BaseOT):
    TEST = 1


def _days_to_seconds(d):
    ONE_DAY_SECONDS = 86400
    return 1 + d * ONE_DAY_SECONDS


class TestCounters(unittest.TestCase):
    def test_straight_update(self):
        counters = Counters()
        counters.update(OT.TEST, CT.TEST, RT.D30, '', 4000, _days_to_seconds(0))
        counters.update(OT.TEST, CT.TEST, RT.D30, '', 2000, _days_to_seconds(30))
        counters.update(OT.TEST, CT.TEST, RT.D30, '', 1000, _days_to_seconds(60))
        self.assertAlmostEqual(3000, counters.value(OT.TEST, CT.TEST, RT.D30, ''), places=5)
        self.assertAlmostEqual(1500, counters.value_at(OT.TEST, CT.TEST, RT.D30, '', _days_to_seconds(90)), places=5)

    def test_reverse_update(self):
        counters = Counters()
        counters.update(OT.TEST, CT.TEST, RT.D30, '', 1000, _days_to_seconds(60))
        counters.update(OT.TEST, CT.TEST, RT.D30, '', 2000, _days_to_seconds(30))
        counters.update(OT.TEST, CT.TEST, RT.D30, '', 4000, _days_to_seconds(0))
        self.assertAlmostEqual(3000, counters.value(OT.TEST, CT.TEST, RT.D30, ''), places=5)
        self.assertAlmostEqual(1500, counters.value_at(OT.TEST, CT.TEST, RT.D30, '', _days_to_seconds(90)), places=5)

    def test_merge(self):
        counters_1 = Counters()
        counters_1.update(OT.TEST, CT.TEST, RT.D30, 'apple', 2000, _days_to_seconds(0))
        counters_1.update(OT.TEST, CT.TEST, RT.D30, 'orange', 2000, _days_to_seconds(0))
        counters_2 = Counters()
        counters_1.update(OT.TEST, CT.TEST, RT.D30, 'apple', 1000, _days_to_seconds(30))
        counters_2.update(OT.TEST, CT.TEST, RT.D30, 'cherry', 1000, _days_to_seconds(30))
        counters_1.merge(counters_2)
        self.assertAlmostEqual(2000, counters_1.value(OT.TEST, CT.TEST, RT.D30, 'apple'), places=5)
        self.assertAlmostEqual(2000, counters_1.value(OT.TEST, CT.TEST, RT.D30, 'orange'), places=5)
        self.assertAlmostEqual(1000, counters_1.value(OT.TEST, CT.TEST, RT.D30, 'cherry'), places=5)

    def test_reduce(self):
        counters = Counters()
        counters.update(OT.TEST, CT.TEST, RT.D30, '', 1000, _days_to_seconds(0))
        counters.reduce(_days_to_seconds(30))
        self.assertAlmostEqual(500, counters.value(OT.TEST, CT.TEST, RT.D30, ''), places=5)


class TestCountersOps(unittest.TestCase):
    def test_empty_cosine(self):
        counters_1 = Counters()
        counters_1.update(OT.TEST, CT.TEST, RT.D30, 'orange', 1, 1)
        counters_2 = Counters()
        counters_2.update(OT.TEST, CT.TEST, RT.D30, 'cherry', 1, 1)
        value = counter_cosine(counters_1, OT.TEST, CT.TEST, counters_2, OT.TEST, CT.TEST, RT.D30)
        self.assertEqual(value, 0)

    def test_cosine(self):
        counters_1 = Counters()
        counters_1.update(OT.TEST, CT.TEST, RT.D30, 'apple', 1, 1)
        counters_1.update(OT.TEST, CT.TEST, RT.D30, 'orange', 1, 1)
        counters_2 = Counters()
        counters_2.update(OT.TEST, CT.TEST, RT.D30, 'apple', 1, 1)
        counters_2.update(OT.TEST, CT.TEST, RT.D30, 'cherry', 1, 1)
        value = counter_cosine(counters_1, OT.TEST, CT.TEST, counters_2, OT.TEST, CT.TEST, RT.D30)
        self.assertAlmostEqual(value, 0.5)

    def test_cosine_fails(self):
        counters_1 = Counters()
        counters_1.update(OT.TEST, CT.TEST, RT.D30, 'apple', 1, 3)
        counters_1.update(OT.TEST, CT.TEST, RT.D30, 'orange', 1, 2)
        counters_2 = Counters()
        counters_2.update(OT.TEST, CT.TEST, RT.D30, 'apple', 1, 4)
        counters_2.update(OT.TEST, CT.TEST, RT.D30, 'cherry', 1, 5)

        def callable():
            counter_cosine_at(counters_1, OT.TEST, CT.TEST, counters_2, OT.TEST, CT.TEST, RT.D30, 1)
        self.assertRaises(AssertionError, callable)
