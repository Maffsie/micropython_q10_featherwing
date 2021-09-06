class Objdict(dict):
    def __getattr__(self, item):
        if item in self:
            return self[item]
        raise AttributeError(f"No such attribute '{item}'")

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, item):
        if item in self:
            del self[item]
        raise AttributeError(f"No such attribute '{item}'")
