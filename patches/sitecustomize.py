"""Local hotfix for a dulwich lock-file race (loaded via PYTHONPATH at startup).

dulwich's _GitFile.close() renames foo.lock -> foo and then, in `finally`,
calls abort(), which does os.remove("foo.lock"). Once the rename is done the
lock is released, so another xandikos request thread may already have created
a *new* foo.lock -- and we delete it. That thread's os.replace() then fails with
FileNotFoundError after its commit has landed in HEAD, leaving .git/index stale.
xandikos builds every commit from the index, so the next PUT silently reverts
the earlier change. Seen 2026-06..10 (9 reverted contacts).

Still present in dulwich 1.2.17 / main as of 2026-10-08. Drop this file once
upstream only calls abort() on failure.
"""

import os
import sys

try:
    from dulwich import file as _dfile

    def _close(self):
        if self._closed:
            return
        self._file.flush()
        if self._fsync:
            os.fsync(self._file.fileno())
        self._file.close()
        adjust = getattr(_dfile, "adjust_shared_perm", None)
        if adjust is not None and hasattr(self, "_shared_perm"):
            adjust(self._lockfilename, self._shared_perm)
        try:
            os.replace(self._lockfilename, self._filename)
        except BaseException:
            self.abort()
            raise
        # Rename succeeded: the lock path no longer belongs to us, never remove it.
        self._closed = True

    _dfile._GitFile.close = _close
    print("sitecustomize: patched dulwich _GitFile.close lock race", file=sys.stderr)
except Exception as exc:  # never block startup
    print(f"sitecustomize: dulwich patch NOT applied: {exc!r}", file=sys.stderr)
