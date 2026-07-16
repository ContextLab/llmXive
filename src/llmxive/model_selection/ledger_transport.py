"""Strict per-record CAS transport for the credit-reservation ledger (spec 026,
slice 1B / FR-016).

The reservation ledger is ONE authoritative append-only log on a dedicated
protected ref — ``refs/llmxive/credit-ledger`` — that EVERY branch and runner
reserves against (never a branch-local copy). Events live at
``reservations/<schema_revision>/<event-id>.json`` and are projected into the
reservation state by :mod:`llmxive.model_selection.reservations`.

Why not ``scripts/ci/commit-and-push.sh``: its ``-X theirs`` whole-tree rebase
lets a LOSING reservation replay stale admitted state over a winner — that is a
merge, not a compare-and-swap. This module instead uses git's NATIVE CAS:

- the ref is **never checked out**; each event is appended with pure plumbing
  (``hash-object`` → a throwaway ``GIT_INDEX_FILE`` + ``read-tree`` /
  ``update-index`` / ``write-tree`` → ``commit-tree`` parented on the current tip);
- locally, ``git update-ref <ref> <new> <expected-old>`` fails if the ref moved;
- against a shared remote, a **fast-forward-only** push is rejected server-side
  when a concurrent event landed first — and that rejection IS the compare.

On rejection the caller re-fetches, re-projects, re-verifies the predicate, and
re-appends onto the new tip (bounded retries). A genuine AUTH / permission
failure is distinct from a non-fast-forward rejection: it raises
:class:`LedgerAuthError` so the caller FAILS CLOSED (no paid call when the ledger
is unreachable) rather than silently proceeding unguarded.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

#: The single authoritative ledger ref (a standalone ref, NOT a working branch).
LEDGER_REF = "refs/llmxive/credit-ledger"
#: Bump when the on-disk event schema changes; events are namespaced by it so an
#: old runner's projection never mixes schema revisions.
SCHEMA_REVISION = "v1"
_EVENT_DIR = f"reservations/{SCHEMA_REVISION}"

_ZERO_OID = "0" * 40  # git's "ref must not currently exist" sentinel for update-ref
#: Fixed identity for ledger commits — never depends on the runner's git config.
_GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "llmxive-credit-ledger",
    "GIT_AUTHOR_EMAIL": "ledger@llmxive.local",
    "GIT_COMMITTER_NAME": "llmxive-credit-ledger",
    "GIT_COMMITTER_EMAIL": "ledger@llmxive.local",
}
# stderr fragments that mean "authenticated/authorized transport FAILED" (fail
# closed) as opposed to a benign non-fast-forward rejection (retry).
_AUTH_FAIL_MARKERS = (
    "authentication failed",
    "could not read username",
    "permission denied",
    "access denied",
    "403",
    "401",
    "fatal: could not read",
    "remote: permission to",
    "terminal prompts disabled",
)
# Benign rejections a concurrent reserver caused — REFETCH + recompute (retry).
# A concurrent CREATE of the same new ref reports "cannot lock ref ... reference
# already exists" / "failed to update ref"; a concurrent UPDATE reports
# non-fast-forward. Both are the CAS working, not an error.
_NON_FF_MARKERS = (
    "non-fast-forward", "fetch first", "failed to push some refs", "! [rejected]",
    "reference already exists", "cannot lock ref", "failed to update ref",
)
# A push rejected by a branch/ref PROTECTION or PERMISSION rule is an AUTH failure
# (fail closed), checked first so it is never masked. Kept SPECIFIC — a bare "remote
# rejected" also appears in the benign concurrent-create case above, so it is NOT here.
_PUSH_DENY_MARKERS = ("pre-receive hook declined", "protected branch", "protected ref", "gh006")
#: Event/reservation ids become git path segments (reservations/<rev>/<id>.json), so
#: they must be a single safe path component — no "/" (nesting/collision) or "..".
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")


class LedgerError(RuntimeError):
    """A ledger transport failure."""


class LedgerAuthError(LedgerError):
    """The authoritative ref is UNREACHABLE (auth/permission/network) — the caller
    MUST fail closed: no paid call may proceed without a working ledger."""


class LedgerContention(LedgerError):
    """The strict CAS could not fast-forward within the retry budget (sustained
    contention). The caller fails closed rather than force the write."""


class LedgerDenied(LedgerError):
    """The credit predicate rejected the reservation against fresh state (e.g. no
    headroom once counting reservations + fresh spend are considered). Distinct
    from contention: the event was NEVER appended by design."""


def _git(
    args: list[str], *, cwd: Path, extra_env: dict[str, str] | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **_GIT_IDENTITY, "GIT_TERMINAL_PROMPT": "0"}
    if extra_env:
        env.update(extra_env)
    proc = subprocess.run(
        ["git", *args], cwd=str(cwd), env=env, capture_output=True, text=True, check=False
    )
    if check and proc.returncode != 0:
        raise LedgerError(f"git {' '.join(args)} failed ({proc.returncode}): {proc.stderr.strip()}")
    return proc


def _rev(repo: Path, ref: str) -> str | None:
    """The commit OID the ref points at, or ``None`` if the ref does not exist."""
    proc = _git(["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], cwd=repo, check=False)
    oid = proc.stdout.strip()
    return oid or None


def read_events(repo: Path, *, ref: str = LEDGER_REF) -> list[dict]:
    """Every event currently recorded on ``ref`` (empty if the ref is absent).
    Reads straight from the object store — the ledger ref is never checked out."""
    tip = _rev(repo, ref)
    if tip is None:
        return []
    listing = _git(
        ["ls-tree", "-r", "--name-only", tip, "--", f"{_EVENT_DIR}/"], cwd=repo, check=False
    ).stdout
    events: list[dict] = []
    for path in filter(None, (line.strip() for line in listing.splitlines())):
        blob = _git(["cat-file", "blob", f"{tip}:{path}"], cwd=repo).stdout
        try:
            events.append(json.loads(blob))
        except json.JSONDecodeError as exc:
            # FAIL CLOSED (C4): this is the AUTHORITATIVE financial ledger, not a
            # cache. Skipping a corrupt event could drop a COUNTING (open/settling)
            # reservation from the projection → counting_total under-counts →
            # phantom headroom → overspend. Refuse to read rather than under-count.
            raise LedgerError(f"corrupt ledger event {path!r}: {exc}") from exc
    return events


def _append_commit(repo: Path, parent: str | None, event: dict) -> str:
    """Build (WITHOUT touching the working tree) a new commit that adds exactly
    one event file onto ``parent``'s tree. Returns the new commit OID."""
    event_id = str(event["event_id"])
    # hash-object needs the content on stdin, so run it directly for the pipe
    # (the fixed ledger identity env is irrelevant to a pure blob write).
    proc = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"],
        cwd=str(repo),
        input=json.dumps(event, indent=2, sort_keys=True),
        capture_output=True,
        text=True,
        check=True,
    )
    blob_oid = proc.stdout.strip()

    with tempfile.TemporaryDirectory() as td:
        index = str(Path(td) / "index")
        env = {"GIT_INDEX_FILE": index}
        if parent is not None:
            _git(["read-tree", parent], cwd=repo, extra_env=env)
        _git(
            ["update-index", "--add", "--cacheinfo", f"100644,{blob_oid},{_EVENT_DIR}/{event_id}.json"],
            cwd=repo,
            extra_env=env,
        )
        tree = _git(["write-tree"], cwd=repo, extra_env=env).stdout.strip()

    msg = f"ledger: {event.get('type', '?')} {event.get('reservation_id', '?')} {event_id}"
    commit_args = ["commit-tree", tree, "-m", msg]
    if parent is not None:
        commit_args += ["-p", parent]
    return _git(commit_args, cwd=repo).stdout.strip()


