<h1 align="center"> Xandikos Troubleshooting </h1>
<h6 align="center"> Fixes for problems seen in production </h6>

## `500` on `REPORT` / DAVx5 sync stuck (zlib errors)

### Symptom

- Clients (DAVx5, macOS Contacts, `khard`) fail to sync; DAVx5 sync gets **stuck** and retries forever.
- `nginx` logs show `500` on `REPORT /user/contacts/addressbook/` (or the calendar equivalent):

  ```bash
  docker logs --since 30m xandikos-nginx-1 | grep '" 500 '
  ```

- The `xandikos` container logs show **varying** `zlib` errors while reading git objects:

  ```
  zlib.error: Error -3 while decompressing data: invalid stored block lengths
  zlib.error: Error -3 while decompressing data: invalid code lengths set
  zlib.error: ... incorrect header check / decompressed data does not match expected size
  ```

  The traceback ends in `dulwich/pack.py` (`resolve_object` → `get_object_at` → `read_zlib_chunks`).

### Root cause

A **dulwich concurrency bug reading from the git packfile**. Under a client's parallel/streaming
reads, dulwich's single shared pack file handle (`PackData._file` seek position) gets raced between
overlapping requests, so it decompresses bytes at the wrong offset → the (varying) `zlib` errors.

Key facts to avoid chasing the wrong thing:

- **The data on disk is NOT corrupt.** Verify: `git fsck --full` is clean and
  `git cat-file --batch-all-objects --batch --unordered 2>err >/dev/null; wc -l err` reports 0 errors.
- It is a **transient concurrency** fault, so it is essentially **not reproducible** with local
  `curl` (even 150-way parallel) — it needs the real client's streaming pattern.

### What does NOT fix it (don't waste time)

- `docker restart` — helps briefly, recurs.
- Upgrading the xandikos image / dulwich — reduces but does not eliminate.
- **`git gc` — makes it WORSE.** Packing + deltifying the objects adds *more* shared-handle
  seeking (delta-base resolution). Do not run it. See "Durability" below.
- `git repack --depth=0 --window=0` (no-delta pack) — still races on the shared pack handle.

### The fix: convert the store to all-loose objects

With every object stored **loose** (one file per object), dulwich opens each object independently —
there is no shared file handle to race, so the bug cannot trigger.

Set `STORE` to the affected store and run:

```bash
STORE=/home/parham/Downloads/xandikos/user/contacts/addressbook   # or .../user/calendars/calendar

# 1. Stop xandikos so nothing reads the store mid-swap (brief downtime, data is safe)
docker stop xandikos-xandikos-1

# 2. Explode every pack into loose objects
cd "$STORE"
mkdir -p /tmp/packbak
mv .git/objects/pack/pack-*.pack .git/objects/pack/pack-*.idx .git/objects/pack/pack-*.rev /tmp/packbak/ 2>/dev/null
git unpack-objects -r < /tmp/packbak/pack-*.pack

# 3. Sanity check: clean, and no packs remain
git fsck --full | grep -v dangling        # expect no output
ls .git/objects/pack/                      # expect empty

# 4. Start xandikos again
docker start xandikos-xandikos-1
```

Then on the client, let it re-sync (or in DAVx5 pull-to-refresh). It should complete with no 500s.

### Durability — keep it fixed

Loose objects only stay loose if **nothing ever repacks the store**. Harden it once:

```bash
cd "$STORE"
git config gc.auto 0
git config gc.autoPackLimit 0
git config gc.autoDetach false
```

Rules going forward:

- **Never run `git gc` or `git repack`** on a xandikos store. This is the #1 way to reintroduce the bug.
- Loose objects accumulate slowly over time. **That is fine — do not "clean it up".**
- Optional belt-and-suspenders: lower the client's sync frequency / parallelism.
- The permanent fix is upstream in dulwich; this is a workaround.

### Verify health (anytime)

```bash
docker logs --since 10m xandikos-xandikos-1 | grep -c zlib.error   # want: 0
docker logs --since 10m xandikos-nginx-1    | grep -c '" 500 '     # want: 0
```

### Note on the pinned image

