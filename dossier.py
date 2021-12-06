from counters import Counters, BaseCT, BaseOT, RT, counter_cosine


class Dossier:
    def __init__(self, object_type, object_id):
        self.object_type = object_type
        self.object_id = object_id
        self.counters = Counters()

    def __repr__(self):
        return str(vars(self))

    def reduce(self, timestamp):
        self.counters.reduce(timestamp)
