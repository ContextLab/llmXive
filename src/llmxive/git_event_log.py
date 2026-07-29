"""Ref-agnostic append-only event log with strict per-record CAS on a git ref.

This is the transport the 026 credit ledger proved, extracted so more than one
domain can rest on it (spec 025 slice 1A, Task 1). Nothing here knows about
credits, reservations, or the self-improvement lane: a caller supplies a
:class:`LogRef` (which ref, which subtree, which remote, which pinned anchor),
its own ``validate``/``message_fn``, and gets git's NATIVE compare-and-swap.

Why git plumbing rather than a checkout + merge: a ``-X theirs`` whole-tree
rebase lets a LOSING writer replay stale state over a winner — that is a merge,
not a compare-and-swap. Instead:

- the ref is **never checked out**; each event is appended with pure plumbing
  (``hash-object`` → a throwaway ``GIT_INDEX_FILE`` + ``read-tree`` /
  ``update-index`` / ``write-tree`` → ``commit-tree`` parented on the current tip);
- locally, ``git update-ref <ref> <new> <expected-old>`` fails if the ref moved;
- against a shared remote, a **fast-forward-only** push is rejected server-side
  when a concurrent event landed first — and that rejection IS the compare.

On rejection the caller re-fetches, re-projects, re-verifies its predicate, and
re-appends onto the new tip (bounded retries). A genuine AUTH / permission
failure is distinct from a non-fast-forward rejection: it raises
:class:`GitLogAuthError` so the caller FAILS CLOSED rather than proceeding
against an unverified log.

Every event is a JSON object with a unique ``event_id``, stored at
``<event_dir>/<event_id>.json``. ``event_id`` is the ONE key the core requires;
everything else is the caller's schema.
"""

from __future__ import annotations

import json
import os
import random
import re
import subprocess
import tempfile
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

#: git's "ref must not currently exist" sentinel for ``update-ref``.
_ZERO_OID = "0" * 40

#: Event ids become git path segments (``<event_dir>/<id>.json``), so they must be a
#: single safe path component — no "/" (nesting/collision) or "..".
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")

#: Fallback commit identity. A caller that wants its log attributable to a specific
#: actor passes its own via ``LogRef.git_identity`` — never depend on the runner's
#: git config, which varies per environment.
_DEFAULT_GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "llmxive-event-log",
    "GIT_AUTHOR_EMAIL": "event-log@llmxive.local",
    "GIT_COMMITTER_NAME": "llmxive-event-log",
    "GIT_COMMITTER_EMAIL": "event-log@llmxive.local",
}

# stderr fragments that mean "authenticated/authorized transport FAILED" (fail
# closed) as opposed to a benign non-fast-forward rejection (retry). CONTEXTUAL only:
# a bare "401"/"403" matched random commit OIDs in a concurrent "cannot lock ref ...
# expected <OID>" rejection and misclassified it as an auth failure — every marker
# here must be a phrase that cannot appear inside a hex OID.
_AUTH_FAIL_MARKERS = (
    "authentication failed",
    "could not read username",
    "permission denied",
    "access denied",
    "returned error: 401",
    "returned error: 403",
    "error: 401 unauthorized",
    "error: 403 forbidden",
    "fatal: could not read",
    "remote: permission to",
    "terminal prompts disabled",
)
# Benign rejections a concurrent writer caused — REFETCH + recompute (retry).
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


class GitLogError(RuntimeError):
    """An event-log transport failure."""


class GitLogAuthError(GitLogError):
    """The authoritative ref is UNREACHABLE (auth/permission/network) — the caller
    MUST fail closed: no guarded operation may proceed without a working log."""


class GitLogContention(GitLogError):
    """The strict CAS could not fast-forward within the retry budget (sustained
    contention). The caller fails closed rather than force the write."""


class GitLogDenied(GitLogError):
    """The caller's ``predicate`` rejected the append against fresh state (e.g. no
    headroom once committed records are considered). Distinct from contention: the
    event was NEVER appended, by design."""