def _fetch_authoritative(repo: Path, remote: str) -> None:
    """Sync the LOCAL ledger ref to the authoritative remote copy. Fail CLOSED on
    an auth/permission/network error (the remote's ref is authoritative — if we
    can't read it we must not proceed with a paid call)."""
    proc = _git(
        ["fetch", "--quiet", remote, f"+{LEDGER_REF}:{LEDGER_REF}"], cwd=repo, check=False
    )
    if proc.returncode != 0:
        stderr = proc.stderr.strip().lower()
        # Check auth/permission markers FIRST (C5): a real auth failure whose stderr
        # ALSO mentions a missing ref must NOT be misread as a benign cold start
        # (that would proceed against an empty ledger unguarded = fail OPEN).
        if any(m in stderr for m in _AUTH_FAIL_MARKERS):
            raise LedgerAuthError(f"ledger ref unreachable on {remote!r}: {proc.stderr.strip()}")
        # A genuinely-absent ref on a REACHABLE remote is a cold start (first run).
        # NOTE: a reachable-but-WRONG remote (fork / renamed origin) is
        # indistinguishable from first-run here; slice-3 wiring MUST bootstrap the
        # ref + pin the correct remote so a missing ref thereafter is an error.
        if "couldn't find remote ref" in stderr or "no such ref" in stderr:
            return
        raise LedgerAuthError(f"ledger fetch from {remote!r} failed: {proc.stderr.strip()}")


