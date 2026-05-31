"""T039 (spec 016, FR-019) — one-time F-18 → unified marker migration."""

from __future__ import annotations

from llmxive.claims.gate import CLAIM_MARKER_PREFIX, has_unresolved_claims
from llmxive.claims.migrate import migrate_unverified_markers
from llmxive.claims.models import ClaimStatus
from llmxive.state import claims as claim_store


def _seed(repo_root, rel, text):
    p = repo_root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def test_migrate_rewrites_marker_and_seeds_registry(tmp_path):
    proj = "PROJ-700-knots"
    doc = _seed(
        tmp_path,
        f"projects/{proj}/spec.md",
        "The count is [UNVERIFIED: 27,635 prime knots — no resolvable source].",
    )

    changed = migrate_unverified_markers(repo_root=tmp_path)

    assert doc in changed
    new_text = doc.read_text(encoding="utf-8")
    assert "[UNVERIFIED:" not in new_text
    assert CLAIM_MARKER_PREFIX in new_text
    assert has_unresolved_claims(new_text)

    # A registry entry was seeded NOT_ENOUGH_INFO so the layer re-resolves it.
    registry = claim_store.load(proj, repo_root=tmp_path)
    assert len(registry) == 1
    assert registry[0].status == ClaimStatus.NOT_ENOUGH_INFO
    assert "27,635" in registry[0].raw_text


def test_migrate_dry_run_changes_nothing(tmp_path):
    proj = "PROJ-701-knots"
    original = "x [UNVERIFIED: arXiv:9999.99 — fake] y"
    doc = _seed(tmp_path, f"projects/{proj}/plan.md", original)

    changed = migrate_unverified_markers(repo_root=tmp_path, dry_run=True)

    assert doc in changed  # reported as would-change
    assert doc.read_text(encoding="utf-8") == original  # but untouched
    assert claim_store.load(proj, repo_root=tmp_path) == []  # no registry writes


def test_migrate_noop_when_no_markers(tmp_path):
    _seed(tmp_path, "projects/PROJ-702-x/spec.md", "A clean document with no markers.")
    assert migrate_unverified_markers(repo_root=tmp_path) == []
