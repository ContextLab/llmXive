"""Shared drivers for the lifecycle model tests: build a synthetic history that REACHES a
given state, using only the declared table — so the helper cannot encode a path the machine
does not actually allow."""
from __future__ import annotations

import re
from collections import deque
from collections.abc import Sequence
from itertools import count
from pathlib import Path
from typing import Any

from llmxive.self_improvement.events import Event, derive_event_id
from llmxive.self_improvement.lifecycle import (
    NON_TRANSITION_EVENTS,
    TRANSITIONS,
    AttemptState,
    legal_events_from,
)

TS = "2026-07-31T12:00:00+00:00"

#: Distinguishes "caller said nothing" from "caller said None", which is itself a case the
#: invariant tests must be able to build.
_UNSET: Any = object()

_SEQ = count()

#: Every event type whose payload the fold reads a claim generation out of. Supplied by
#: default so a history built here is one the writers could actually have produced: a
#: `ClaimGranted` with no generation is refused by `walk_attempt`, and a helper that emitted
#: one would make every claim-reaching test fail for a reason unrelated to what it asserts.
_GENERATION_DEFAULT = {"ClaimGranted": 1, "ClaimExpired": 1, "ClaimHeartbeat": 1}

#: A stand-in for every payload field the TABLE declares as part of an idempotency key.
#: Keyed by FIELD and applied through `Transition.key_fields`, so declaring a new keyed row
#: is all it takes to cover it here. Same rule as the generation defaults, one layer out:
#: the fold does not READ these, but no writer can produce a keyed transition without them,
#: so a history containing one is not a history the machine could have reached.
_KEY_FIELD_DEFAULT: dict[str, Any] = {
    "head_sha": "a" * 40, "reason": "regression", "lane_revision": 0, "claim_generation": 1}

_undefaulted = {f for t in TRANSITIONS for f in t.key_fields
                if f not in _KEY_FIELD_DEFAULT}
if _undefaulted:   # at IMPORT: a silent omission would build unproducible histories
    raise AssertionError(
        f"idempotency-key fields with no test default: {sorted(_undefaulted)}")

_KEY_DEFAULTS: dict[str, dict[str, Any]] = {
    t.event: {f: _KEY_FIELD_DEFAULT[f] for f in t.key_fields}
    for t in TRANSITIONS if t.key_fields}


def attempt_event(event_type: str, *, attempt_id: str = "A1", problem_id: str = "P1",
                  payload: dict | None = None, seq: int | None = _UNSET) -> Event:
    """One Attempt event, sequenced the way the store sequences one.

    ``seq`` defaults to the next value from a monotonic counter, so histories built by
    repeated calls satisfy the strictly-increasing invariant `project_attempt` enforces
    without every caller threading positions. Pass ``seq=`` explicitly to build the
    out-of-order and gapped histories the invariant tests need — including ``seq=None``,
    which is why the default is a sentinel rather than ``None``.

    An explicit ``payload`` OVERRIDES the generation default, which is what lets a test
    build the stale-generation beat the fencing token exists to detect."""
    body: dict[str, Any] = {"problem_id": problem_id, "attempt_id": attempt_id}
    if event_type in _GENERATION_DEFAULT:
        body["claim_generation"] = _GENERATION_DEFAULT[event_type]
    body.update(_KEY_DEFAULTS.get(event_type, {}))
    body.update(payload or {})
    return Event(
        event_id=derive_event_id(problem_id, f"{event_type}\x00{attempt_id}"),
        event_type=event_type, problem_id=problem_id, actor="test",
        payload=body, timestamp=TS, attempt_id=attempt_id,
        seq=next(_SEQ) if seq is _UNSET else seq,
    )


class Clock:
    """A monotonic instant source with the shape `cas_attempt_transition` takes.

    Distinct timestamps per call, because several assertions turn on two records sharing
    ONE construction: a clock returning a constant would make `assert_partner_intact`'s
    actor/timestamp agreement check pass for halves that were built separately."""

    def __init__(self, start: int = 0) -> None:
        self._n = start

    def __call__(self) -> str:
        self._n += 1
        return f"2026-08-04T12:{self._n // 60:02d}:{self._n % 60:02d}+00:00"


