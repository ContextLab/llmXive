"""The lost-acknowledgement contract, parameterized over the cross-stream matrix.

A durable transaction whose caller never learned it landed is indistinguishable, to that
caller, from one that never ran. So the recovery path is the ordinary retry, and the retry
must report "already yours" rather than raising or claiming fresh work.

ONE test body over every matrix row, not a per-row test written where each row was
implemented: row 1 had all of this and rows 2/3/4 had none, and that asymmetry is exactly
how the replay defect survived. Task 7 lands rows 2 and 4; Task 8 adds row 1 and Task 10
row 3 to `_ROWS` rather than re-implementing the body.

Real git repositories throughout — no mocks.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from llmxive.self_improvement.coordinator import project_coordinator
from llmxive.self_improvement.events import (
    COORDINATOR_STREAM,
    coordinator_event_id,
    event_to_json,
)

# The store's own stamping and canonical form, reused rather than re-stated: these tests
# forge records that are byte-identical to stored ones except for the ONE thing under test,
# and a second definition of "what a stored record looks like" would make a damage case
# pass or fail for reasons unrelated to the damage.
from llmxive.self_improvement.lane_log import (
    LANE_REF,
    LaneLogConfig,
    _finalize,
    _to_json,
    bootstrap_lane_log,
    read,
)
from llmxive.self_improvement.lifecycle import cas_attempt_transition
from llmxive.self_improvement.pairing import LaneInconsistent
from tests.helpers.lane_lifecycle import Clock, seed_claim

_EVENT_DIR = "self-improvement/events"


def _git(repo, *a, **kw) -> str:
    return subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True,
                          text=True, **kw).stdout.strip()


@pytest.fixture
def bare_remote(tmp_path):
    r = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(r)], check=True)
    return r


@pytest.fixture
def clone(tmp_path, bare_remote):
    """A clone whose lane ref lives on the remote — the ONLY configuration in which a lost
    acknowledgement is possible, because there the PUSH is the commit point and
    `_after_push` fires between "durable on the remote" and "local ref moved"."""
    dst = tmp_path / "c"
    subprocess.run(["git", "clone", "-q", str(bare_remote), str(dst)], check=True)
    _git(dst, "config", "user.email", "t@t")
    _git(dst, "config", "user.name", "t")
    bootstrap_lane_log(dst, config=LaneLogConfig(remote="origin"))
    return dst


@pytest.fixture
def repo(tmp_path):
    """Local-only. The damage cases must NOT use the clone: `read` force-fetches the
    authoritative ref, which would restore every blob these tests corrupt."""
    r = tmp_path / "local"
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    bootstrap_lane_log(r, config=LaneLogConfig())
    return r


REMOTE = LaneLogConfig(remote="origin")
LOCAL = LaneLogConfig()


def _apply(repo, event_type, *, config, clock, actor="runner-1", payload=None,
           problem_id="P1", attempt_id="A1", **seams):
    return cas_attempt_transition(
        repo, problem_id=problem_id, attempt_id=attempt_id, event_type=event_type,
        payload=payload or {}, actor=actor, clock=clock, config=config, **seams)


# --- the matrix rows ------------------------------------------------------------------

def _row2_prelude(repo, config, clock):
    seed_claim(repo, config=config, clock=clock)
    _apply(repo, "Implementing", config=config, clock=clock)


def _row4_prelude(repo, config, clock):
    _row2_prelude(repo, config, clock)
    _apply(repo, "EvaluationPassed", payload={"head_sha": "a" * 40}, config=config,
           clock=clock)
    _apply(repo, "PromotionRequested", payload={"head_sha": "a" * 40}, config=config,
           clock=clock)


def _claims_the_free_lane(repo, config, clock):
    """After rows 2 and 4 the lane is FREE, so unrelated activity is a second Problem
    taking it — which grows BOTH streams and changes current ownership."""
    seed_claim(repo, problem_id="P2", attempt_id="A2", config=config, clock=clock)


class Row:
    def __init__(self, name, prelude, event_type, payload, partners):
        self.name = name
        self.prelude = prelude
        self.event_type = event_type
        self.payload = payload
        self.partners = partners        # the coordinator halves this row declares

    def invoke(self, repo, config, clock, *, actor="runner-1", **seams):
        return _apply(repo, self.event_type, payload=dict(self.payload), config=config,
                      clock=clock, actor=actor, **seams)


_ROWS = [
    Row("row2-claim-holding-terminal", _row2_prelude, "ImplementationFailed", {},
        ("ClaimReleased",)),
    Row("row4-promotion-observed", _row4_prelude, "PromotionObserved",
        {"head_sha": "a" * 40}, ("MonitorStarted", "ClaimReleased")),
]
_IDS = [r.name for r in _ROWS]


def _snapshot(repo, config, *streams):
    return {s: read(repo, s, config=config) for s in streams}


def _crash_after_push(repo, row, config, clock):
    """Land the row's transaction durably, but leave the caller believing it failed."""
    def _lost_ack():
        raise RuntimeError("acknowledgement lost after the push")

    with pytest.raises(RuntimeError, match="acknowledgement lost"):
        row.invoke(repo, config, clock, _after_push=_lost_ack)


