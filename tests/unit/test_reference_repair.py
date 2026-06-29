"""Unit tests for autonomous dead-reference repair (user requirement).

Covers:
- :func:`llmxive.speckit._research_guard.find_unreachable_references` — returns
  ALL dead refs (not just the first), reusing the same probe as the hard gate.
- :func:`llmxive.speckit._reference_repair.repair_research_references` — swaps a
  dead URL for a librarian-verified replacement (logged, never silent), and
  leaves a URL unresolved when the librarian finds nothing.

Dead URLs use RFC 2606 reserved hosts (``*.invalid``) so the reachability probe
fails deterministically (DNS NXDOMAIN) with NO network flakiness; the "good" URL
is ``https://example.com`` (RFC 2606 reserved, always reachable). The librarian
search is monkeypatched so the repair test never hits the network.
"""

from __future__ import annotations

import json

import pytest

from llmxive.speckit import _reference_repair
from llmxive.speckit._research_guard import find_unreachable_references

# RFC 2606 reserved hosts: ``.invalid`` never resolves (deterministic DNS fail);
# ``example.com`` is always reachable. No network flakiness either way.
GOOD_URL = "https://example.com"
DEAD_URL_1 = "https://nonexistent-host-aaa.invalid/datasets/foo/train.csv"
DEAD_URL_2 = "https://nonexistent-host-bbb.invalid/datasets/bar/test.csv"


def _research_md() -> str:
    # Each dataset reference on its OWN line (realistic for a research.md
    # references list) so per-reference intent derivation isn't cross-
    # contaminated by a sibling reference on the same line.
    return (
        "# Research\n\n"
        f"We use the [Foo dataset]({DEAD_URL_1}).\n"
        f"We also use the [Bar dataset]({DEAD_URL_2}).\n\n"
        f"Reference implementation: {GOOD_URL}\n"
    )


_NOTE_HEADER = "Reference repairs (autonomous, FR-006)"


def _body_and_note(research: str) -> tuple[str, str]:
    """Split repaired research.md into (body-before-note, note)."""
    if _NOTE_HEADER in research:
        idx = research.index("##")
        # The note header line is the LAST '##' section we appended.
        note_start = research.rindex(_NOTE_HEADER)
        # Back up to the start of that markdown heading line.
        body_cut = research.rindex("\n##", 0, note_start) if "\n##" in research[:note_start] else idx
        return research[:body_cut], research[body_cut:]
    return research, ""


# ---------------------------------------------------------------------------
# find_unreachable_references
# ---------------------------------------------------------------------------


def test_find_unreachable_returns_all_dead_not_just_first() -> None:
    dead = find_unreachable_references(_research_md(), timeout=5)
    dead_urls = {u for u, _reason in dead}
    assert DEAD_URL_1 in dead_urls
    assert DEAD_URL_2 in dead_urls
    # The good URL must NOT be reported dead.
    assert GOOD_URL not in dead_urls
    # Both dead refs returned (not the first-fail short-circuit of the hard gate).
    assert len(dead) == 2
    # Every entry carries a (url, reason) pair.
    for url, reason in dead:
        assert isinstance(url, str) and url
        assert isinstance(reason, str) and reason


def test_find_unreachable_empty_when_all_good() -> None:
    assert find_unreachable_references(f"All good: {GOOD_URL}\n", timeout=5) == []
    assert find_unreachable_references("", timeout=5) == []


# ---------------------------------------------------------------------------
# repair_research_references
# ---------------------------------------------------------------------------


@pytest.fixture
def project_dir(tmp_path):
    pdir = tmp_path / "projects" / "PROJ-999-test-repair"
    pdir.mkdir(parents=True)
    return pdir


def test_repair_swaps_dead_url_for_verified_replacement(monkeypatch, tmp_path, project_dir) -> None:
    """A dead URL whose intent the librarian resolves is swapped + logged."""
    repo_root = tmp_path

    # Monkeypatch the librarian's verified-URL source to return a known-GOOD
    # replacement for the FIRST dead ref's intent and nothing reachable for the
    # second — so we exercise BOTH the swap and the unresolved path in one run.
    def fake_resolve_datasets(intent, *, project_dir, repo_root, budget_s=300):
        from llmxive.librarian.dataset_resolver import ResolvedDatasets, ResolvedIntent

        # "Foo" intent -> a verified replacement; "Bar" (and all else) ->
        # unresolved. Each ref is on its own line so the intents don't collide.
        if "foo" in intent.lower():
            return ResolvedDatasets(datasets=[
                ResolvedIntent(
                    intent=intent, status="verified",
                    candidates=[{"url": GOOD_URL, "source": "huggingface", "format": "csv"}],
                )
            ])
        return ResolvedDatasets(datasets=[
            ResolvedIntent(intent=intent, status="unresolved", candidates=[])
        ])

    monkeypatch.setattr(
        "llmxive.librarian.dataset_resolver.resolve_datasets", fake_resolve_datasets
    )

    files = {"research.md": _research_md()}
    updated, unresolved = _reference_repair.repair_research_references(
        files, project_dir=project_dir, repo_root=repo_root
    )

    research = updated["research.md"]
    body, note = _body_and_note(research)
    # The dead Foo URL is gone from the BODY, replaced by the verified GOOD_URL.
    assert DEAD_URL_1 not in body
    assert GOOD_URL in body
    # The Bar URL had no reachable replacement -> still present + unresolved.
    assert DEAD_URL_2 in body
    assert unresolved == [DEAD_URL_2]

    # The swap is auditable: an appended note in research.md records the dead
    # URL verbatim (never silent) ...
    assert _NOTE_HEADER in note
    assert DEAD_URL_1 in note
    assert GOOD_URL in note
    # ... and a state/reference_repairs/<project>.json log.
    log_path = repo_root / "state" / "reference_repairs" / f"{project_dir.name}.json"
    assert log_path.exists()
    log = json.loads(log_path.read_text())
    swaps = [r for entry in log for r in entry["repairs"]]
    assert any(
        r["dead_url"] == DEAD_URL_1 and r["replacement_url"] == GOOD_URL for r in swaps
    )

    # The input dict is not mutated (a NEW dict is returned).
    assert files["research.md"] == _research_md()