def _push_fast_forward(repo: Path, remote: str, commit: str) -> bool:
    """Fast-forward-only push of ``commit`` to the authoritative ref. Returns
    True on success, False on a benign non-fast-forward rejection (a concurrent
    event won — retry). Raises :class:`LedgerAuthError` on auth/permission."""
    proc = _git(
        ["push", "--quiet", remote, f"{commit}:{LEDGER_REF}"], cwd=repo, check=False
    )
    if proc.returncode == 0:
        return True
    stderr = proc.stderr.strip().lower()
    # Auth / permission / ref-protection denial FIRST (C10): a protected-ref rejection
    # emits "failed to push some refs" too, so classifying it as a benign non-FF would
    # waste the whole retry budget and then raise the WRONG (contention) error.
    if any(m in stderr for m in _AUTH_FAIL_MARKERS) or any(m in stderr for m in _PUSH_DENY_MARKERS):
        raise LedgerAuthError(f"ledger push to {remote!r} denied: {proc.stderr.strip()}")
    if any(m in stderr for m in _NON_FF_MARKERS):
        return False  # a concurrent event won — refetch + recompute
    raise LedgerError(f"ledger push to {remote!r} failed: {proc.stderr.strip()}")


def append_event(
    repo: Path,
    event: dict,
    *,
    remote: str | None = None,
    predicate: Callable[[list[dict]], tuple[bool, str]] | None = None,
    max_retries: int = 8,
) -> str:
    """Append ONE ``event`` to the authoritative ledger under strict CAS.

    Each attempt: (1) fetch the authoritative ref (if ``remote``); (2) re-read the
    events (the projection input); (3) re-evaluate ``predicate`` against that fresh
    state — a False result raises :class:`LedgerDenied` and NOTHING is appended;
    (4) build the append-only commit onto the current tip; (5) fast-forward the ref
    (``update-ref`` CAS locally, FF push remotely); (6) on a non-fast-forward
    rejection, discard and recompute from the NEW tip. Every ledger mutation
    (open / heartbeat / settling / reconciled) flows through here.

    ``event`` MUST carry a unique ``event_id`` (append-only filename) and a
    ``reservation_id`` (idempotency key). Returns the new tip commit OID.
    """
    if "event_id" not in event or "reservation_id" not in event:
        raise ValueError("ledger event requires 'event_id' and 'reservation_id'")
    # C9: ids become a git path segment reservations/<rev>/<id>.json — reject any
    # that are not a single safe component (e.g. slice-3 model-derived ids contain
    # "/"/":" and MUST be sanitized before reaching the ledger, else nesting/collision).
    for key in ("event_id", "reservation_id"):
        if not _SAFE_ID.match(str(event[key])):
            raise ValueError(f"ledger {key}={event[key]!r} must match {_SAFE_ID.pattern}")
    event.setdefault("ts", datetime.now(UTC).isoformat())

    for _attempt in range(max_retries):
        if remote is not None:
            _fetch_authoritative(repo, remote)
        events = read_events(repo)
        if predicate is not None:
            ok, reason = predicate(events)
            if not ok:
                raise LedgerDenied(reason)
        parent = _rev(repo, LEDGER_REF)
        new_commit = _append_commit(repo, parent, event)
        if remote is not None:
            if _push_fast_forward(repo, remote, new_commit):
                # Sync the local ref to what we successfully pushed.
                _git(["update-ref", LEDGER_REF, new_commit], cwd=repo)
                return new_commit
            continue  # concurrent event won — refetch + recompute
        # Local-only CAS: set the ref iff it still equals the observed parent.
        proc = _git(
            ["update-ref", LEDGER_REF, new_commit, parent or _ZERO_OID], cwd=repo, check=False
        )
        if proc.returncode == 0:
            return new_commit
        # ref moved under us (same-clone concurrency) — recompute from the new tip.
    raise LedgerContention(
        f"could not fast-forward {LEDGER_REF} after {max_retries} attempts (sustained contention)"
    )


__all__ = [
    "LEDGER_REF",
    "SCHEMA_REVISION",
    "LedgerAuthError",
    "LedgerContention",
    "LedgerDenied",
    "LedgerError",
    "append_event",
    "read_events",
]
