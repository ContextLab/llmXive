"""Two-tier convergence for the doc-authoring tasks gate (Constitution 1.2.0).

The `/speckit.analyze` step is an LLM critic that almost never emits a literal
``CLEAN`` (it reliably finds some minor nit), so gating tasks-stage convergence
on ``is_clean`` alone stalled EVERY project at the tasks gate forever. The
tasks gate now advances on writing-level residue (MEDIUM/LOW findings) while a
CRITICAL/HIGH cross-artifact issue always kicks back — mirroring the convergence
engine's two-tier bar. The strict zero-concern gate remains research_review.

Cases use the real analyze-report shape observed on PROJ-492
(`(severity: CRITICAL|HIGH|MEDIUM|LOW) (file:section) summary`).
"""

from __future__ import annotations

from llmxive.speckit.analyze_cmd import analyze_advance_ok, is_clean


def test_clean_report_advances():
    assert analyze_advance_ok("CLEAN")
    assert analyze_advance_ok("CLEAN\n")
    assert is_clean("CLEAN")


def test_critical_or_high_kicks_back():
    # Real PROJ-492 findings — must NOT advance (genuine requirement defects).
    crit = "- (severity: CRITICAL) (file:tasks.md:Phase 7) T070 tests the wrong component"
    high = "- (severity: HIGH) (file:tasks.md:T044) logistic-regression is scope creep vs FR-027"
    assert not analyze_advance_ok(crit)
    assert not analyze_advance_ok(high)
    assert not analyze_advance_ok(crit + "\n" + high)
    # A CRITICAL anywhere in a multi-finding report still blocks.
    mixed = (
        "- (severity: MEDIUM) (file:plan.md) Bonferroni added\n"
        "- (severity: CRITICAL) (file:tasks.md) deferred threshold left undefined\n"
        "- (severity: LOW) (file:tasks.md) wording nit"
    )
    assert not analyze_advance_ok(mixed)


def test_medium_low_only_residue_advances():
    """Writing-level residue (only MEDIUM/LOW) lets the doc stage advance — the
    later research_review still strictly catches anything real."""
    residue = (
        "- (severity: MEDIUM) (file:plan.md:Phase 3) Bonferroni correction added for FR-005b\n"
        "- (severity: LOW) (file:tasks.md:T012) task description could be tightened"
    )
    assert analyze_advance_ok(residue)
    assert analyze_advance_ok("- (severity: LOW) (file:tasks.md) minor wording in T007")


def test_malformed_noncllean_report_kicks_back():
    """A non-CLEAN report with NO parseable `severity:` bullet is malformed —
    kick back rather than advance on an uninterpretable critique."""
    assert not analyze_advance_ok("The tasks mostly look fine but tighten things up.")
    assert not analyze_advance_ok("")
