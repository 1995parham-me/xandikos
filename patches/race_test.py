import os, sys, tempfile, threading
from dulwich.repo import Repo
from dulwich.index import locked_index
from dulwich.file import FileLocked
d = tempfile.mkdtemp(); r = Repo.init(d); path = r.index_path()
with locked_index(path): pass
errs = {"lost_lock": 0, "locked": 0, "ok": 0, "corrupt": 0}; lk = threading.Lock()
def worker():
    for _ in range(1500):
        try:
            with locked_index(path) as idx:
                pass
            k = "ok"
        except FileLocked: k = "locked"
        except FileNotFoundError: k = "lost_lock"
        except AssertionError: k = "corrupt"
        with lk: errs[k] += 1
ts = [threading.Thread(target=worker) for _ in range(16)]
[t.start() for t in ts]; [t.join() for t in ts]
print(errs)
