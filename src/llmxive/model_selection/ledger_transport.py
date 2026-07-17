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
import math
import os
import re
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
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
# closed) as opposed to a benign non-fast-forward rejection (retry). CONTEXTUAL only
# (R4-1): a bare "401"/"403" matched random commit OIDs in a concurrent
# "cannot lock ref ... expected <OID>" rejection and misclassified it as an auth
# failure — every marker here must be a phrase that cannot appear inside a hex OID.
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
#: The reservation-event schema this ledger accepts (this IS the credit-reservation
#: ledger — the full per-type schema lives here so it is enforced on EVERY read and
#: write, with NO downstream defaults for safety-critical fields).
_KNOWN_EVENT_TYPES = frozenset({"open", "heartbeat", "settling", "reconciled"})
#: Fields REQUIRED for each event type (beyond the universal event_id/reservation_id/
#: type/ts). Missing → fail closed (a missing worst_case_credits would otherwise
#: project as a phantom 0-credit counting reservation → overspend).
_REQUIRED_BY_TYPE = {
    "open": ("worst_case_credits", "model", "budget_epoch", "settlement_baseline", "created_at", "lease_expires_at"),
    "heartbeat": ("lease_expires_at",),
    "settling": (),
    "reconciled": (),
}
#: Credit-amount fields that MUST be finite and non-negative when present.
_AMOUNT_FIELDS = ("worst_case_credits", "settlement_baseline")
#: Fields that, when present, MUST parse as an ISO-8601 timestamp.
_TIMESTAMP_FIELDS = ("ts", "created_at", "lease_expires_at", "settled_at")


def _canonical(event: dict) -> str:
    """The single canonical on-disk serialization of an event (also the blob body)."""
    return json.dumps(event, indent=2, sort_keys=True)


def _validate_event(event: dict) -> None:
    """STRICT schema validation for a reservation-ledger event — enforced BOTH at
    the write boundary (append) AND on every read (fixes R3-1). Rejects any event
    that could corrupt the projection: missing universal fields; unsafe/known-type
    violations; missing per-type required fields (e.g. an ``open`` without
    ``worst_case_credits`` would project as a phantom 0-credit counting reservation);
    non-finite/negative amounts; unparseable timestamps; an empty ``budget_epoch``
    on an ``open`` (would silently drop out of every epoch's counting)."""
    for key in ("event_id", "reservation_id", "type", "ts"):
        if key not in event:
            raise ValueError(f"ledger event missing required field {key!r}")
    for key in ("event_id", "reservation_id"):
        if not _SAFE_ID.match(str(event[key])):
            raise ValueError(f"ledger {key}={event[key]!r} must match {_SAFE_ID.pattern}")
    etype = event["type"]
    if etype not in _KNOWN_EVENT_TYPES:
        raise ValueError(f"ledger event type {etype!r} not in {sorted(_KNOWN_EVENT_TYPES)}")
    for field in _REQUIRED_BY_TYPE[etype]:
        if field not in event:
            raise ValueError(f"ledger {etype!r} event missing required field {field!r}")
    for field in _AMOUNT_FIELDS:
        if field in event:
            val = event[field]
            if not isinstance(val, (int, float)) or isinstance(val, bool) or not math.isfinite(val):
                raise ValueError(f"ledger event {field}={val!r} must be a finite number")
            if val < 0:
                raise ValueError(f"ledger event {field}={val!r} must be non-negative")
    for field in _TIMESTAMP_FIELDS:
        if field in event:
            try:
                datetime.fromisoformat(str(event[field]))
            except ValueError as exc:
                raise ValueError(f"ledger event {field}={event[field]!r} is not an ISO timestamp") from exc
    if etype == "open" and not str(event.get("budget_epoch", "")).strip():
        raise ValueError("ledger 'open' event has an empty budget_epoch")


def _read_event_blob(repo: Path, event_id: str, tip: str) -> str | None:
    """The stored body of ``<event_id>.json`` at ``tip``, or ``None`` if absent."""
    proc = _git(
        ["cat-file", "-p", f"{tip}:{_EVENT_DIR}/{event_id}.json"], cwd=repo, check=False
    )
    return proc.stdout if proc.returncode == 0 else None