def seed_claim(repo, *, problem_id: str = "P1", attempt_id: str = "A1",
               generation: int = 1, actor: str = "seed", clock: Clock | None = None,
               config=None, already_proposed: bool = False) -> Event:
    """Put the lane in the state a paired claim leaves it in, WITHOUT going through
    `cas_claim`.

    Writes the same two records in the same ONE commit that Task 8's paired `cas_claim`
    will — so tests assert against the claim's SHAPE rather than against whichever version
    of `cas_claim` exists when they run, and Task 8 replacing that function leaves them
    green. Slice 1A's `cas_claim` writes only the coordinator's `ClaimAcquired`, which would
    leave the Attempt at `proposal_verified` with no claim-holding transition legal.

    It is a FIXTURE, not a second claim API: it takes no preconditions and lives in
    `tests/helpers/`, so nothing in `src/` can reach it.

    `already_proposed` skips the two opening transitions for an Attempt a test has already
    started — the claim-status race needs an Attempt that exists before the lane moves.

    Returns the grant, so a test re-issuing it through the real path can pass the SAME
    key-bearing payload rather than a guess at what the fixture chose."""
    from llmxive.self_improvement.coordinator import project_coordinator
    from llmxive.self_improvement.events import COORDINATOR_STREAM, coord_event
    from llmxive.self_improvement.lane_log import append_many, read
    from llmxive.self_improvement.lifecycle import TRANSITIONS, cas_attempt_transition

    clock = clock or Clock()
    if not already_proposed:
        for event_type in ("Proposed", "ProposalVerified"):
            cas_attempt_transition(repo, problem_id=problem_id, attempt_id=attempt_id,
                                   event_type=event_type, payload={}, actor=actor,
                                   clock=clock, config=config)
    else:
        cas_attempt_transition(repo, problem_id=problem_id, attempt_id=attempt_id,
                               event_type="ProposalVerified", payload={}, actor=actor,
                               clock=clock, config=config)
    problem_events = read(repo, problem_id, config=config)
    coordinator_events = read(repo, COORDINATOR_STREAM, config=config)
    timestamp = clock()
    row = next(t for t in TRANSITIONS if t.event == "ClaimGranted")
    payload = {"problem_id": problem_id, "attempt_id": attempt_id,
               # The grant's key is `(attempt_id,"claim",lane_revision)`, so the revision it
               # was granted AT is part of the record, not just of the CAS below.
               "claim_generation": generation,
               "lane_revision": project_coordinator(coordinator_events).lane_revision}
    grant = Event(
        # Derived BY THE ROW, not rebuilt from its parts. A hand-written copy of the
        # derivation is a second implementation of the idempotency key: this fixture stands
        # in for `cas_attempt_transition`, so a copy that drifted would make every
        # claim-holding test assert against a claim the real path can no longer produce.
        event_id=row.event_id(problem_id, attempt_id, payload),
        event_type="ClaimGranted", problem_id=problem_id, actor=actor,
        payload=payload, timestamp=timestamp, attempt_id=attempt_id,
    )
    acquired = coord_event("ClaimAcquired", problem_id=problem_id, attempt_id=attempt_id,
                           payload={"problem_id": problem_id, "attempt_id": attempt_id},
                           actor=actor, timestamp=timestamp)
    append_many(repo, [acquired, grant],
                expected_revisions={COORDINATOR_STREAM: len(coordinator_events),
                                    problem_id: len(problem_events)},
                config=config)
    return grant


def witness_payload(state: AttemptState | None, event_type: str) -> dict[str, str]:
    """The payload term a transition's state witness requires when taken FROM ``state``.

    `attempt_event` supplies the generation defaults on its own because they depend only on
    the event type; a witness term depends on the SOURCE STATE, which only a builder walking
    a history knows. Same rule though — a history built by these helpers must be one the
    writers could have produced, or tests start failing (or worse, PASSING) for reasons
    unrelated to what they assert: `drive(REVIEW_ABORTED)` without this yields a history the
    fold refuses for a missing `stage`, which still satisfies a `pytest.raises` looking for
    "already terminal".

    Returns `{}` when the step is not legal from ``state`` — the fold will refuse it, and
    inventing a witness for a transition that cannot happen would mask that refusal."""
    transition = next((t for t in TRANSITIONS if t.event == event_type
                       and (state in t.from_states if state is not None
                            else not t.from_states)), None)
    if transition is None or transition.witness is None:
        return {}
    term = transition.witness.term(state)
    return {} if term is None else {transition.witness.field: term}