# --- 13: the immediate retry ----------------------------------------------------------

@pytest.mark.parametrize("row", _ROWS, ids=_IDS)
def test_a_retry_after_a_lost_acknowledgement_is_a_no_op(clone, row):
    clock = Clock()
    row.prelude(clone, REMOTE, clock)
    _crash_after_push(clone, row, REMOTE, clock)
    landed = _snapshot(clone, REMOTE, COORDINATOR_STREAM, "P1")

    # A DIFFERENT actor: recovery routinely runs under another runner identity than the one
    # that died, which is precisely why the replay must LOCATE the stored records rather
    # than rebuild them (`actor` is part of an event's append-only identity).
    outcome = row.invoke(clone, REMOTE, clock, actor="runner-2")

    assert outcome.created is False
    assert _snapshot(clone, REMOTE, COORDINATOR_STREAM, "P1") == landed
    for stream, events in landed.items():
        for event in events:
            assert event.actor != "runner-2", f"{stream}: the replay rewrote {event.event_type}"


@pytest.mark.parametrize("row", _ROWS, ids=_IDS)
def test_a_DELAYED_retry_after_the_lane_moved_on_is_still_a_no_op(clone, row):
    """A retry after a crash is usually the NEXT run — minutes and several commits later.
    The immediate case above is the easy half of the contract."""
    clock = Clock()
    row.prelude(clone, REMOTE, clock)
    _crash_after_push(clone, row, REMOTE, clock)
    _claims_the_free_lane(clone, REMOTE, clock)
    moved_on = _snapshot(clone, REMOTE, COORDINATOR_STREAM, "P1", "P2")

    outcome = row.invoke(clone, REMOTE, clock, actor="runner-2")

    assert outcome.created is False
    # (h) The replay's expected revisions are read at the CURRENT tip, so a LONGER stream is
    # not a stale-revision failure. This is the assertion that would fail if a refactor
    # "helpfully" pinned them to the transaction being replayed.
    assert _snapshot(clone, REMOTE, COORDINATOR_STREAM, "P1", "P2") == moved_on
    # (f) and the retry did not renumber history.
    assert [e.seq for e in moved_on["P1"]] == list(range(len(moved_on["P1"])))
    # The projection describes the ATTEMPT, which the later activity did not touch. The
    # historical/current split assertion (g) belongs to the rows that carry OWNERSHIP
    # fields — `ClaimOutcome`, row 1 — and lands with Task 8.
    assert outcome.projection == cas_attempt_transition_projection(clone, REMOTE)
    holder = project_coordinator(moved_on[COORDINATOR_STREAM])
    assert (holder.active_problem_id, holder.active_attempt_id) == ("P2", "A2")