@dataclass(frozen=True)
class LedgerConfig:
    """Where the authoritative ledger lives + how to trust it (R4-3). Passed to
    EVERY authoritative read and mutation so remote identity + the pinned bootstrap
    anchor are enforced uniformly (production Slice 3 pins ``expected_anchor``). The
    default is local-only — tests / a single-runner / degenerate mode."""

    remote: str | None = None
    expected_anchor: str | None = None


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
            event = json.loads(blob)
        except json.JSONDecodeError as exc:
            # FAIL CLOSED (C4): this is the AUTHORITATIVE financial ledger, not a
            # cache. Skipping a corrupt event could drop a COUNTING reservation from
            # the projection → under-count → phantom headroom → overspend.
            raise LedgerError(f"corrupt ledger event {path!r}: {exc}") from exc
        # Re-validate on READ too (R3-1): a manually-corrupted or older malformed
        # event on the authoritative ref must NOT slip past write-time validation.
        if not isinstance(event, dict):
            raise LedgerError(f"ledger event {path!r} is not an object")
        try:
            _validate_event(event)
        except ValueError as exc:
            raise LedgerError(f"invalid ledger event {path!r}: {exc}") from exc
        # The filename MUST match the payload id (a rename/mismatch is tampering).
        if Path(path).stem != str(event["event_id"]):
            raise LedgerError(
                f"ledger event path {path!r} does not match payload event_id "
                f"{event['event_id']!r}"
            )
        events.append(event)
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


def _remote_ledger_oid(repo: Path, remote: str) -> str | None:
    """The OID the ledger ref points at ON THE REMOTE (via ``ls-remote``), or
    ``None`` if the remote genuinely has no such ref. Fails closed (LedgerAuthError)
    if the remote cannot be queried — a missing ref must never be inferred from an
    auth/network failure. Checking the REMOTE (not the possibly-stale LOCAL ref) is
    what stops a pre-existing local ledger + empty/wrong remote from being treated
    as bootstrapped (R3-4)."""
    proc = _git(["ls-remote", remote, LEDGER_REF], cwd=repo, check=False)
    if proc.returncode != 0:
        raise LedgerAuthError(
            f"cannot query {remote!r} for {LEDGER_REF}: {proc.stderr.strip()} — failing closed"
        )
    line = proc.stdout.strip()
    return line.split()[0] if line else None


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    """True iff ``ancestor`` is reachable from ``descendant`` (shared ledger history)."""
    return (
        _git(["merge-base", "--is-ancestor", ancestor, descendant], cwd=repo, check=False).returncode
        == 0
    )


def bootstrap_ledger(repo: Path, remote: str | None = None) -> str:
    """Bring the authoritative ledger into existence with an empty anchor commit —
    the ONE-TIME, EXPLICIT administrative operation (R3-4). NOT part of the routine
    sweep. Every other write path fails closed when the remote ref is absent, so this
    is the only sanctioned creator. Returns the anchor commit OID.

    Divergence guard (R3-4): when ``remote`` is given, the REMOTE (not the possibly
    stale local ref) is authoritative. If the remote already has the ledger it is
    adopted (no-op). If the remote is EMPTY but a LOCAL ledger already exists, that is
    a wrong/misconfigured remote — bootstrapping would push a divergent ledger — so it
    FAILS CLOSED rather than create one. Production should additionally protect the ref
    server-side (a protected ref / branch-protection rule allowing only fast-forward
    appends by the ledger identity) and pin the anchor for the ancestry check that the
    read/write paths perform (see ``LedgerConfig(expected_anchor=...)``)."""
    if remote is not None:
        remote_oid = _remote_ledger_oid(repo, remote)
        if remote_oid is not None:
            _fetch_authoritative(repo, remote)  # already bootstrapped remotely — adopt it
            return _rev(repo, LEDGER_REF) or remote_oid
        if _rev(repo, LEDGER_REF) is not None:
            raise LedgerAuthError(
                f"refusing to bootstrap {remote!r}: a LOCAL ledger exists but the remote has "
                "none — a wrong/misconfigured remote would receive a DIVERGENT ledger. Verify "
                "the remote (or clear the local ref if this is a deliberate re-init)."
            )
    elif _rev(repo, LEDGER_REF) is not None:
        return _rev(repo, LEDGER_REF)

    with tempfile.TemporaryDirectory() as td:
        env = {"GIT_INDEX_FILE": os.path.join(td, "index")}
        empty_tree = _git(["write-tree"], cwd=repo, extra_env=env).stdout.strip()  # empty index → empty tree
    commit = _git(
        ["commit-tree", empty_tree, "-m", f"bootstrap credit-ledger {SCHEMA_REVISION}"], cwd=repo
    ).stdout.strip()
    proc = _git(["update-ref", LEDGER_REF, commit, _ZERO_OID], cwd=repo, check=False)
    if proc.returncode != 0:  # a concurrent bootstrap won locally
        return _rev(repo, LEDGER_REF) or commit
    if remote is not None and not _push_fast_forward(repo, remote, commit):
        # a concurrent bootstrap won remotely — adopt it as authoritative
        _fetch_authoritative(repo, remote)
        return _rev(repo, LEDGER_REF) or commit
    return commit


