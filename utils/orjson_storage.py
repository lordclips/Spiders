import orjson
import os
import io

from tinydb.storages import Storage, touch
from typing import Optional, Dict, Any

"""
Fun little docstring

This is far from a perfect solution, however
it is good enough for now. Based on the default
JSONStorage storage available in the regular
TinyDB lib except using serialization using
orjson for extra speed.
"""


class orjsonStore(Storage):
    def __init__(self, path):
        self.path = path

        touch(path, False)

    def read(self) -> Optional[Dict[str, Dict[str, any]]]:
        with open(self.path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()

            if not size:
                return None

            handle.seek(0)

            return orjson.loads(handle.read(size))

    def write(self, data: Dict[str, Dict[str, Any]]):
        with open(self.path, "wb") as handle:
            handle.seek(0)

            serialized = orjson.dumps(data)

            handle.write(serialized)

            handle.flush()
            handle.truncate()


# Literally the single worst series
# of tests I've ever written.
# It works, at least.
if __name__ == "__main__":
    from tinydb import TinyDB

    db = TinyDB("db.json", storage=orjsonStore)

    db.insert({"1": "Test", "2": "Test"})

    db.close()

    db = TinyDB("db.json", storage=orjsonStore)

    print(db.all())