@dataclass(frozen=True)
class LogRef:
    """WHICH log, and how to trust it.

    ``ref``/``event_dir`` locate the records. ``remote`` (when set) names the
    authoritative copy: the ref must already exist there (bootstrap is the only
    creator), and ``expected_anchor`` pins the bootstrap commit so a wrong/divergent
    log is rejected. The default is local-only: tests, a single runner, or a
    degenerate mode.

    **Setting ``remote`` does NOT make every read authoritative.** Only
    :func:`sync_and_verify` and :func:`append_to_log` (which calls it) fetch the remote
    and check the anchor; :func:`read_log` is a pure local object-store read by design
    — see its docstring. A wrapper that exposes a public read MUST call
    :func:`sync_and_verify` first, or it will project a stale (possibly empty) local
    ref while appearing to be remote-backed.
    """

    ref: str
    event_dir: str
    remote: str | None = None
    expected_anchor: str | None = None
    git_identity: Mapping[str, str] = field(default_factory=lambda: dict(_DEFAULT_GIT_IDENTITY))


@dataclass(frozen=True)
class AppendResult:
    """``commit`` is the resulting tip. ``seq`` is the record's position in the log
    (0-based, assigned inside the successful CAS). ``created`` is True iff THIS call
    committed the event; False means an identical record was already present (an
    idempotent replay), so the caller must not treat it as new work."""

    commit: str
    seq: int
    created: bool


def _canonical(event: dict) -> str:
    """The single canonical on-disk serialization of an event (also the blob body).

    ``allow_nan=False``: Python's json emits bare ``NaN``/``Infinity``, which is not
    valid JSON — it round-trips only in Python and breaks every other reader of an
    append-only log. A non-finite number must never reach the ref.
    """
    return json.dumps(event, indent=2, sort_keys=True, allow_nan=False)


def _git(
    args: list[str],
    *,
    cwd: Path,
    identity: Mapping[str, str],
    extra_env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **identity, "GIT_TERMINAL_PROMPT": "0"}
    if extra_env:
        env.update(extra_env)
    proc = subprocess.run(
        ["git", *args], cwd=str(cwd), env=env, capture_output=True, text=True, check=False
    )
    if check and proc.returncode != 0:
        raise GitLogError(f"git {' '.join(args)} failed ({proc.returncode}): {proc.stderr.strip()}")
    return proc


def _rev(repo: Path, ref: str, *, identity: Mapping[str, str]) -> str | None:
    """The commit OID the ref points at, or ``None`` iff the ref GENUINELY does not
    exist.

    Absence and failure MUST NOT collapse into the same answer. ``None`` propagates as
    "empty log", and an empty log means "no claim / no reservation / no spend" to every
    projection built on this — so returning it for a wrong repository or a damaged
    object store would be fail-OPEN on an admission decision.

    ``rev-parse --verify --quiet`` exits 128 for an operational failure (e.g. not a git
    repository) and 1 for BOTH a missing ref and a ref whose object cannot be read. The
    second case is disambiguated with ``show-ref``, which reports on the REF itself
    independently of object readability: exit 1 there means the ref is truly absent;
    anything else means the ref exists but could not be resolved — corruption, which
    raises.
    """
    proc = _git(
        ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=repo, identity=identity, check=False,
    )
    if proc.returncode == 0:
        oid = proc.stdout.strip()
        if not oid:
            raise GitLogError(f"git rev-parse {ref!r} succeeded but returned no OID")
        return oid
    if proc.returncode != 1:
        raise GitLogError(
            f"cannot resolve {ref!r} ({proc.returncode}): {proc.stderr.strip()} — refusing "
            "to treat an unreadable ref as an empty log"
        )
    exists = _git(
        ["show-ref", "--verify", "--quiet", ref], cwd=repo, identity=identity, check=False
    )
    if exists.returncode == 1:
        return None  # the ref genuinely does not exist (cold start)
    raise GitLogError(
        f"ref {ref!r} exists but its object could not be resolved "
        f"({exists.returncode}): {exists.stderr.strip() or proc.stderr.strip()} — refusing "
        "to treat a damaged log as an empty one"
    )