def test_repair_leaves_url_unresolved_when_search_finds_nothing(
    monkeypatch, tmp_path, project_dir
) -> None:
    """When the librarian finds no replacement, the URL is unchanged + unresolved."""
    repo_root = tmp_path

    def fake_resolve_nothing(intent, *, project_dir, repo_root, budget_s=300):
        from llmxive.librarian.dataset_resolver import ResolvedDatasets

        return ResolvedDatasets(datasets=[])

    monkeypatch.setattr(
        "llmxive.librarian.dataset_resolver.resolve_datasets", fake_resolve_nothing
    )

    files = {"research.md": _research_md()}
    updated, unresolved = _reference_repair.repair_research_references(
        files, project_dir=project_dir, repo_root=repo_root
    )

    # Nothing changed: both dead URLs unresolved, research.md untouched, no note.
    assert updated["research.md"] == _research_md()
    assert set(unresolved) == {DEAD_URL_1, DEAD_URL_2}
    assert "Reference repairs (autonomous, FR-006)" not in updated["research.md"]
    # No log written when no repair happened.
    log_path = repo_root / "state" / "reference_repairs" / f"{project_dir.name}.json"
    assert not log_path.exists()


def test_repair_rejects_unreachable_replacement(monkeypatch, tmp_path, project_dir) -> None:
    """A candidate URL that does NOT pass the reachability probe is never used.

    Guards the Constitution-II invariant: never swap one dead URL for another.
    """
    repo_root = tmp_path

    def fake_resolve_dead_candidate(intent, *, project_dir, repo_root, budget_s=300):
        from llmxive.librarian.dataset_resolver import ResolvedDatasets, ResolvedIntent

        # "verified" by the resolver, but the URL is itself a dead .invalid host:
        # the repair must RE-PROBE and reject it.
        return ResolvedDatasets(datasets=[
            ResolvedIntent(
                intent=intent, status="verified",
                candidates=[{"url": "https://still-dead.invalid/x.csv", "source": "hf", "format": "csv"}],
            )
        ])

    monkeypatch.setattr(
        "llmxive.librarian.dataset_resolver.resolve_datasets", fake_resolve_dead_candidate
    )

    files = {"research.md": _research_md()}
    updated, unresolved = _reference_repair.repair_research_references(
        files, project_dir=project_dir, repo_root=repo_root
    )

    # The unreachable replacement was rejected -> both dead URLs unresolved.
    assert set(unresolved) == {DEAD_URL_1, DEAD_URL_2}
    assert "still-dead.invalid" not in updated["research.md"]
    assert updated["research.md"] == _research_md()


def test_repair_noop_when_no_research_md(tmp_path, project_dir) -> None:
    files = {"plan.md": "# Plan\n"}
    updated, unresolved = _reference_repair.repair_research_references(
        files, project_dir=project_dir, repo_root=tmp_path
    )
    assert updated is files
    assert unresolved == []


def test_repair_degrades_to_unresolved_on_search_exception(
    monkeypatch, tmp_path, project_dir
) -> None:
    """A librarian/search crash must NOT propagate — it degrades to unresolved."""
    repo_root = tmp_path

    def boom(intent, *, project_dir, repo_root, budget_s=300):
        raise RuntimeError("network exploded")

    monkeypatch.setattr(
        "llmxive.librarian.dataset_resolver.resolve_datasets", boom
    )

    files = {"research.md": _research_md()}
    updated, unresolved = _reference_repair.repair_research_references(
        files, project_dir=project_dir, repo_root=repo_root
    )
    # No crash; dead URLs fall through to the gate.
    assert set(unresolved) == {DEAD_URL_1, DEAD_URL_2}
    assert updated["research.md"] == _research_md()