def cas_attempt_transition_projection(repo, config, problem_id="P1", attempt_id="A1"):
    from llmxive.self_improvement.lifecycle import project_attempt
    return project_attempt([e for e in read(repo, problem_id, config=config)
                            if e.attempt_id == attempt_id])


# --- 14: a replay whose stored transaction is not intact ------------------------------

def _paths_in_tip(repo) -> list[str]:
    out = _git(repo, "show", "--name-only", "--format=", LANE_REF)
    return [line for line in out.splitlines() if line.strip()]


def _path(stream, event_id) -> str:
    return f"{_EVENT_DIR}/{stream}/{event_id}.json"


def _commit_blobs(repo, changes: dict[str, str | None], message: str) -> str:
    """Commit blob edits DIRECTLY onto the lane ref, bypassing every lane API.

    The APIs correctly refuse to produce any of these states, which is the point: the
    damage has to be built by hand, or the test would only be checking that a healthy
    write is healthy."""
    index = repo / ".git" / "damage.index"
    env = {"GIT_INDEX_FILE": str(index)}
    tip = _git(repo, "rev-parse", LANE_REF)
    _git(repo, "read-tree", tip, env={**_env(), **env})
    for path, content in changes.items():
        if content is None:
            _git(repo, "update-index", "--force-remove", path, env={**_env(), **env})
        else:
            oid = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=str(repo),
                                 input=content, capture_output=True, text=True,
                                 check=True).stdout.strip()
            _git(repo, "update-index", "--add", "--cacheinfo", f"100644,{oid},{path}",
                 env={**_env(), **env})
    tree = _git(repo, "write-tree", env={**_env(), **env})
    commit = _git(repo, "commit-tree", tree, "-p", tip, "-m", message)
    _git(repo, "update-ref", LANE_REF, commit, tip)
    index.unlink(missing_ok=True)
    return commit


def _env() -> dict[str, str]:
    import os
    return dict(os.environ)


def _stored_raw(repo, stream, event_id) -> dict:
    return json.loads(_git(repo, "show", f"{LANE_REF}:{_path(stream, event_id)}"))


def _rewrite(repo, stream, event_id, **changes) -> None:
    """Replace a stored record's fields IN PLACE — same id, same seq, same anchors."""
    raw = {**_stored_raw(repo, stream, event_id), **changes}
    _commit_blobs(repo, {_path(stream, event_id): _to_json(raw)},
                  f"damage: rewrite {event_id[:8]}")


def _readd_in_a_later_commit(repo, stream, event_id) -> None:
    """Same blob, same content, introduced by a DIFFERENT commit than its partner.

    Everything a presence-or-payload check can see is fine here; only the introducing
    commit differs. This is the regression an "optimization" that splits the transaction
    back into two appends would cause."""
    raw = _stored_raw(repo, stream, event_id)
    _commit_blobs(repo, {_path(stream, event_id): None}, "damage: remove")
    _commit_blobs(repo, {_path(stream, event_id): _to_json(raw)}, "damage: re-add")


def _half_a_transaction(repo, row, clock) -> None:
    """The Attempt half with NO coordinator half — built by hand, because deleting the
    partner from a landed transaction would leave a seq GAP and be refused as corruption on
    read, long before the replay check could see it."""
    from llmxive.self_improvement.events import Event, derive_event_id
    from llmxive.self_improvement.lifecycle import _BY_EVENT

    transition = _BY_EVENT[row.event_type]
    event = Event(
        event_id=derive_event_id("P1", f"{transition.key_suffix}\x00A1"),
        event_type=row.event_type, problem_id="P1", actor="runner-1",
        payload={"problem_id": "P1", "attempt_id": "A1", **row.payload},
        timestamp=clock(), attempt_id="A1",
    )
    raw = _finalize(json.loads(event_to_json(event)), len(read(repo, "P1")))
    _commit_blobs(repo, {_path("P1", event.event_id): _to_json(raw)},
                  "damage: half a transaction")