def _sync_and_verify(repo: Path, config: LedgerConfig) -> None:
    """Bring the local ledger ref into agreement with the AUTHORITATIVE remote and
    verify its identity before any read/mutation projects it (R3/R4-3). For a remote
    config: the ref MUST already EXIST on the remote — bootstrap is the only creator,
    so a missing ref fails closed (not treated as an empty local projection); the ref
    is then synced locally; and if an anchor is pinned, the remote tip MUST descend
    from it (else a wrong/unrelated ledger — fail closed). Local-only = no-op."""
    if config.remote is None:
        return
    remote_oid = _remote_ledger_oid(repo, config.remote)
    if remote_oid is None:
        raise LedgerAuthError(
            f"ledger ref {LEDGER_REF} absent on {config.remote!r} — not bootstrapped "
            "(run `credits-ledger-bootstrap` once); failing closed"
        )
    _fetch_authoritative(repo, config.remote)
    if config.expected_anchor is not None and not _is_ancestor(repo, config.expected_anchor, remote_oid):
        raise LedgerAuthError(
            f"remote {LEDGER_REF} tip {remote_oid} does not descend from the pinned anchor "
            f"{config.expected_anchor} — wrong/divergent ledger; failing closed"
        )


def fetch_ledger(repo: Path, config: LedgerConfig) -> None:
    """Sync + verify the authoritative ledger before a projection (fixes #3/R4-3).
    Any read that gates admission or reconciliation — ``sweep``, ``reconcile_settled``,
    production headroom reads — MUST call this first: a fresh Actions checkout does not
    fetch ``refs/llmxive/credit-ledger``, so an un-synced local projection is EMPTY and
    every downstream decision is silently blind."""
    _sync_and_verify(repo, config)


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
    event: dict | None = None,
    *,
    prepare: Callable[[list[dict]], dict | None] | None = None,
    config: LedgerConfig | None = None,
    predicate: Callable[[list[dict]], tuple[bool, str]] | None = None,
    max_retries: int = 8,
) -> str:
    """Append ONE event to the authoritative ledger under strict CAS.

    Each attempt: (1) ``_sync_and_verify`` the authoritative ref per ``config``
    (remote existence + pinned-anchor identity; fails closed if not bootstrapped);
    (2) re-read the events; (3) BUILD the event — either the fixed ``event``
    (optionally gated by ``predicate``) or, for callers that must price against
    FRESH state each attempt (``reserve``), ``prepare(events)`` which returns the
    event to append, ``None`` for an idempotent no-op, or raises
    :class:`LedgerDenied`; (4) enforce append-only immutability; (5) append onto the
    current tip; (6) fast-forward the ref (``update-ref`` CAS locally, FF push
    remotely); (7) on non-fast-forward, refetch and recompute.

    ``prepare`` is re-invoked on EVERY attempt so the event's epoch / settlement
    baseline reflect a fresh, internally-consistent credit observation (fixes #2 —
    the daily-reset race). Returns the tip commit OID.
    """
    if (event is None) == (prepare is None):
        raise ValueError("append_event requires exactly one of 'event' or 'prepare'")
    config = config or LedgerConfig()

    for _attempt in range(max_retries):
        _sync_and_verify(repo, config)  # remote existence + anchor identity; fails closed
        events = read_events(repo)
        if prepare is not None:
            built = prepare(events)  # fresh per attempt; may raise LedgerDenied
            if built is None:
                return _rev(repo, LEDGER_REF) or _ZERO_OID  # idempotent no-op
        else:
            built = event
            if predicate is not None:
                ok, reason = predicate(events)
                if not ok:
                    raise LedgerDenied(reason)
        built.setdefault("ts", datetime.now(UTC).isoformat())
        _validate_event(built)  # strict schema (fixes #1): required fields, finite non-neg amounts
        body = _canonical(built)
        event_id = str(built["event_id"])
        parent = _rev(repo, LEDGER_REF)
        # APPEND-ONLY (fixes #1): an event_id is write-once. An IDENTICAL re-append
        # (an in-flight CAS retry) is an idempotent no-op; a DIFFERENT body for the
        # same id is a mutation of committed state → fail closed, never overwrite.
        if parent is not None:
            existing = _read_event_blob(repo, event_id, parent)
            if existing is not None:
                if existing == body:
                    return parent
                raise LedgerError(
                    f"event_id {event_id!r} already exists with DIFFERENT content "
                    "(append-only violation) — failing closed"
                )
        new_commit = _append_commit(repo, parent, built)
        if config.remote is not None:
            if _push_fast_forward(repo, config.remote, new_commit):
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
    "LedgerConfig",
    "LedgerContention",
    "LedgerDenied",
    "LedgerError",
    "append_event",
    "bootstrap_ledger",
    "fetch_ledger",
    "read_events",
]
