"""Strict per-record CAS transport for the credit-reservation ledger (spec 026,
slice 1B / FR-016).

The reservation ledger is ONE authoritative append-only log on a dedicated
protected ref — ``refs/llmxive/credit-ledger`` — that EVERY branch and runner
reserves against (never a branch-local copy). Events live at
``reservations/<schema_revision>/<event-id>.json`` and are projected into the
reservation state by :mod:`llmxive.model_selection.reservations`.

The git-CAS machinery itself is domain-agnostic and lives in
:mod:`llmxive.git_event_log` (extracted for spec 025's self-improvement lane,
which needs the same guarantees on its own ref). THIS module is the credit
ledger's identity: its ref, its schema, its config, and its error names. The
transport behavior is unchanged by the extraction — same blob bytes, same tree
shape, same commit message, same CAS/retry structure.

Why not ``scripts/ci/commit-and-push.sh``: its ``-X theirs`` whole-tree rebase
lets a LOSING reservation replay stale admitted state over a winner — that is a
merge, not a compare-and-swap. See :mod:`llmxive.git_event_log` for how git's
native CAS is used instead.

A genuine AUTH / permission failure is distinct from a non-fast-forward
rejection: it raises :class:`LedgerAuthError` so the caller FAILS CLOSED (no paid
call when the ledger is unreachable) rather than silently proceeding unguarded.
"""

from __future__ import annotations

import logging
import math
import os
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from llmxive.git_event_log import (
    GitLogAuthError,
    GitLogContention,
    GitLogDenied,
    GitLogError,
    LogRef,
    append_to_log,
    bootstrap_log,
    read_log,
    sync_and_verify,
)
from llmxive.git_event_log import (
    _append_commit as _core_append_commit,
)
from llmxive.git_event_log import (
    _push_fast_forward as _core_push_fast_forward,
)
from llmxive.git_event_log import (
    _remote_log_oid as _core_remote_log_oid,
)
from llmxive.git_event_log import (
    _rev as _core_rev,
)

logger = logging.getLogger(__name__)

#: The single authoritative ledger ref (a standalone ref, NOT a working branch).
LEDGER_REF = "refs/llmxive/credit-ledger"
#: The funded (real-money) ledger ref — same schema + transport, separate protected ref.
#: On this ref every amount field is USD and ``budget_epoch`` is ``YYYY-MM`` (UTC).
FUNDED_LEDGER_REF = "refs/llmxive/funded-ledger"
#: Bump when the on-disk event schema changes; events are namespaced by it so an
#: old runner's projection never mixes schema revisions.
SCHEMA_REVISION = "v1"
_EVENT_DIR = f"reservations/{SCHEMA_REVISION}"

#: Fixed identity for ledger commits — never depends on the runner's git config.
_GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "llmxive-credit-ledger",
    "GIT_AUTHOR_EMAIL": "ledger@llmxive.local",
    "GIT_COMMITTER_NAME": "llmxive-credit-ledger",
    "GIT_COMMITTER_EMAIL": "ledger@llmxive.local",
}

#: Event/reservation ids become git path segments (reservations/<rev>/<id>.json), so
#: they must be a single safe path component — no "/" (nesting/collision) or "..".
#: (The core enforces the same pattern on ``event_id``; this one also covers
#: ``reservation_id``, which is credit-schema-specific.)
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
_AMOUNT_FIELDS = ("worst_case_credits", "settlement_baseline", "charged")
#: Fields that, when present, MUST parse as an ISO-8601 timestamp.
_TIMESTAMP_FIELDS = ("ts", "created_at", "lease_expires_at", "settled_at")


# The ledger keeps its OWN exception identity, as SUBCLASSES of the core's, and this
# module translates every core error into them at its boundary (`_as_ledger_error`).
#
# Plain aliases (`LedgerError = GitLogError`) were the earlier plan. They kept every
# `except Ledger*` site working — but they also made `type(exc).__name__` report
# `GitLogContention`, and `execute` puts that name in its candidate notes, so the
# money-path assertion `"LedgerContention" in str(...)` failed. The domain's error name
# is observable, not just its catchability.
#
# Subclassing ALONE would have the defect aliasing was chosen to avoid: the core raises
# the BASE class, which `except LedgerError` would not catch. Exhaustive translation at
# the one boundary that calls the core closes that — no `GitLog*` reaches a credit
# caller. Multiple inheritance additionally keeps `except GitLogAuthError` working for
# anyone who reaches for the core's names.
class LedgerError(GitLogError):
    """A ledger transport failure."""