def _read_event_blob(repo: Path, log: LogRef, event_id: str, tip: str) -> str | None:
    """The stored body of ``<event_id>.json`` at ``tip``, or ``None`` iff that path is
    GENUINELY absent from the tree.

    Same fail-closed reasoning as :func:`_rev`, and it matters more here: this is the
    append-only guard's read. A failure reported as "absent" would let a caller append
    over an event that is already committed.

    ``cat-file`` cannot distinguish the two cases — a missing path and a damaged object
    both exit 128 — so existence is tested with ``ls-tree``, which exits 0 with EMPTY
    output for an absent path and 128 for any operational failure.
    """
    listing = _git(
        ["ls-tree", tip, "--", f"{log.event_dir}/{event_id}.json"],
        cwd=repo, identity=log.git_identity,
    ).stdout.strip()
    if not listing:
        return None  # the path genuinely is not in this tree
    return _git(
        ["cat-file", "blob", f"{tip}:{log.event_dir}/{event_id}.json"],
        cwd=repo, identity=log.git_identity,
    ).stdout


def read_log(repo: Path, *, log: LogRef, validate: Callable[[dict], None]) -> list[dict]:
    """Every event recorded on the LOCAL ``log.ref`` (empty iff the ref is absent).
    Reads straight from the object store — the log ref is never checked out.

    **LOCAL by design — this does NOT fetch or verify the anchor**, even when
    ``log.remote`` is set. That mirrors the credit ledger's split, where syncing is the
    caller's explicit decision (``fetch_ledger``) because a projection may legitimately
    be taken repeatedly against one synced tip. The consequence is sharp: calling this
    on a fresh checkout with ``remote=`` set returns ``[]`` — an EMPTY log — because
    an ordinary clone does not fetch these refs. **Any public read a caller exposes
    MUST call :func:`sync_and_verify` first.**

    Fails CLOSED on everything else: this is an authoritative log, not a cache. A
    corrupt blob, an unreadable ref, a failed listing, or a payload the caller's
    ``validate`` rejects all RAISE rather than shrinking the projection — dropping a
    record would silently change an admission, ownership, or budget decision.
    ``validate`` runs on READ as well as write, so a manually corrupted or older
    malformed event cannot slip past write-time validation.
    """
    return _read_log_at(repo, log=log, tip=_rev(repo, log.ref, identity=log.git_identity),
                        validate=validate)


#: CAS attempts before an append gives up. It MUST exceed the number of writers that can
#: contend on one ref, because losing every race to every peer is a legal interleaving,
#: not an anomaly: the convergence panel dispatches its lenses through a ThreadPoolExecutor
#: (``engine._PANEL_MAX_CONCURRENCY``, 8), and each reviewer emits several audit events, so
#: a writer can genuinely lose 8 races in a row. The old bound of 8 EQUALLED the
#: concurrency cap with zero margin and blew up as `GitLogContention` on a healthy
#: 5-reviewer panel. Sized at 4x the cap.
_DEFAULT_MAX_RETRIES = 32
#: Upper bound of the randomized backoff between CAS attempts. Without jitter, the losers
#: of a race re-read and re-commit in lockstep and simply collide again; a few ms of
#: spread lets them serialize instead of livelocking.
_RETRY_BACKOFF_S = 0.02


