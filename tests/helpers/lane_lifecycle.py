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
    body.update(payload or {})
    return Event(
        event_id=derive_event_id(problem_id, f"{event_type}\x00{attempt_id}"),
        event_type=event_type, problem_id=problem_id, actor="test",
        payload=body, timestamp=TS, attempt_id=attempt_id,
        seq=next(_SEQ) if seq is _UNSET else seq,
    )


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

SpecRow = tuple[frozenset[str], str, str, tuple[str, ...]]


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
        # `(attempt_id,"promo-obs",head_sha)` → `promo-obs`: the suffix is the only part
        # `TRANSITIONS` carries, because the other elements are values, not declarations.
        key = re.search(r'"([^"]+)"', key_cell)
        if key is None:
            raise AssertionError(f"no quoted idempotency suffix in: {key_cell!r}")
        from_states = frozenset() if _clean(froms) == "∅" else frozenset(
            _clean(f) for f in froms.split("/"))
        rows[event] = (from_states, _clean(to), key.group(1), effects)
    if not rows:
        raise AssertionError(f"no transition rows parsed from {_SPEC} — the test is vacuous")
    if not lane_events:
        raise AssertionError(f"no ‡ rows parsed from {_SPEC} — the test is vacuous")
    return rows, frozenset(non_transitions), frozenset(lane_events)


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
