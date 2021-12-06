from counters import Counters


class Dossier:
    def __init__(self, object_id, object_type):
        self.object_id = object_id
        self.object_type = object_type
        self.counters = Counters()

    @property
    def __dict__(self):
        return {
            "object_id": self.object_id,
            "object_type": self.object_type.value,
            "counters": vars(self.counters)
        }

    @classmethod
    def from_dict(cls, data):
        profile = cls(data["object_id"], OT(data["object_type"]))
        profile.counters = Counters.from_dict(data["counters"])
        return profile

    def dumps(self):
        return json.dumps(vars(self), ensure_ascii=False).strip()

    def dump(self, f):
        f.write(self.dumps() + "\n")

    @classmethod
    def loads(cls, st):
        return cls.from_dict(json.loads(st))

    def print_debug(self):
        print("===== {} {} =====".format(self.object_type.value, self.object_id))
        self.counters.print_debug()
