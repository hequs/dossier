import unittest

from counters import BaseCT, BaseOT, Counters, counter_cosine, ONE_DAY_SECONDS, RT


class CT(BaseCT):
    TEST = 1


class OT(BaseOT):
    TEST = 1
    APPLE = 2
    ORANGE = 3
    CHERRY = 4


class TestCounters(unittest.TestCase):
    def test_single_update(self):
        counters = Counters()
        counters.update(OT.TEST, CT.TEST, RT.D30, '', 1000, 1)
        value = counters.get(OT.TEST, CT.TEST, RT.D30, '', 1+30*ONE_DAY_SECONDS)
        self.assertAlmostEqual(value, 500, places=5)

    def test_multiple_straight_update(self):
        counters = Counters()
        counters.update(OT.TEST, CT.TEST, RT.D30, '', 1000, 1)
        counters.update(OT.TEST, CT.TEST, RT.D30, '', 2000, 1)
        value = counters.get(OT.TEST, CT.TEST, RT.D30, '', 1+30*ONE_DAY_SECONDS)
        self.assertAlmostEqual(value, 1500, places=5)

    def test_multiple_reverse_update(self):
        counters = Counters()
        counters.update(OT.TEST, CT.TEST, RT.D30, '', 1000, 1+30*ONE_DAY_SECONDS)
        counters.update(OT.TEST, CT.TEST, RT.D30, '', 2000, 1)
        value = counters.get(OT.TEST, CT.TEST, RT.D30, '', 1+30*ONE_DAY_SECONDS)
        self.assertAlmostEqual(value, 2000, places=5)

    def test_reduce(self):
        counters = Counters()
        counters.update(OT.TEST, CT.TEST, RT.D30, '', 1000, 1)
        counters.reduce(1+30*ONE_DAY_SECONDS)
        counter_value = counters.slice(OT.TEST, CT.TEST, RT.D30).get('')
        self.assertAlmostEqual(counter_value.value, 500, places=5)
        self.assertEqual(counter_value.timestamp, 1+30*ONE_DAY_SECONDS)


class TestCountersOps(unittest.TestCase):
    def test_empty_cosine(self):
        counters_1 = Counters()
        counters_1.update(OT.TEST, CT.TEST, RT.D30, 'orange', 1, 1)
        counters_2 = Counters()
        counters_2.update(OT.TEST, CT.TEST, RT.D30, 'cherry', 1, 1)
        value = counter_cosine(counters_1, OT.ORANGE, CT.TEST, counters_2, OT.CHERRY, CT.TEST, RT.D30, 1)
        self.assertEqual(value, 0)

    def test_cosine(self):
        counters_1 = Counters()
        counters_1.update(OT.TEST, CT.TEST, RT.D30, 'apple', 1, 1)
        counters_1.update(OT.TEST, CT.TEST, RT.D30, 'orange', 1, 1)
        counters_2 = Counters()
        counters_2.update(OT.TEST, CT.TEST, RT.D30, 'apple', 1, 1)
        counters_2.update(OT.TEST, CT.TEST, RT.D30, 'cherry', 1, 1)
        value = counter_cosine(counters_1, OT.TEST, CT.TEST, counters_2, OT.TEST, CT.TEST, RT.D30, 1)
        self.assertAlmostEqual(value, 0.5)

    def test_cosine_fails(self):
        counters_1 = Counters()
        counters_1.update(OT.TEST, CT.TEST, RT.D30, 'apple', 1, 3)
        counters_1.update(OT.TEST, CT.TEST, RT.D30, 'orange', 1, 2)
        counters_2 = Counters()
        counters_2.update(OT.TEST, CT.TEST, RT.D30, 'apple', 1, 4)
        counters_2.update(OT.TEST, CT.TEST, RT.D30, 'cherry', 1, 5)
        def callable():
            counter_cosine(counters_1, OT.TEST, CT.TEST, counters_2, OT.TEST, CT.TEST, RT.D30, 1)
        self.assertRaises(AssertionError, callable)