def _cat_file_batch(
    repo: Path, *, log: LogRef, tip: str, paths: list[str]
) -> dict[str, str]:
    """Read every event blob in ONE ``git cat-file --batch`` instead of one process each.

    Reading is not a rare operation here: ``append_to_log`` does a FULL read on every
    attempt to derive the next ``seq``, so a per-blob subprocess makes an append cost
    O(n) processes and a whole Attempt O(n²). Measured on this substrate before the
    change: 245 ms/append at 30 events, 1206 ms at 120 — and a real Attempt's ~90 calls
    emit several hundred events, which is minutes of pure git overhead before a single
    model is called.

    Binary I/O throughout: ``--batch`` sizes are BYTE counts, so decoding before slicing
    would corrupt any non-ASCII payload.
    """
    if not paths:
        return {}
    env = {**os.environ, **log.git_identity, "GIT_TERMINAL_PROMPT": "0"}
    stdin = "".join(f"{tip}:{p}\n" for p in paths).encode()
    proc = subprocess.run(
        ["git", "cat-file", "--batch"], cwd=str(repo), env=env,
        input=stdin, capture_output=True, check=False,
    )
    if proc.returncode != 0:
        raise GitLogError(
            f"git cat-file --batch failed ({proc.returncode}): "
            f"{proc.stderr.decode(errors='replace').strip()}"
        )
    out, pos, blobs = proc.stdout, 0, {}
    for path in paths:
        nl = out.find(b"\n", pos)
        if nl < 0:
            raise GitLogError(f"cat-file --batch ended before {path!r}")
        header = out[pos:nl].decode()
        parts = header.split()
        # "<oid> missing" — a listed path whose object cannot be read is corruption, not
        # an empty event: the same fail-closed stance `_rev` takes on an unreadable ref.
        if len(parts) != 3:
            raise GitLogError(f"cat-file --batch could not read {path!r}: {header}")
        size = int(parts[2])
        start = nl + 1
        blobs[path] = out[start:start + size].decode()
        pos = start + size + 1          # skip the trailing newline --batch appends
    return blobs


def _read_log_at(
    repo: Path, *, log: LogRef, tip: str | None, validate: Callable[[dict], None]
) -> list[dict]:
    """:func:`read_log`'s body against an EXPLICIT tip.

    Split out because ``append_to_log`` must derive the next ``seq`` and the CAS parent
    from the SAME observation of the ref. Reading them independently is a live race: if
    another writer lands between the two reads, ``seq`` is stale while ``parent`` is
    fresh, so ``update-ref``'s compare-and-swap SUCCEEDS and two events share one ``seq``
    — which the reader then rejects as a corrupt sequence, after the damage is durable.
    Observed under the real convergence panel's ThreadPoolExecutor with five concurrent
    reviewers on one stream.
    """
    if tip is None:
        return []
    # CHECKED (not check=False): a failed listing has empty stdout, and projecting that
    # as "no events" would report a damaged or wrong repository as an empty log — the
    # same fail-open `_rev` guards against. An exit-0 empty listing genuinely means the
    # subtree holds no events.
    listing = _git(
        ["ls-tree", "-r", "--name-only", tip, "--", f"{log.event_dir}/"],
        cwd=repo, identity=log.git_identity,
    ).stdout
    paths = [p for p in (line.strip() for line in listing.splitlines()) if p]
    blobs = _cat_file_batch(repo, log=log, tip=tip, paths=paths)
    events: list[dict] = []
    for path in paths:
        blob = blobs[path]
        try:
            event = json.loads(blob)
        except json.JSONDecodeError as exc:
            raise GitLogError(f"corrupt log event {path!r}: {exc}") from exc
        if not isinstance(event, dict):
            raise GitLogError(f"log event {path!r} is not an object")
        try:
            validate(event)
        except ValueError as exc:
            raise GitLogError(f"invalid log event {path!r}: {exc}") from exc
        # The filename MUST match the payload id (a rename/mismatch is tampering).
        if Path(path).stem != str(event["event_id"]):
            raise GitLogError(
                f"log event path {path!r} does not match payload event_id "
                f"{event['event_id']!r}"
            )
        events.append(event)
    return events