@pytest.mark.parametrize("row", _ROWS, ids=_IDS)
def test_a_replay_whose_partner_is_MISSING_raises(repo, row):
    """The case the naive replay reports as healthy: the Attempt event is present, so
    "already landed" is true, and nothing ever looks at the half that is gone."""
    clock = Clock()
    row.prelude(repo, LOCAL, clock)
    _half_a_transaction(repo, row, clock)

    with pytest.raises(LaneInconsistent, match="half a transaction"):
        row.invoke(repo, LOCAL, clock)


@pytest.mark.parametrize("row", _ROWS, ids=_IDS)
@pytest.mark.parametrize("partner_index", [0, -1])
def test_a_replay_whose_partner_was_SEPARATELY_COMMITTED_raises(repo, row, partner_index):
    """For row 4 this runs over BOTH partners: a replay that checked only `ClaimReleased`
    would bless a `MonitorStarted` that was not part of the same transaction."""
    clock = Clock()
    row.prelude(repo, LOCAL, clock)
    row.invoke(repo, LOCAL, clock)
    partner = row.partners[partner_index]
    _readd_in_a_later_commit(repo, COORDINATOR_STREAM,
                             coordinator_event_id(partner, "P1", "A1"))

    with pytest.raises(LaneInconsistent, match="one transaction writes both"):
        row.invoke(repo, LOCAL, clock)


@pytest.mark.parametrize("row", _ROWS, ids=_IDS)
def test_a_replay_whose_partner_DISAGREES_on_actor_raises(repo, row):
    """The replay reuses both halves verbatim, so a disagreement here would be carried
    forward as fact."""
    clock = Clock()
    row.prelude(repo, LOCAL, clock)
    row.invoke(repo, LOCAL, clock)
    _rewrite(repo, COORDINATOR_STREAM,
             coordinator_event_id(row.partners[-1], "P1", "A1"), actor="somebody-else")

    with pytest.raises(LaneInconsistent, match="disagree on actor/timestamp"):
        row.invoke(repo, LOCAL, clock)


def test_a_replay_whose_partner_is_the_WRONG_TYPE_at_the_right_id_raises(repo):
    """A record at a derived id can be present and still be the wrong record. The id is a
    hypothesis; what is found there is evidence, not proof.

    Row 4 only: replacing row 2's single partner (`ClaimReleased`) with another type makes
    `project_coordinator` refuse the history first — a different, also-correct fail-closed
    path, but not the one under test here."""
    clock = Clock()
    row = _ROWS[1]
    row.prelude(repo, LOCAL, clock)
    row.invoke(repo, LOCAL, clock)
    monitor_id = coordinator_event_id("MonitorStarted", "P1", "A1")
    raw = _stored_raw(repo, COORDINATOR_STREAM, monitor_id)
    _commit_blobs(repo, {_path(COORDINATOR_STREAM, monitor_id): _to_json(
        {**raw, "event_type": "PromotionEnabledSet",
         "payload": {"promotion_enabled": True}})}, "damage: wrong type")

    with pytest.raises(LaneInconsistent, match="expected MonitorStarted"):
        row.invoke(repo, LOCAL, clock)


def test_a_replay_whose_partner_names_ANOTHER_ATTEMPT_raises(repo):
    """Row 4's `MonitorStarted` again, for the same reason: rewriting a `ClaimReleased`'s
    Attempt makes the coordinator fold reject it as a non-owner before the replay runs."""
    clock = Clock()
    row = _ROWS[1]
    row.prelude(repo, LOCAL, clock)
    row.invoke(repo, LOCAL, clock)
    monitor_id = coordinator_event_id("MonitorStarted", "P1", "A1")
    raw = _stored_raw(repo, COORDINATOR_STREAM, monitor_id)
    _commit_blobs(repo, {_path(COORDINATOR_STREAM, monitor_id): _to_json(
        {**raw, "attempt_id": "A9",
         "payload": {**raw["payload"], "attempt_id": "A9"}})}, "damage: other attempt")

    with pytest.raises(LaneInconsistent, match="names P1/A9 instead"):
        row.invoke(repo, LOCAL, clock)