class LedgerAuthError(LedgerError, GitLogAuthError):
    """The authoritative ref is UNREACHABLE (auth/permission/network) — the caller
    MUST fail closed: no paid call may proceed without a working ledger."""


class LedgerContention(LedgerError, GitLogContention):
    """The strict CAS could not fast-forward within the retry budget (sustained
    contention). The caller fails closed rather than force the write."""


class LedgerDenied(LedgerError, GitLogDenied):
    """The credit predicate rejected the reservation against fresh state (e.g. no
    headroom once counting reservations + fresh spend are considered). Distinct
    from contention: the event was NEVER appended by design."""


#: Core → ledger error translation, most specific first.
_ERROR_TRANSLATION = (
    (GitLogAuthError, LedgerAuthError),
    (GitLogContention, LedgerContention),
    (GitLogDenied, LedgerDenied),
    (GitLogError, LedgerError),
)


@contextmanager
def _as_ledger_error() -> Iterator[None]:
    """Re-raise any core error under this domain's name. Applied at EVERY entry point
    that calls the core, so a ``GitLog*`` never escapes to a credit caller."""
    try:
        yield
    except LedgerError:
        raise  # already this domain's (e.g. a `prepare` that raised LedgerDenied)
    except GitLogError as exc:
        for core_cls, ledger_cls in _ERROR_TRANSLATION:
            if isinstance(exc, core_cls):
                raise ledger_cls(str(exc)) from exc
        raise


@dataclass(frozen=True)
class LedgerConfig:
    """Where the authoritative ledger lives + how to trust it (R4-3). Passed to
    EVERY authoritative read and mutation so remote identity + the pinned bootstrap
    anchor are enforced uniformly (production Slice 3 pins ``expected_anchor``). The
    default is local-only — tests / a single-runner / degenerate mode."""

    remote: str | None = None
    expected_anchor: str | None = None
    ref: str = LEDGER_REF


#: Env vars pinning the PRODUCTION ledger location + trust anchor (R5-1). The anchor
#: is the bootstrap commit OID printed by ``credits-ledger-bootstrap``; pinning it
#: makes every authoritative read/write verify the remote tip descends from it.
LEDGER_REMOTE_ENV = "LLMXIVE_CREDIT_LEDGER_REMOTE"
LEDGER_ANCHOR_ENV = "LLMXIVE_CREDIT_LEDGER_ANCHOR"
#: The funded ledger's equivalents (see ``funded_ledger_config_from_env``).
FUNDED_LEDGER_REMOTE_ENV = "LLMXIVE_FUNDED_LEDGER_REMOTE"
FUNDED_LEDGER_ANCHOR_ENV = "LLMXIVE_FUNDED_LEDGER_ANCHOR"


def _log_ref(config: LedgerConfig | None = None, *, ref: str | None = None) -> LogRef:
    """THE ledger's :class:`LogRef` — its ref (``config.ref`` unless ``ref`` overrides),
    subtree, remote, anchor, and fixed commit identity. Built here so every call site
    shares one definition."""
    config = config or LedgerConfig()
    return LogRef(
        ref=ref or config.ref,
        event_dir=_EVENT_DIR,
        remote=config.remote,
        expected_anchor=config.expected_anchor,
        git_identity=_GIT_IDENTITY,
    )


def _canonical(event: dict) -> str:
    """The single canonical on-disk serialization of an event (also the blob body)."""
    from llmxive.git_event_log import _canonical as _core_canonical

    return _core_canonical(event)


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


def _message_fn(event: dict) -> str:
    """The ledger's commit subject — unchanged by the extraction."""
    return (
        f"ledger: {event.get('type', '?')} "
        f"{event.get('reservation_id', '?')} {event['event_id']}"
    )