def _append_commit(
    repo: Path, log: LogRef, parent: str | None, event: dict, message: str
) -> str:
    """Build (WITHOUT touching the working tree) a new commit that adds exactly
    one event file onto ``parent``'s tree. Returns the new commit OID."""
    event_id = str(event["event_id"])
    # hash-object needs the content on stdin, so run it directly for the pipe
    # (the fixed identity env is irrelevant to a pure blob write).
    proc = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"],
        cwd=str(repo),
        input=_canonical(event),
        capture_output=True,
        text=True,
        check=True,
    )
    blob_oid = proc.stdout.strip()

    with tempfile.TemporaryDirectory() as td:
        index = str(Path(td) / "index")
        env = {"GIT_INDEX_FILE": index}
        if parent is not None:
            _git(["read-tree", parent], cwd=repo, identity=log.git_identity, extra_env=env)
        _git(
            [
                "update-index", "--add", "--cacheinfo",
                f"100644,{blob_oid},{log.event_dir}/{event_id}.json",
            ],
            cwd=repo,
            identity=log.git_identity,
            extra_env=env,
        )
        tree = _git(["write-tree"], cwd=repo, identity=log.git_identity, extra_env=env).stdout.strip()

    commit_args = ["commit-tree", tree, "-m", message]
    if parent is not None:
        commit_args += ["-p", parent]
    return _git(commit_args, cwd=repo, identity=log.git_identity).stdout.strip()