@pytest.mark.parametrize("prelude, event_type, replacement, required, why", [
    (_row2_prelude, "ImplementationFailed", "PublishFailed", True,
     "a claim-holding terminal: partners are expected"),
    (None, "ReviewAborted", "Rejected", False,
     "a PRE-CLAIM terminal: NO partner exists to cross-check against, so the anchor's own "
     "identity is the only thing between a corrupt record and a replay reported as success"),
])
def test_a_replay_whose_ANCHOR_is_the_wrong_type_raises(repo, prelude, event_type,
                                                        replacement, required, why):
    """Both branches of `required`, because the second is the one a partner-only check
    cannot reach at all. Without the anchor's type check this replays as "already landed"
    and returns a `TransitionOutcome` describing a transition that never happened."""
    clock = Clock()
    payload = {"stage": "proposal", "cause": "wall_clock", "unresolved_dispatches": []} \
        if event_type == "ReviewAborted" else {}
    if prelude is None:
        _apply(repo, "Proposed", config=LOCAL, clock=clock)
    else:
        prelude(repo, LOCAL, clock)
    _apply(repo, event_type, payload=payload, config=LOCAL, clock=clock)

    from llmxive.self_improvement.events import derive_event_id
    from llmxive.self_improvement.lifecycle import _BY_EVENT
    anchor_id = derive_event_id("P1", f"{_BY_EVENT[event_type].key_suffix}\x00A1")
    raw = _stored_raw(repo, "P1", anchor_id)
    _commit_blobs(repo, {_path("P1", anchor_id): _to_json(
        {**raw, "event_type": replacement,
         "payload": {"problem_id": "P1", "attempt_id": "A1"}})}, "damage: anchor type")

    with pytest.raises(LaneInconsistent, match=f"expected {event_type}"):
        _apply(repo, event_type, payload=payload, config=LOCAL, clock=clock)


def test_a_PRE_CLAIM_terminal_that_somehow_has_a_release_raises(repo):
    """Clause 3 of the conditional-effects rule, which the auditor also enforces: a row can
    DECLARE an effect and correctly not have written one. Then the ABSENCE is the
    invariant, and a partner that exists released somebody else's claim.

    Passing the pruned effect list instead of `(declared, required)` would make "correctly
    wrote nothing" and "wrongly holds another Attempt's release" the same input."""
    from llmxive.self_improvement.coordinator import cas_claim
    from llmxive.self_improvement.events import coord_event

    clock = Clock()
    # The lane's coordinator says P1/A1 holds it; P1/A1's own timeline never got a grant, so
    # it is `proposed` and holds NOTHING. That divergence is what makes the forged release
    # foldable — a release naming an Attempt the coordinator does not show as owner is
    # refused by `project_coordinator` long before any replay, which is why this case has to
    # be built from the disagreement rather than from a stray record.
    cas_claim(repo, problem_id="P1", attempt_id="A1", actor="runner-1", timestamp=clock())
    _apply(repo, "Proposed", config=LOCAL, clock=clock)
    payload = {"stage": "proposal", "cause": "wall_clock", "unresolved_dispatches": []}
    _apply(repo, "ReviewAborted", payload=payload, config=LOCAL, clock=clock)
    assert len(_paths_in_tip(repo)) == 1, "the terminal correctly wrote no release"

    forged = coord_event("ClaimReleased", problem_id="P1", attempt_id="A1",
                         payload={"problem_id": "P1", "attempt_id": "A1"},
                         actor="runner-1", timestamp=clock())
    raw = _finalize(json.loads(event_to_json(forged)),
                    len(read(repo, COORDINATOR_STREAM, config=LOCAL)))
    _commit_blobs(repo, {_path(COORDINATOR_STREAM, forged.event_id): _to_json(raw)},
                  "damage: a release nobody was owed")

    with pytest.raises(LaneInconsistent, match="released another Attempt's claim"):
        _apply(repo, "ReviewAborted", payload=payload, config=LOCAL, clock=clock)