def _config_from_env(
    *, remote: str | None, require_anchor: bool, remote_env: str, anchor_env: str, ref: str,
    what: str, bootstrap_cmd: str, disabled_effect: str,
) -> LedgerConfig:
    resolved_remote = (remote or os.environ.get(remote_env, "").strip() or "origin")
    anchor = os.environ.get(anchor_env, "").strip() or None
    if require_anchor and anchor is None:
        raise LedgerError(
            f"production {what} not fully configured: set {anchor_env} to the "
            f"pinned bootstrap anchor OID (printed by `llmxive {bootstrap_cmd}`) so the "
            f"ancestry check can reject a wrong/divergent ledger — {disabled_effect} "
            f"until then (fail closed)."
        )
    return LedgerConfig(remote=resolved_remote, expected_anchor=anchor, ref=ref)


def ledger_config_from_env(*, remote: str | None = None, require_anchor: bool = True) -> LedgerConfig:
    """THE single production :class:`LedgerConfig` source (R5-1): the authoritative
    remote (``LLMXIVE_CREDIT_LEDGER_REMOTE``, default ``origin``, overridable via
    ``remote=``) + the pinned bootstrap anchor (``LLMXIVE_CREDIT_LEDGER_ANCHOR``).
    Both ``execute``'s paid path AND the maintenance sweep build their config here so
    they share the SAME remote + anchor (finding-3 / the deferred R5-1 AC).

    FAIL CLOSED (``require_anchor=True``): if the anchor is not pinned, RAISE
    :class:`LedgerError` — paid fallback stays DISABLED until an operator sets it
    (post-bootstrap), rather than running without the ancestry check that guards
    against a wrong/divergent ledger. The ref MUST additionally be protected
    server-side (fast-forward-only, writable only by the ledger identity); that is a
    deploy-time operation, not enforceable in-repo — see the runbook
    ``infra/credit-ledger-ops.md`` (bootstrap, required env, ref protection, token
    identity/permissions).
    """
    return _config_from_env(
        remote=remote, require_anchor=require_anchor, remote_env=LEDGER_REMOTE_ENV,
        anchor_env=LEDGER_ANCHOR_ENV, ref=LEDGER_REF, what="credit ledger",
        bootstrap_cmd="credits-ledger-bootstrap",
        disabled_effect="paid fallback stays disabled",
    )


def funded_ledger_config_from_env(*, remote: str | None = None, require_anchor: bool = True) -> LedgerConfig:
    """The funded (real-money) ledger's :class:`LedgerConfig`: same mechanism as
    :func:`ledger_config_from_env`, but on ``FUNDED_LEDGER_REF`` with its own remote
    (``LLMXIVE_FUNDED_LEDGER_REMOTE``) and pinned anchor
    (``LLMXIVE_FUNDED_LEDGER_ANCHOR``). Fails closed without the anchor."""
    return _config_from_env(
        remote=remote, require_anchor=require_anchor, remote_env=FUNDED_LEDGER_REMOTE_ENV,
        anchor_env=FUNDED_LEDGER_ANCHOR_ENV, ref=FUNDED_LEDGER_REF, what="funded ledger",
        bootstrap_cmd="funded-ledger-bootstrap",
        disabled_effect="funded (Hugging Face) spend stays disabled",
    )


# --- Thin compatibility shims over the core -------------------------------------
# These keep the pre-extraction private names + signatures working for existing
# callers and tests (which must pass with NO edits).


def _rev(repo: Path, ref: str) -> str | None:
    """The commit OID the ref points at, or ``None`` if the ref does not exist."""
    with _as_ledger_error():
        return _core_rev(repo, ref, identity=_GIT_IDENTITY)


def _append_commit(
    repo: Path, parent: str | None, event: dict, config: LedgerConfig | None = None
) -> str:
    """Build (WITHOUT touching the working tree) a new commit that adds exactly
    one event file onto ``parent``'s tree. Returns the new commit OID."""
    with _as_ledger_error():
        return _core_append_commit(repo, _log_ref(config), parent, event, _message_fn(event))


def _push_fast_forward(
    repo: Path, remote: str, commit: str, config: LedgerConfig | None = None
) -> bool:
    """Fast-forward-only push of ``commit`` to the authoritative ref. Returns
    True on success, False on a benign non-fast-forward rejection (a concurrent
    event won — retry). Raises :class:`LedgerAuthError` on auth/permission."""
    with _as_ledger_error():
        return _core_push_fast_forward(repo, _log_ref(config), remote, commit)


