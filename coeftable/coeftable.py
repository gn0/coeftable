import argh
import json
import sys


def traverse(obj):
    if type(obj) is dict:
        for key, obj2 in obj.iteritems():
            for subpath, value in traverse(obj2):
                if subpath is None:
                    yield "%s" % key, value
                else:
                    yield "%s::%s" % (key, subpath), value
    elif type(obj) is list:
        for i, obj2 in enumerate(obj, 1):
            for subpath, value in traverse(obj2):
                if subpath is None:
                    yield "%d" % i, value
                else:
                    yield "%d::%s" % (i, subpath), value
    else:
        yield None, obj


assert (dict(tuple(traverse([1, 2])))
        == {"1": 1, "2": 2})
assert (dict(tuple(traverse(
            {"asd": 1, "bsd": 2})))
        == {"asd": 1, "bsd": 2})
assert (dict(tuple(traverse(
            {"asd": [1, 2], "bsd": 2})))
        == {"asd::1": 1, "asd::2": 2, "bsd": 2})
assert (dict(tuple(traverse(
            {"asd": {"foo": 1, "bar": 2}, "bsd": 2})))
        == {"asd::foo": 1, "asd::bar": 2, "bsd": 2})


def load_models(filenames):
    data = dict()

    for i, filename in enumerate(filenames, 1):
        with open(filename, "r") as f:
            for path, value in traverse(json.load(f)):
                key = "%d::%s" % (i, path)

                data[key] = value

    return data


@argh.arg("--models", nargs="+", type=str, required=True)
def dispatcher(models=None):
    template = sys.stdin.read()
    data = load_models(models)

    print template % data


def main():
    argh.dispatch_command(dispatcher)


if __name__ == "__main__":
    main()