`docker-compose.yml` pins the `xandikos` image by digest (not `:latest`) for reproducibility.
Heads-up: the `ghcr.io/jelmer/xandikos` **`vX.Y.Z` release tags are stale** (e.g. `v0.3.0` is a
downgrade). The newest code lives on the moving `:latest` tag, so to upgrade, pull `:latest`, read
its new digest, and pin that digest.

## DAVx5: "HTTP server error – Received multi-get response without data"

### Symptom

DAVx5 shows a sync-problem notification for the `main` address book (or the calendar) with that text. The debug page names the remote resource: `.../user/contacts/addressbook/push-subscriptions.json` (or any other non-`.vcf` / non-`.ics` file). Every sync fails the same way; the server log shows a `REPORT` answered with `207` and only a few hundred bytes right after the `sync-collection` report.

### Root cause

Xandikos lists a collection straight from the **git tree**: every committed blob is a member, whatever its name. Its WebDAV-Push store writes `push-subscriptions.json` into the collection directory on the filesystem only, which is harmless, but a `git add -A` or `git add .` in `user/contacts/addressbook` or `user/calendars/calendar` commits it, and from then on `sync-collection` reports it as a changed member, DAVx5 multigets it, gets an etag with no `address-data`, and aborts the whole sync. Seen 2026-10-02 after a "chore: update push configuration" commit; the same happens with any helper script left in the collection (`rename_vcf_by_uid.py` sat there for a year and only stayed quiet because it never changed).

### The fix

```sh
cd ~/Downloads/xandikos/user/contacts/addressbook   # and user/calendars/calendar
git rm --cached push-subscriptions.json              # keep the file on disk, xandikos reads it from there
git commit -m "drop push-subscriptions.json from the tree"
```

`.git/info/exclude` in both collection repos now lists `push-subscriptions.json`, `.push-subscriptions.*.tmp` and `push-subscription-index.json`, so a stray `git add -A` no longer picks them up (a `.gitignore` would itself become a member, which is why it is `info/exclude`). Keep helper scripts outside the collections; `rename_vcf_by_uid.py` now lives in the repo root.

Verify from anywhere: a `PROPFIND` with `Depth: 1` on the collection must list only `.vcf` / `.ics` hrefs, and the next `sync-collection` reports the removed names as `404`, which DAVx5 handles as deletions. No restart needed.

## Phantom `MM` diff in `git status` / a contact edit silently reverted

### Symptom

`git status` in the addressbook shows a `.vcf` as both staged and unstaged (`MM`), with each diff the mirror image of the other, while `git diff HEAD` is empty. In `docker logs` a `PUT` returned `500` with `FileNotFoundError: ... '.git/index.lock' -> '.git/index'`. Worse case: a later xandikos commit "Modified A.vcf" also changes B.vcf back to an older version.

### Root cause

dulwich's `_GitFile.close()` renames `index.lock` → `index` and then, in `finally`, calls `abort()`, which `os.remove`s `index.lock`. After the rename another request thread may already hold a *new* `index.lock`, and it gets deleted. That thread's commit lands in HEAD but its index write fails, so `.git/index` stays stale. xandikos builds every commit from the index, so the **next PUT reverts the earlier change**. Concurrent DAVx5 PUT bursts trigger it. It happened 9 times from June to October 2026, and all were recovered. Still unfixed upstream as of dulwich 1.2.17.

### The fix

`patches/sitecustomize.py` (mounted read-only and put first on `PYTHONPATH` in `docker-compose.yml`) monkeypatches `close()` so it only calls `abort()` when the rename fails. Check that it's active: `docker logs xandikos-xandikos-1 2>&1 | grep sitecustomize` should print `patched dulwich _GitFile.close lock race`. `patches/race_test.py` reproduces the race (`docker exec -e PYTHONPATH=/code xandikos-xandikos-1 python3 /data/patches/race_test.py` vs `-e PYTHONPATH=/data/patches:/code`). Upstream fix: https://github.com/jelmer/dulwich/pull/2490. Remove the patch once a dulwich release containing it is in the pinned image.

### If it happens anyway

Confirm `git diff HEAD` is empty for the file, then `git restore --staged <file>`. To find collateral reverts, look for xandikos `Modified X.vcf` commits that touch any file other than X.