def _fetch_authoritative(repo: Path, log: LogRef, remote: str) -> None:
    """Sync the LOCAL ref to the authoritative remote copy. Fail CLOSED on an
    auth/permission/network error (the remote's ref is authoritative — if we can't
    read it we must not proceed)."""
    proc = _git(
        ["fetch", "--quiet", remote, f"+{log.ref}:{log.ref}"],
        cwd=repo, identity=log.git_identity, check=False,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.strip().lower()
        # Check auth/permission markers FIRST: a real auth failure whose stderr ALSO
        # mentions a missing ref must NOT be misread as a benign cold start (that
        # would proceed against an empty log unguarded = fail OPEN).
        if any(m in stderr for m in _AUTH_FAIL_MARKERS):
            raise GitLogAuthError(f"log ref unreachable on {remote!r}: {proc.stderr.strip()}")
        # A genuinely-absent ref on a REACHABLE remote is a cold start (first run).
        if "couldn't find remote ref" in stderr or "no such ref" in stderr:
            return
        raise GitLogAuthError(f"log fetch from {remote!r} failed: {proc.stderr.strip()}")


def _remote_log_oid(repo: Path, log: LogRef, remote: str) -> str | None:
    """The OID the ref points at ON THE REMOTE (via ``ls-remote``), or ``None`` if the
    remote genuinely has no such ref. Fails closed if the remote cannot be queried — a
    missing ref must never be inferred from an auth/network failure. Checking the
    REMOTE (not the possibly-stale LOCAL ref) is what stops a pre-existing local log +
    empty/wrong remote from being treated as bootstrapped."""
    proc = _git(["ls-remote", remote, log.ref], cwd=repo, identity=log.git_identity, check=False)
    if proc.returncode != 0:
        raise GitLogAuthError(
            f"cannot query {remote!r} for {log.ref}: {proc.stderr.strip()} — failing closed"
        )
    line = proc.stdout.strip()
    return line.split()[0] if line else None


def _is_ancestor(repo: Path, log: LogRef, ancestor: str, descendant: str) -> bool:
    """True iff ``ancestor`` is reachable from ``descendant`` (shared log history)."""
    return (
        _git(
            ["merge-base", "--is-ancestor", ancestor, descendant],
            cwd=repo, identity=log.git_identity, check=False,
        ).returncode
        == 0
    )


def sync_and_verify(repo: Path, *, log: LogRef) -> None:
    """Bring the local ref into agreement with the AUTHORITATIVE remote and verify its
    identity before any read/mutation projects it. For a remote config: the ref MUST
    already EXIST on the remote — bootstrap is the only creator, so a missing ref fails
    closed (not treated as an empty local projection); the ref is then synced locally;
    and if an anchor is pinned, the remote tip MUST descend from it (else a
    wrong/unrelated log — fail closed). Local-only = no-op."""
    if log.remote is None:
        return
    remote_oid = _remote_log_oid(repo, log, log.remote)
    if remote_oid is None:
        raise GitLogAuthError(
            f"log ref {log.ref} absent on {log.remote!r} — not bootstrapped; failing closed"
        )
    _fetch_authoritative(repo, log, log.remote)
    # Verify the LOCAL tip AFTER the fetch — not the ls-remote OID captured before it
    # (TOCTOU hardening): a force-rewrite between ls-remote and fetch could otherwise
    # leave us operating on a tip we never verified. This checks the exact commit we
    # will project/append onto.
    local_tip = _rev(repo, log.ref, identity=log.git_identity)
    if local_tip is None:
        raise GitLogAuthError(
            f"log ref {log.ref} vanished from {log.remote!r} mid-operation; failing closed"
        )
    if log.expected_anchor is not None and not _is_ancestor(repo, log, log.expected_anchor, local_tip):
        raise GitLogAuthError(
            f"remote {log.ref} tip {local_tip} does not descend from the pinned anchor "
            f"{log.expected_anchor} — wrong/divergent log; failing closed"
        )


def _push_fast_forward(repo: Path, log: LogRef, remote: str, commit: str) -> bool:
    """Fast-forward-only push of ``commit`` to the authoritative ref. Returns True on
    success, False on a benign non-fast-forward rejection (a concurrent event won —
    retry). Raises :class:`GitLogAuthError` on auth/permission."""
    proc = _git(
        ["push", "--quiet", remote, f"{commit}:{log.ref}"],
        cwd=repo, identity=log.git_identity, check=False,
    )
    if proc.returncode == 0:
        return True
    stderr = proc.stderr.strip().lower()
    # Auth / permission / ref-protection denial FIRST: a protected-ref rejection emits
    # "failed to push some refs" too, so classifying it as a benign non-FF would waste
    # the whole retry budget and then raise the WRONG (contention) error.
    if any(m in stderr for m in _AUTH_FAIL_MARKERS) or any(m in stderr for m in _PUSH_DENY_MARKERS):
        raise GitLogAuthError(f"log push to {remote!r} denied: {proc.stderr.strip()}")
    if any(m in stderr for m in _NON_FF_MARKERS):
        return False  # a concurrent event won — refetch + recompute
    raise GitLogError(f"log push to {remote!r} failed: {proc.stderr.strip()}")


def bootstrap_log(
    repo: Path,
    *,
    log: LogRef,
    message: str,
    remote: str | None = None,
    _after_probe: Callable[[], None] | None = None,
) -> str:
    """Bring the authoritative log into existence with an empty anchor commit — the
    ONE-TIME, EXPLICIT administrative operation. NOT part of routine operation: every
    other write path fails closed when the remote ref is absent, so this is the only
    sanctioned creator. Returns the anchor commit OID.

    Divergence guard: when ``remote`` is given, the REMOTE (not the possibly stale
    LOCAL ref) is authoritative. If the remote already has the log it is adopted
    (no-op). If the remote is EMPTY but a LOCAL log already exists, that is a
    wrong/misconfigured remote — bootstrapping would push a divergent log — so it FAILS
    CLOSED rather than create one.

    ``_after_probe`` is a TEST-ONLY seam: it is called after the existence probe
    decides "not yet bootstrapped" and BEFORE the commit/update-ref/push, so two
    workers can block on a shared barrier there and genuinely race the push. It
    defaults to ``None`` (no-op) and is never used in production.
    """
    identity = log.git_identity
    if remote is not None:
        remote_oid = _remote_log_oid(repo, log, remote)
        if remote_oid is not None:
            _fetch_authoritative(repo, log, remote)  # already bootstrapped remotely — adopt it
            return _rev(repo, log.ref, identity=identity) or remote_oid
        if _rev(repo, log.ref, identity=identity) is not None:
            raise GitLogAuthError(
                f"refusing to bootstrap {remote!r}: a LOCAL log exists but the remote has "
                "none — a wrong/misconfigured remote would receive a DIVERGENT log. Verify "
                "the remote (or clear the local ref if this is a deliberate re-init)."
            )
    elif _rev(repo, log.ref, identity=identity) is not None:
        return _rev(repo, log.ref, identity=identity)

    if _after_probe is not None:
        _after_probe()  # TEST-ONLY barrier: both workers have probed an empty ref

    with tempfile.TemporaryDirectory() as td:
        env = {"GIT_INDEX_FILE": os.path.join(td, "index")}
        # empty index → empty tree
        empty_tree = _git(["write-tree"], cwd=repo, identity=identity, extra_env=env).stdout.strip()
    commit = _git(
        ["commit-tree", empty_tree, "-m", message], cwd=repo, identity=identity
    ).stdout.strip()
    proc = _git(
        ["update-ref", log.ref, commit, _ZERO_OID], cwd=repo, identity=identity, check=False
    )
    if proc.returncode != 0:  # a concurrent bootstrap won locally
        return _rev(repo, log.ref, identity=identity) or commit
    if remote is not None and not _push_fast_forward(repo, log, remote, commit):
        # a concurrent bootstrap won remotely — adopt it as authoritative
        _fetch_authoritative(repo, log, remote)
        return _rev(repo, log.ref, identity=identity) or commit
    return commit


def append_to_log(
    repo: Path,
    *,
    log: LogRef,
    validate: Callable[[dict], None],
    message_fn: Callable[[dict], str],
    event: dict | None = None,
    prepare: Callable[[list[dict]], dict | None] | None = None,
    predicate: Callable[[list[dict]], tuple[bool, str]] | None = None,
    now_field: str | None = None,
    finalize: Callable[[dict, int], dict] | None = None,
    identity_exclude: frozenset[str] = frozenset(),
    _after_parent: Callable[[], None] | None = None,
    max_retries: int = _DEFAULT_MAX_RETRIES,
) -> AppendResult:
    """Append ONE event to the authoritative log under strict CAS.

    Each attempt: (1) :func:`sync_and_verify` the ref per ``log`` (remote existence +
    pinned-anchor identity; fails closed if not bootstrapped); (2) re-read the events
    and fix ``parent``; (3) BUILD the event — either the fixed ``event`` (optionally
    gated by ``predicate``) or, for callers that must recompute against FRESH state
    each attempt, ``prepare(events)`` which returns the event to append, ``None`` for
    an idempotent no-op, or raises :class:`GitLogDenied`; (4) stamp ``now_field`` and
    apply ``finalize``; (5) ``validate``; (6) enforce append-only immutability; (7)
    append onto the current tip; (8) fast-forward the ref (``update-ref`` CAS locally,
    FF push remotely); (9) on non-fast-forward, refetch and recompute.

    ``prepare`` is re-invoked on EVERY attempt so a caller pricing against live state
    sees a fresh, internally-consistent observation.

    ``now_field`` (when set) receives an ISO-8601 UTC timestamp via ``setdefault``.
    ``finalize(built, seq)`` lets a caller stamp the authoritative ``seq`` and any
    derived anchors INSIDE the CAS, where ``seq`` is the record's position at the
    verified parent. ``identity_exclude`` names fields that are NOT part of an event's
    semantic identity (a store-assigned ``seq``, a timestamp, a revision anchor): the
    append-only guard compares canonical bodies with those fields removed from BOTH
    sides, so a semantic retry that differs only in them is an idempotent no-op rather
    than a spurious append-only violation.

    With ``now_field=None``, ``finalize=None`` and an empty ``identity_exclude``, steps
    (4) and the exclusion in (6) are no-ops and the guard compares the stored bytes
    exactly — byte-for-byte the behavior the credit ledger has always had.

    ``_after_parent`` is a TEST-ONLY seam called after ``parent``/``seq`` are fixed and
    before the commit + ref-CAS, so two workers can block on a shared barrier there
    (guaranteeing they built from the SAME parent) and then race the actual
    ``update-ref``/push — deterministically exercising the non-fast-forward retry path.
    """
    if (event is None) == (prepare is None):
        raise ValueError("append_to_log requires exactly one of 'event' or 'prepare'")

    def _identity_body(doc: dict) -> str:
        if not identity_exclude:
            return _canonical(doc)
        return _canonical({k: v for k, v in doc.items() if k not in identity_exclude})

    for _attempt in range(max_retries):
        if _attempt:
            # Jittered backoff. The losers of a race would otherwise re-read and re-commit
            # in lockstep and collide again on the very next attempt.
            time.sleep(random.uniform(0, _RETRY_BACKOFF_S))
        sync_and_verify(repo, log=log)  # remote existence + anchor identity; fails closed
        # ONE observation of the ref feeds BOTH the CAS parent and the next seq. Reading
        # them separately (read_log's own _rev, then another here) is a live race: a
        # writer landing between the two leaves `seq` stale while `parent` is fresh, so
        # the compare-and-swap passes and two events durably share a seq.
        parent = _rev(repo, log.ref, identity=log.git_identity)
        events = _read_log_at(repo, log=log, tip=parent, validate=validate)
        seq = len(events)
        if prepare is not None:
            built = prepare(events)  # fresh per attempt; may raise GitLogDenied
            if built is None:
                return AppendResult(parent or _ZERO_OID, seq, created=False)  # idempotent no-op
        else:
            assert event is not None  # guarded above
            built = event
            if predicate is not None:
                ok, reason = predicate(events)
                if not ok:
                    raise GitLogDenied(reason)
        if now_field is not None:
            built.setdefault(now_field, datetime.now(UTC).isoformat())
        if finalize is not None:
            built = finalize(built, seq)
        validate(built)  # strict schema: required fields, safe ids, caller invariants
        event_id = str(built["event_id"])
        if not _SAFE_ID.match(event_id):
            raise GitLogError(f"event_id {event_id!r} must match {_SAFE_ID.pattern}")
        # APPEND-ONLY: an event_id is write-once. An IDENTICAL re-append (an in-flight
        # CAS retry) is an idempotent no-op; a DIFFERENT body for the same id is a
        # mutation of committed state → fail closed, never overwrite.
        if parent is not None:
            existing = _read_event_blob(repo, log, event_id, parent)
            if existing is not None:
                if _identity_body(json.loads(existing)) == _identity_body(built):
                    landed = json.loads(existing)
                    return AppendResult(parent, int(landed.get("seq", seq)), created=False)
                raise GitLogError(
                    f"event_id {event_id!r} already exists with DIFFERENT content "
                    "(append-only violation) — failing closed"
                )

        if _after_parent is not None:
            _after_parent()  # TEST-ONLY barrier: parent + seq are fixed, race the CAS

        new_commit = _append_commit(repo, log, parent, built, message_fn(built))
        if log.remote is not None:
            if _push_fast_forward(repo, log, log.remote, new_commit):
                # Sync the local ref to what we successfully pushed.
                _git(["update-ref", log.ref, new_commit], cwd=repo, identity=log.git_identity)
                return AppendResult(new_commit, seq, created=True)
            continue  # concurrent event won — refetch + recompute
        # Local-only CAS: set the ref iff it still equals the observed parent.
        proc = _git(
            ["update-ref", log.ref, new_commit, parent or _ZERO_OID],
            cwd=repo, identity=log.git_identity, check=False,
        )
        if proc.returncode == 0:
            return AppendResult(new_commit, seq, created=True)
        # ref moved under us (same-clone concurrency) — recompute from the new tip.
    raise GitLogContention(
        f"could not fast-forward {log.ref} after {max_retries} attempts (sustained contention)"
    )


__all__ = [
    "AppendResult",
    "GitLogAuthError",
    "GitLogContention",
    "GitLogDenied",
    "GitLogError",
    "LogRef",
    "append_to_log",
    "bootstrap_log",
    "read_log",
    "sync_and_verify",
]