def next_state(state: AttemptState | None, event_type: str) -> AttemptState | None:
    """Where the machine lands, or ``None`` if the step is not legal from ``state``.

    Non-transitions leave the state alone — a heartbeat that reset the tracked state to
    `None` would make every witness after it unknowable."""
    if event_type in NON_TRANSITION_EVENTS:
        return state
    transition = next((t for t in TRANSITIONS if t.event == event_type
                       and (state in t.from_states if state is not None
                            else not t.from_states)), None)
    return None if transition is None else transition.to_state


def build_history(event_types: Sequence[str], *, sequential: bool = False) -> list[Event]:
    """A history of ``event_types``, each carrying whatever its source state obliges it to.

    The ONE state-tracking builder: `drive`, the random walks, and the test module's
    `_history` all route through it, so a future witnessed field is satisfied everywhere at
    once instead of in whichever builder someone remembers."""
    events: list[Event] = []
    state: AttemptState | None = None
    for position, event_type in enumerate(event_types):
        payload: dict[str, Any] = dict(witness_payload(state, event_type))
        if event_type == "ClaimHeartbeat":
            payload["tick"] = position
        events.append(attempt_event(event_type, payload=payload,
                                    seq=position if sequential else _UNSET))
        state = next_state(state, event_type)
    return events


def _shortest_paths() -> dict[AttemptState, list[str]]:
    """BFS over the declared table. Derived, never hand-written: a hand-written path would
    silently stop testing a transition the table later changes."""
    start = AttemptState.PROPOSED
    paths: dict[AttemptState, list[str]] = {start: ["Proposed"]}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for event in sorted(legal_events_from(state)):
            nxt = next(t.to_state for t in TRANSITIONS
                       if t.event == event and state in t.from_states)
            if nxt not in paths:
                paths[nxt] = paths[state] + [event]
                queue.append(nxt)
    return paths


_PATHS = _shortest_paths()


def drive(state: AttemptState) -> list[Event]:
    """A minimal legal history ending in ``state``."""
    if state not in _PATHS:
        raise AssertionError(f"{state} is unreachable from PROPOSED — the table is wrong")
    return build_history(_PATHS[state])


_MARKER_EFFECTS = {"†": "ClaimReleased", "◇": "MonitorStarted"}

#: Marks a row that is a real lane transition but does NOT move an Attempt through
#: `TRANSITIONS` (Problem-level, coordinator-level, or non-state-changing).
_NOT_AN_ATTEMPT_TRANSITION = "‡"

#: Effect ORDER is fixed by the coordinator fold, not by the order markers happen to appear
#: in the spec cell: MonitorStarted must precede ClaimReleased or the release has no owner
#: to check against. Declaring it once here keeps the spec free of an ordering it should
#: not have to encode.
_EFFECT_ORDER = ("MonitorStarted", "ClaimReleased")

#: Anchored on THIS FILE, deliberately not on `llmxive.config.repo_root()`: that resolver
#: honours `LLMXIVE_REPO_ROOT`, which hermetic runs point at a synthetic DATA root with no
#: `specs/` in it. The spec being compared here is a source artifact of the same checkout as
#: the code, so the test tree's own location is the only anchor that cannot be redirected
#: out from under it — and a relative path would depend on the working directory instead.
_SPEC = Path(__file__).resolve().parents[2] / "specs/025-self-improvement-lane/spec.md"

#: `(from_states, to_state, (key_suffix, key_fields), coordinator_effects)`. The key is a
#: PAIR because the spec states a tuple: comparing only the suffix is how a code table that
#: had dropped `head_sha` and `reason` from its derived ids matched the spec exactly.
SpecRow = tuple[frozenset[str], str, tuple[str, tuple[str, ...]], tuple[str, ...]]


