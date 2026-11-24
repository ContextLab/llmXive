"""Is a cross-stream transaction INTACT? (spec 025 slice 2, FR-035's invariant matrix.)

A transaction that spans the coordinator and an Attempt is one commit, so "both halves
landed together" is a checkable property of the log rather than a promise by whoever wrote
it. Everything here answers one question — does what is stored look like something ONE
transaction produced — and raises :class:`LaneInconsistent` when it does not.

**Why its own module.** These checks have three callers that must apply the SAME strength
(Constitution I): `lifecycle.cas_attempt_transition` replaying matrix rows 2/4,
`coordinator.cas_claim` replaying row 1, and the auditor `assert_lane_consistent` walking
all of history. `lifecycle` already imports `coordinator` (it reads the lane's ownership),
so putting them in `coordinator` would force `coordinator` to import `lifecycle` back the
moment row 1's replay or the auditor needs them — a genuine import cycle, not a stylistic
one. Sitting below both, this module imports only the store and the event vocabulary.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from llmxive.self_improvement.events import (
    COORDINATOR_STREAM,
    Event,
    coordinator_event_id,
    payload_field,
)
from llmxive.self_improvement.lane_log import LaneLogConfig, events_by_commit


class LaneInconsistent(RuntimeError):
    """A cross-stream transaction is not intact: a declared half is missing, malformed, or
    was added by a different commit than its partner.

    Distinct from ``LaneRevisionConflict`` (someone else got there first — retry) and from
    ``IllegalTransition`` (this event cannot follow that state — a caller bug). This one
    means the LOG disagrees with itself, so there is nothing to retry and nothing to
    recompute: fail closed and stop."""


def assert_member_identity(event: Event, expected_type: str, stream: str,
                           problem_id: str, attempt_id: str) -> None:
    """A located record IS the record it was located as: right type, right stream, naming
    this Problem and Attempt. Raise otherwise.

    Every caller that finds a record by DERIVED ID needs this, because a derived id is a
    hypothesis ("if this transaction landed, its record is here") and the record found there
    is evidence, not proof. Reusing it verbatim without checking is how a corrupt record
    gets replayed as a healthy transaction — ``append_many`` cannot catch it, since on the
    replay path each stored event is compared against ITSELF.

    ``expected_type`` is REQUIRED and has no default. An earlier revision made the anchor's
    type check optional, and both replay paths then silently omitted it: the parameter
    existed, defaulted to ``None``, and disabled exactly the check it was added for. A
    caller that genuinely cannot name a type must not call this function at all.

    Not every check is reachable from every caller, and that is fine — the ANCHOR of an
    Attempt-side replay is selected out of a stream read by `problem_id` and filtered by the
    envelope `attempt_id`, and `validate_lane_event` has already refused any record whose
    payload disagrees with its envelope, so for that caller only the TYPE check can fire.
    Partners are located by id alone among all coordinator events, where all three can."""
    if event.event_type != expected_type:
        raise LaneInconsistent(
            f"{problem_id}/{attempt_id}: expected {expected_type} on {stream!r}, "
            f"found {event.event_type}")
    if event.problem_id != stream:
        raise LaneInconsistent(
            f"{problem_id}/{attempt_id}: {event.event_type} is on stream "
            f"{event.problem_id!r}, expected {stream!r}")
    if (payload_field(event, "problem_id"), payload_field(event, "attempt_id")) != (
            problem_id, attempt_id):
        raise LaneInconsistent(
            f"{problem_id}/{attempt_id}: {event.event_type} names "
            f"{payload_field(event, 'problem_id')}/"
            f"{payload_field(event, 'attempt_id')} instead")


def assert_partner_intact(*, anchor: Event, partner: Event | None, coordinator_event: str,
                          compare: tuple[str, ...],
                          commit_of: Mapping[tuple[str, str], str],
                          problem_id: str, attempt_id: str) -> Event:
    """One anchor→partner pairing, checked to the FULL strength of the matrix, or raise.

    Four things, in the order a corruption is cheapest to describe: the partner exists; it
    is the declared type on the coordinator stream naming this Problem and Attempt
    (:func:`assert_member_identity`); both members were introduced by the SAME commit; and
    the fields the row calls shared agree.

    **The ANCHOR's own identity is the caller's job, not this function's**, because only the
    caller knows how the anchor was obtained. A caller that located it by derived id (both
    replay paths) MUST call :func:`assert_member_identity` on it first; the auditor need not,
    because its anchor comes out of ``walk_attempt``, which has already refused unknown types
    and illegal transitions. Making that an optional parameter here was the bug: it read as
    covered and was not.

    ``actor`` and ``timestamp`` are checked unconditionally — every row builds all of its
    members from one actor and one timestamp, and the store never stamps them itself
    (``lane_log.append``/``append_many`` pass no ``now_field``, so ``git_event_log``'s
    ``setdefault`` never fires and the caller's values are what land). If a future row
    legitimately writes its halves under different identities, that belongs beside the row's
    declaration — not as a weakening here.

    They previously carried three strengths of the same check, weakest at the writer: the
    replay path verified only that a partner was PRESENT. A record at a derived id can be
    present and still be the wrong type, name another Attempt, or — the one presence can
    never see — have been added by a DIFFERENT COMMIT, which is a transaction that was
    re-split into two and is exactly the regression the atomicity argument rests on. Feeding
    such a record back to ``append_many`` proves nothing, because there each stored event is
    compared against ITSELF: on the replay path append-only validation is a tautology, so
    everything it cannot see must be checked here.

    ``commit_of`` is passed in rather than read, so a caller checking several pairings pays
    for one :func:`events_by_commit` traversal."""
    if partner is None:
        raise LaneInconsistent(
            f"{problem_id}/{attempt_id}: {anchor.event_type} is present but its "
            f"{coordinator_event} is not — half a transaction, which nothing that writes "
            "this lane can produce")
    assert_member_identity(partner, coordinator_event, COORDINATOR_STREAM,
                           problem_id, attempt_id)
    # Scoped by (stream, id) — the store's identity, not the bare id.
    commits = {}
    for event in (anchor, partner):
        commit = commit_of.get((event.problem_id, event.event_id))
        if commit is None:
            raise LaneInconsistent(
                f"{problem_id}/{attempt_id}: no commit introduces {event.event_type} — "
                "the ref does not contain a record that `read` returned")
        commits[event.event_type] = commit
    if len(set(commits.values())) != 1:
        # Both present is not the invariant; both present IN ONE COMMIT is.
        raise LaneInconsistent(
            f"{problem_id}/{attempt_id}: " + " and ".join(
                f"{t} was added by {c}" for t, c in commits.items()) +
            " — the matrix says one transaction writes both")
    for field in compare:
        if payload_field(anchor, field) != payload_field(partner, field):
            raise LaneInconsistent(
                f"{problem_id}/{attempt_id}: {field} is "
                f"{payload_field(anchor, field)!r} on {anchor.event_type} and "
                f"{payload_field(partner, field)!r} on {partner.event_type} — one "
                "transaction wrote both from one construction, so they cannot disagree")
    if (anchor.actor, anchor.timestamp) != (partner.actor, partner.timestamp):
        raise LaneInconsistent(
            f"{problem_id}/{attempt_id}: the halves disagree on actor/timestamp "
            f"({anchor.actor}@{anchor.timestamp} vs {partner.actor}@{partner.timestamp}); "
            "the replay path reuses both verbatim, so a disagreement here would be carried "
            "forward as fact")
    return partner


def replayed_transaction(repo: Path, stored: Event, declared_effects: tuple[str, ...],
                         coordinator_events: list[Event], *, problem_id: str,
                         attempt_id: str, expected_event_type: str, required: bool,
                         config: LaneLogConfig | None = None) -> list[Event]:
    """The event set of an already-landed cross-stream transaction, LOCATED not rebuilt.

    ``cas_attempt_transition`` (rows 2 and 4) and ``cas_reclaim`` (row 3) call it with the
    effects their row DECLARES and with ``required`` = whether the Attempt held the lane in
    the state the stored event was written from. Both clauses of the conditional-effects
    rule are checked here, not only the one that expects a partner — passing the pruned list
    instead of ``(declared, required)`` would make "correctly wrote nothing" and "wrongly
    holds another Attempt's release" the same input.

    Row 1 does NOT, and the reason is worth stating so nobody "unifies" it later: there, the
    Attempt-side ``ClaimGranted`` is not a reliable anchor — the surviving half can be
    EITHER one, and ``cas_claim`` must detect a lone ``ClaimAcquired`` (a lane wedged behind
    an Attempt that never started) as well as a lone grant. Its bidirectional check is a
    stronger test, not a duplicate of this one; folding it into this shape would delete a
    case.

    Two properties, both learned the hard way:

    **Located, not rebuilt.** ``actor`` is part of an event's identity
    (``lane_log._IDENTITY_EXCLUDE`` covers ``seq``, ``timestamp`` and the revision anchors —
    not ``actor``), and recovery routinely runs under a different runner identity than the
    one that died. Rebuilding would produce a different body under the same derived id and
    fail append-only validation on exactly the cross-runner retry the lost-acknowledgement
    contract exists to make survivable.

    **Intact or refused.** A stored Attempt event whose declared partner is missing is half
    a transaction; one whose partner is present but malformed, or present but added by a
    different commit, is a transaction that was never atomically written. Returning the
    Attempt event anyway would let the retry report success while the damage went
    unmentioned — the naive replay's failure, and the reason a row-4 replay could pass with
    its ``MonitorStarted`` gone. Completing a missing half instead is the repair this design
    does not offer: it would finish a transaction that was never atomically started."""
    # FIRST, and on BOTH branches below: the anchor was located by a derived id, so its own
    # identity is a hypothesis until checked. The `not required` path returns it with no
    # partner to cross-check against, which makes this the only thing standing between a
    # corrupt record at the right id and a replay reported as success.
    assert_member_identity(stored, expected_event_type, problem_id, problem_id, attempt_id)
    found = {
        name: next((e for e in coordinator_events
                    if e.event_id == coordinator_event_id(name, problem_id, attempt_id)),
                   None)
        for name in declared_effects
    }
    if not required:
        # Clause 3 of the conditional-effects rule, which the auditor also enforces: a row
        # can DECLARE an effect and correctly not have written one. Then the absence is the
        # invariant, and a partner that exists released somebody else's claim.
        present = sorted(name for name, event in found.items() if event is not None)
        if present:
            raise LaneInconsistent(
                f"{problem_id}/{attempt_id}: {stored.event_type} was written from a state "
                f"that held nothing, so it wrote no coordinator effect — but "
                f"{', '.join(present)} exists for it, which released another Attempt's "
                "claim")
        return [stored]
    commit_of = events_by_commit(repo, config=config)
    return [stored, *(
        assert_partner_intact(anchor=stored, partner=found[name], coordinator_event=name,
                              compare=(), commit_of=commit_of,
                              problem_id=problem_id, attempt_id=attempt_id)
        for name in declared_effects)]


__all__ = [
    "LaneInconsistent",
    "assert_member_identity",
    "assert_partner_intact",
    "replayed_transaction",
]
