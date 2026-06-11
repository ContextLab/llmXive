"""Regression (spec 023 defect #15, observed live on PROJ-552): the
deterministic planning strip BARE-DELETED empirical tokens, leaving broken
prose ("≥95% of records have…" → "of records have…") that review panels
correctly flagged forever — and it also deleted VERIFIED values (9988 with
its OEIS source cited inline), mutilating even the plan's own correction
note. Values now defer to the sanctioned ``[deferred]`` marker and
verified-facts values are exempt."""

from __future__ import annotations

from pathlib import Path

from llmxive.claims.planning_scan import (
    DEFERRED_MARKER,
    strip_empirical_values,
)


def test_deferral_is_grammatical_not_a_deletion() -> None:
    line = "**Then** approximately 95% of records have crossing number values present"
    out = strip_empirical_values(line)
    assert out == f"**Then** {DEFERRED_MARKER} of records have crossing number values present"


def test_bound_led_targets_survive() -> None:
    """Spec 023 defect #16: design targets are requirements, not claims."""
    line = "**Then** ≥95% of records have values; power is at least 80%; done within 60 minutes"
    assert strip_empirical_values(line) == line


def test_verified_values_are_exempt() -> None:
    line = (
        "OEIS A002863 shows 9,988 prime knots at crossing number 13; "
        "roughly 90% of records are usable."
    )
    out = strip_empirical_values(line, exempt=("9988",))
    assert "9,988 prime knots" in out, "verified value (with source) must survive"
    assert "roughly 90%" not in out
    assert DEFERRED_MARKER in out


def test_idempotent_with_markers() -> None:
    line = f"Validate {DEFERRED_MARKER} of knots, approximately 2,000 records."
    once = strip_empirical_values(line)
    assert once == strip_empirical_values(once)
    assert once.count(DEFERRED_MARKER) == 2


def test_live_proj552_correction_note_survives_with_exemption() -> None:
    """The exact mutilation observed: plan.md's critical note about the
    spec's factual error had ITS OWN numbers stripped, becoming
    self-referentially meaningless."""
    note = (
        "spec.md states 49 prime knots at crossing number 13 but OEIS "
        "A002863 shows 9,988 prime knots (source: https://oeis.org/A002863)."
    )
    out = strip_empirical_values(note, exempt=("9988", "49"))
    assert "49 prime knots" in out and "9,988 prime knots" in out


def test_service_passes_verified_facts_exemption(tmp_path: Path) -> None:
    """End-to-end through the service planning path: a verified_facts.yaml
    value survives the guarantee pass; an unverified one defers."""
    import yaml

    from llmxive.claims import service

    pid = "PROJ-941-strip"
    mem = tmp_path / "projects" / pid / ".specify" / "memory"
    mem.mkdir(parents=True)
    (mem / "verified_facts.yaml").write_text(
        yaml.safe_dump(
            {
                "13|crossing knot prime": {
                    "value": "9988",
                    "source_id": "A002863",
                    "url": "https://oeis.org/A002863",
                    "quote": "13 9988",
                }
            }
        ),
        encoding="utf-8",
    )

    class _NoBackend:
        def chat(self, *a, **kw):
            raise RuntimeError("offline test — extractor falls back to no-op")

    text = (
        "The dataset holds 9,988 prime knots (OEIS A002863) and roughly 95% "
        "of records carry all invariants."
    )
    smoothed, claims, report = service._process_planning_document(
        text,
        artifact_path=f"projects/{pid}/specs/001-x/plan.md",
        project_id=pid,
        backend=_NoBackend(),
        model=None,
        repo_root=tmp_path,
        stage_label="plan",
    )
    assert "9,988 prime knots" in smoothed
    assert "roughly 95%" not in smoothed
    assert DEFERRED_MARKER in smoothed