def parse_spec_transitions() -> tuple[dict[str, SpecRow], frozenset[str], frozenset[str]]:
    """Parse spec 025's Attempt transition table into rows comparable with `TRANSITIONS`,
    the set of Attempt-scoped rows that are NOT transitions, and EVERY `‡` row's event name.

    The spec's six columns are `From | Event | To | Idempotency key | Side effect |
    Reconciliation`; the effect markers live in the Event cell (`†` release, `◇` monitor,
    `‡` not an Attempt transition). Only the four machine-checkable fields come back — the
    last two columns are prose by design and comparing them would make the test a diff.

    The second return is needed because the spec's `‡` rows split two ways: some are
    problem- or coordinator-scoped and never touch an Attempt's stream, and some (keyed by
    `attempt_id`) do. Only the second kind must appear in `NON_TRANSITION_EVENTS`.

    The THIRD return exists because excluding `‡` rows from the row comparison silently
    excluded their VOCABULARY too, and two rows drifted in that blind spot: the spec named
    an `OperationalCooldown` and a `PromotionReenabled` that no writer produces. A `‡` row
    is not an Attempt transition, but it still names a record something must write, so the
    names remain checkable against `KNOWN_EVENT_TYPES_V1` even when the columns are not.

    A row that does not parse is an ERROR, never a skip. Silently dropping unparseable rows
    is how a drift test ends up comparing an empty set with an empty set and passing."""
    rows: dict[str, SpecRow] = {}
    non_transitions: set[str] = set()
    lane_events: set[str] = set()
    inside = False
    for line in _SPEC.read_text().split("\n"):
        stripped = line.strip()
        if stripped.startswith("|") and "Idempotency key" in stripped:
            inside = True
            continue
        if not inside:
            continue
        if not stripped.startswith("|"):
            break
        if set(stripped) <= set("|- "):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) != 6:
            raise AssertionError(
                f"spec transition row has {len(cells)} cells, expected 6: {stripped!r}")
        froms, event_cell, to, key_cell, _side, _recon = cells
        if _NOT_AN_ATTEMPT_TRANSITION in event_cell:
            lane_events.add(_event_name(event_cell))
            # Not a transition — but if it is keyed by `attempt_id` it still LANDS on an
            # Attempt's stream, and `project_attempt` folds every event it finds there.
            # Collecting these is what lets the parity test prove `NON_TRANSITION_EVENTS`
            # is complete instead of remembered; forgetting one makes every projection of
            # that Attempt fail closed the moment the event is first written.
            if "attempt_id" in key_cell:
                non_transitions.add(_event_name(event_cell))
            continue
        effects = tuple(
            name for name in _EFFECT_ORDER
            if name in {_MARKER_EFFECTS[m] for m in event_cell if m in _MARKER_EFFECTS})
        event = _event_name(event_cell)
        if not event.isidentifier():
            raise AssertionError(f"unparseable Event cell: {event_cell!r}")
        from_states = frozenset() if _clean(froms) == "∅" else frozenset(
            _clean(f) for f in froms.split("/"))
        rows[event] = (from_states, _clean(to), _parse_key(key_cell), effects)
    if not rows:
        raise AssertionError(f"no transition rows parsed from {_SPEC} — the test is vacuous")
    if not lane_events:
        raise AssertionError(f"no ‡ rows parsed from {_SPEC} — the test is vacuous")
    return rows, frozenset(non_transitions), frozenset(lane_events)


def _parse_key(cell: str) -> tuple[str, tuple[str, ...]]:
    """`` `(attempt_id,"promo-obs",head_sha)` `` → `("promo-obs", ("head_sha",))`.

    The WHOLE declaration, not just the suffix. The previous parser stopped at the first
    quoted literal and discarded the rest as "values, not declarations" — but the field
    NAMES are exactly a declaration (which payload fields complete the key), and dropping
    them made the test bless a code table that derived its ids without them.

    Every row is `(attempt_id, "suffix", field*)`: `attempt_id` is implicit in the
    per-Attempt derivation, so it is required and then dropped. Anything else is a spec typo
    rather than a shape this parser should quietly accommodate."""
    parts = [p.strip() for p in _clean(cell).strip("()").split(",")]
    if len(parts) < 2 or parts[0] != "attempt_id":
        raise AssertionError(f"idempotency key is not attempt-scoped: {cell!r}")
    if not (parts[1].startswith('"') and parts[1].endswith('"') and len(parts[1]) > 2):
        raise AssertionError(f"no quoted idempotency suffix in: {cell!r}")
    for field in parts[2:]:
        if not field.isidentifier():
            raise AssertionError(f"idempotency key names a non-field {field!r}: {cell!r}")
    return parts[1].strip('"'), tuple(parts[2:])


def _clean(cell: str) -> str:
    """Strip markdown emphasis, code ticks, and the effect markers."""
    out = cell
    for junk in ("`", "*", *_MARKER_EFFECTS, _NOT_AN_ATTEMPT_TRANSITION):
        out = out.replace(junk, "")
    return out.strip()


def _event_name(cell: str) -> str:
    """`_clean`, plus a trailing parenthetical GLOSS — `PromotionEnabledSet (manual
    re-enable)`. The gloss says when the row applies; the event name is what the code must
    have. Scoped to the Event column deliberately: a `‡` row's From cell is a prose
    CONDITION that may itself be parenthesised, and stripping there would erase it."""
    return re.sub(r"\s*\([^)]*\)", "", _clean(cell)).strip()