def _remote_ledger_oid(repo: Path, remote: str, config: LedgerConfig | None = None) -> str | None:
    """The OID the ledger ref points at ON THE REMOTE (via ``ls-remote``), or
    ``None`` if the remote genuinely has no such ref. Fails closed
    (:class:`LedgerAuthError`) if the remote cannot be queried."""
    with _as_ledger_error():
        return _core_remote_log_oid(repo, _log_ref(config), remote)


def _sync_and_verify(repo: Path, config: LedgerConfig) -> None:
    """Bring the local ledger ref into agreement with the AUTHORITATIVE remote and
    verify its identity before any read/mutation projects it (R3/R4-3)."""
    with _as_ledger_error():
        sync_and_verify(repo, log=_log_ref(config))


def fetch_ledger(repo: Path, config: LedgerConfig) -> None:
    """Sync + verify the authoritative ledger before a projection (fixes #3/R4-3).
    Any read that gates admission or reconciliation — ``sweep``, ``reconcile_settled``,
    production headroom reads — MUST call this first: a fresh Actions checkout does not
    fetch ``refs/llmxive/credit-ledger``, so an un-synced local projection is EMPTY and
    every downstream decision is silently blind."""
    _sync_and_verify(repo, config)


def read_events(repo: Path, *, ref: str = LEDGER_REF) -> list[dict]:
    """Every event currently recorded on ``ref`` (empty if the ref is absent).
    Reads straight from the object store — the ledger ref is never checked out."""
    with _as_ledger_error():
        return read_log(repo, log=_log_ref(ref=ref), validate=_validate_event)


def bootstrap_ledger(repo: Path, remote: str | None = None, *, ref: str = LEDGER_REF) -> str:
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
    with _as_ledger_error():
        return bootstrap_log(
            repo,
            log=_log_ref(ref=ref),
            message=(
                f"bootstrap credit-ledger {SCHEMA_REVISION}" if ref == LEDGER_REF
                else f"bootstrap ledger {ref} {SCHEMA_REVISION}"
            ),
            remote=remote,
        )


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

    Each attempt: (1) sync + verify the authoritative ref per ``config`` (remote
    existence + pinned-anchor identity; fails closed if not bootstrapped); (2) re-read
    the events; (3) BUILD the event — either the fixed ``event`` (optionally gated by
    ``predicate``) or, for callers that must price against FRESH state each attempt
    (``reserve``), ``prepare(events)`` which returns the event to append, ``None`` for
    an idempotent no-op, or raises :class:`LedgerDenied`; (4) stamp ``ts``; (5) enforce
    append-only immutability; (6) append onto the current tip; (7) fast-forward the ref
    (``update-ref`` CAS locally, FF push remotely); (8) on non-fast-forward, refetch and
    recompute.

    ``prepare`` is re-invoked on EVERY attempt so the event's epoch / settlement
    baseline reflect a fresh, internally-consistent credit observation (fixes #2 —
    the daily-reset race). Returns the tip commit OID.
    """
    with _as_ledger_error():
        return append_to_log(
            repo,
            log=_log_ref(config),
            validate=_validate_event,
            message_fn=_message_fn,
            event=event,
            prepare=prepare,
            predicate=predicate,
            now_field="ts",   # reproduces the pre-extraction `built.setdefault("ts", ...)`
            finalize=None,    # the ledger stamps no seq / revision anchors
            identity_exclude=frozenset(),  # append-only guard compares the FULL body
            max_retries=max_retries,
        ).commit


__all__ = [
    "FUNDED_LEDGER_ANCHOR_ENV",
    "FUNDED_LEDGER_REF",
    "FUNDED_LEDGER_REMOTE_ENV",
    "LEDGER_ANCHOR_ENV",
    "LEDGER_REF",
    "LEDGER_REMOTE_ENV",
    "SCHEMA_REVISION",
    "LedgerAuthError",
    "LedgerConfig",
    "LedgerContention",
    "LedgerDenied",
    "LedgerError",
    "append_event",
    "bootstrap_ledger",
    "fetch_ledger",
    "funded_ledger_config_from_env",
    "ledger_config_from_env",
    "read_events",
]
