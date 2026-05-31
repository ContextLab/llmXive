"""T022 — integration test: F-14 kickback repoint for unresolved-claim kickbacks.

Asserts that:
1. An unresolved-claim kickback (``unresolved_claim=True`` in sentinel) routes
   to the resolver stage (escalate=False) for up to CLAIM_RETRY_BUDGET extra
   automated retries BEYOND the normal CONVERGENCE_KICKBACK_CAP.
2. Human escalation (escalate=True) only fires AFTER the combined budget
   (CONVERGENCE_KICKBACK_CAP + CLAIM_RETRY_BUDGET) is exhausted.
3. Non-claim kickbacks are NOT affected: they still escalate after
   CONVERGENCE_KICKBACK_CAP (old behavior preserved).

Real filesystem (tmp_path), no mocks.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from llmxive.pipeline._kickback import (
    CLAIM_RETRY_BUDGET,
    CONVERGENCE_KICKBACK_CAP,
    consume_convergence_kickback,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_sentinel(
    memory_dir: Path,
    *,
    to_stage: str,
    stage: str = "spec",
    unresolved_claim: bool = False,
) -> None:
    memory_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "to_stage": to_stage,
        "worst_severity": "science",
        "reason": "unresolved external claim" if unresolved_claim else "did not converge",
        "stage": stage,
        "unresolved_concerns": [],
        "artifact_links": [],
    }
    if unresolved_claim:
        payload["unresolved_claim"] = True
    (memory_dir / "convergence_kickback.yaml").write_text(
        yaml.safe_dump(payload), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Non-claim kickbacks: old cap→human behaviour unchanged
# ---------------------------------------------------------------------------


class TestNonClaimKickbacks:
    """CONVERGENCE_KICKBACK_CAP is still the escalation threshold for plain kicks."""

    def test_routes_within_cap(self, tmp_path: Path) -> None:
        decisions = []
        for _ in range(CONVERGENCE_KICKBACK_CAP):
            _write_sentinel(tmp_path, to_stage="flesh_out_in_progress", stage="spec")
            decisions.append(consume_convergence_kickback(tmp_path))
        assert all(d is not None and d.escalate is False for d in decisions)

    def test_escalates_at_cap_plus_one(self, tmp_path: Path) -> None:
        for _ in range(CONVERGENCE_KICKBACK_CAP):
            _write_sentinel(tmp_path, to_stage="flesh_out_in_progress", stage="spec")
            consume_convergence_kickback(tmp_path)
        # This push exceeds the cap
        _write_sentinel(tmp_path, to_stage="flesh_out_in_progress", stage="spec")
        last = consume_convergence_kickback(tmp_path)
        assert last is not None
        assert last.escalate is True
        assert last.to_stage is None
        assert last.count == CONVERGENCE_KICKBACK_CAP + 1


# ---------------------------------------------------------------------------
# Claim kickbacks: CLAIM_RETRY_BUDGET extra automated retries before human
# ---------------------------------------------------------------------------


class TestClaimKickbacks:
    """Unresolved-claim kickbacks stay automated for an extra CLAIM_RETRY_BUDGET rounds."""

    def test_claim_kickbacks_stay_automated_through_combined_budget(
        self, tmp_path: Path
    ) -> None:
        """All CONVERGENCE_KICKBACK_CAP + CLAIM_RETRY_BUDGET kicks are escalate=False."""
        combined = CONVERGENCE_KICKBACK_CAP + CLAIM_RETRY_BUDGET
        decisions = []
        for _ in range(combined):
            _write_sentinel(
                tmp_path,
                to_stage="flesh_out_in_progress",
                stage="spec",
                unresolved_claim=True,
            )
            decisions.append(consume_convergence_kickback(tmp_path))

        assert all(d is not None for d in decisions)
        assert all(d.escalate is False for d in decisions), (
            f"Expected no escalation within budget={combined}; "
            f"got escalations at indices: {[i for i,d in enumerate(decisions) if d.escalate]}"
        )

    def test_claim_kickback_escalates_after_combined_budget(
        self, tmp_path: Path
    ) -> None:
        """The kick that exceeds CONVERGENCE_KICKBACK_CAP+CLAIM_RETRY_BUDGET escalates."""
        combined = CONVERGENCE_KICKBACK_CAP + CLAIM_RETRY_BUDGET
        for _ in range(combined):
            _write_sentinel(
                tmp_path,
                to_stage="flesh_out_in_progress",
                stage="spec",
                unresolved_claim=True,
            )
            consume_convergence_kickback(tmp_path)

        # This one exceeds the combined budget
        _write_sentinel(
            tmp_path,
            to_stage="flesh_out_in_progress",
            stage="spec",
            unresolved_claim=True,
        )
        last = consume_convergence_kickback(tmp_path)
        assert last is not None
        assert last.escalate is True
        assert last.count == combined + 1

    def test_claim_budget_greater_than_plain_cap(self) -> None:
        """Sanity: the claim combined budget is strictly larger than the plain cap."""
        assert CLAIM_RETRY_BUDGET > 0
        assert CONVERGENCE_KICKBACK_CAP + CLAIM_RETRY_BUDGET > CONVERGENCE_KICKBACK_CAP

    def test_claim_kickback_routes_to_specified_stage(self, tmp_path: Path) -> None:
        """The resolver stage in to_stage is used verbatim (not overridden)."""
        _write_sentinel(
            tmp_path,
            to_stage="flesh_out_in_progress",
            stage="spec",
            unresolved_claim=True,
        )
        d = consume_convergence_kickback(tmp_path)
        assert d is not None
        assert d.escalate is False
        assert d.to_stage == "flesh_out_in_progress"

    def test_plain_kickback_does_not_get_extra_budget(self, tmp_path: Path) -> None:
        """A sentinel without unresolved_claim=True does NOT get the extra budget."""
        # Exhaust the plain cap
        for _ in range(CONVERGENCE_KICKBACK_CAP):
            _write_sentinel(tmp_path, to_stage="flesh_out_in_progress", stage="spec")
            consume_convergence_kickback(tmp_path)
        # Next kick (no unresolved_claim flag) must escalate
        _write_sentinel(tmp_path, to_stage="flesh_out_in_progress", stage="spec")
        last = consume_convergence_kickback(tmp_path)
        assert last is not None
        assert last.escalate is True


# ---------------------------------------------------------------------------
# graph._decide_next_stage: claim kickback stays automated through combined budget
# ---------------------------------------------------------------------------


class TestDecideNextStageClaimKickback:
    """_decide_next_stage routes claim kickbacks for the full combined budget."""

    def _spec_project(self):
        from datetime import UTC, datetime

        from llmxive.types import Project, Stage

        now = datetime.now(UTC)
        return Project(
            id="PROJ-022-claim-kb",
            title="Claim kickback test",
            field="mathematics",
            current_stage=Stage.SPECIFIED,
            created_at=now,
            updated_at=now,
            speckit_research_dir="specs/001-x",
        )

    def test_decide_claim_kickback_no_human_within_budget(self, tmp_path: Path) -> None:
        from llmxive.pipeline.graph import _decide_next_stage
        from llmxive.types import Stage

        project = self._spec_project()
        project_dir = tmp_path / "projects" / project.id
        mem = project_dir / ".specify" / "memory"
        combined = CONVERGENCE_KICKBACK_CAP + CLAIM_RETRY_BUDGET

        stages = []
        for _ in range(combined):
            _write_sentinel(
                mem,
                to_stage="flesh_out_in_progress",
                stage="spec",
                unresolved_claim=True,
            )
            stages.append(_decide_next_stage(project, project_dir, repo_root=tmp_path))

        # All within the combined budget should route to the resolver, not human
        assert all(s == Stage.FLESH_OUT_IN_PROGRESS for s in stages), (
            f"Expected all FLESH_OUT_IN_PROGRESS, got: {stages}"
        )

    def test_decide_claim_kickback_escalates_after_combined_budget(
        self, tmp_path: Path
    ) -> None:
        from llmxive.pipeline.graph import _decide_next_stage
        from llmxive.types import Stage

        project = self._spec_project()
        project_dir = tmp_path / "projects" / project.id
        mem = project_dir / ".specify" / "memory"
        combined = CONVERGENCE_KICKBACK_CAP + CLAIM_RETRY_BUDGET

        for _ in range(combined):
            _write_sentinel(
                mem,
                to_stage="flesh_out_in_progress",
                stage="spec",
                unresolved_claim=True,
            )
            _decide_next_stage(project, project_dir, repo_root=tmp_path)

        # One more exceeds the budget
        _write_sentinel(
            mem,
            to_stage="flesh_out_in_progress",
            stage="spec",
            unresolved_claim=True,
        )
        last_stage = _decide_next_stage(project, project_dir, repo_root=tmp_path)
        assert last_stage == Stage.HUMAN_INPUT_NEEDED


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
