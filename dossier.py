from copy import deepcopy
from counters import Counters, BaseCT, BaseOT, RT, counter_cosine


class Dossier:
    def __init__(self, object_type, object_id):
        self.object_type = object_type
        self.object_id = object_id
        self.counters = Counters()
        self.additional_data = dict()

    def __repr__(self):
        return str(vars(self))

    def merge(self, other):
        assert (self.object_type, self.object_id) == (other.object_type, other.object_id), 'unequal dossier ids'
        self.counters.merge(other.counters)

    @staticmethod
    def merge_all(dossiers):
        dossiers = iter(dossiers)
        dossier = deepcopy(next(dossiers))
        for next_dossier in dossiers:
            dossier.merge(next_dossier)
        return dossier

    def reduce(self, timestamp):
        self.counters.reduce(timestamp)
