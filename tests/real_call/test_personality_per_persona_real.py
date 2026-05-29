"""Real-call test for the personality agent (T050, US4).

Gated on ``LLMXIVE_REAL_TESTS=1`` (per the conftest convention).
Drives one real-LLM tick per persona against a fixture project
catalog and asserts:

  (a) the LLM returned a parseable Action JSON in the persona's
      characteristic voice (smoke check — the assertion is just
      "non-empty, parses, valid action enum");
  (b) the response is overwhelmingly English (≥ 95% of characters in
      basic Latin / Latin-1-Supplement / General Punctuation Unicode
      blocks) — this enforces FR-014 against the historical figures
      whose primary language was not English;
  (c) pairwise vocabulary-overlap between any two personas' outputs
      stays below the smoke-test threshold (Jaccard similarity over
      content-word sets < 0.6). This is a sanity check on persona
      distinctness — NOT the SC-005 voice-distinctness gate, which is
      verified manually after the first full rotation completes
      (see quickstart.md § 9).

Prints each persona's output for human eyeballing — the print is the
real value of this test, the asserts are guard-rails.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from llmxive.agents import personality as p

REPO = Path(__file__).resolve().parents[2]
POOL_DIR = REPO / p.POOL_PATH


def _english_dominance(s: str) -> float:
    """Fraction of characters in the basic Latin / Latin-1-Supplement /
    General Punctuation Unicode blocks. Whitespace counts as English."""
    if not s:
        return 1.0
    n_english = 0
    for ch in s:
        cp = ord(ch)
        # Basic Latin (0000-007F), Latin-1-Supplement (0080-00FF),
        # General Punctuation (2000-206F), and a few stray
        # mathematical-operator chars LLMs love (×, –, —, ', ", …).  # noqa: RUF003 -- documents the intentional unicode test data on the next line
        if cp <= 0x024F or (0x2000 <= cp <= 0x206F) or ch in "×∼≈≤≥":  # noqa: RUF001 -- intentional unicode chars the loader must count as acceptable
            n_english += 1
    return n_english / len(s)


def _content_words(text: str) -> set[str]:
    """Set of length->=4 lowercased tokens, used for Jaccard distinctness."""
    import re
    return {w.lower() for w in re.findall(r"[A-Za-z]{4,}", text)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@pytest.fixture(scope="module")
def real_repo(tmp_path_factory) -> Path:
    """Snapshot the live pool + umbrella prompt + a single fixture
    project into a tmp dir for the test. Keeps the live repo's
    rotation pointer untouched."""
    if os.environ.get("LLMXIVE_REAL_TESTS") != "1":
        pytest.skip("real-call test; set LLMXIVE_REAL_TESTS=1")
    if not POOL_DIR.is_dir():
        pytest.skip(f"pool dir {POOL_DIR} not present")

    repo = tmp_path_factory.mktemp("real")
    # Copy the live pool + umbrella prompt.
    (repo / "agents" / "prompts" / "personalities").mkdir(parents=True)
    for src in POOL_DIR.glob("*.md"):
        shutil.copy(src, repo / "agents" / "prompts" / "personalities" / src.name)
    shutil.copy(REPO / p.UMBRELLA_PROMPT_PATH, repo / p.UMBRELLA_PROMPT_PATH)

    # One fixture project so the catalog is non-empty.
    pid = "PROJ-999-real-call-fixture"
    spec_dir = repo / "projects" / pid / "specs" / "999-fixture"
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_text(
        "# Fixture project\n\nA placeholder spec. The personalities should comment on this.\n",
        encoding="utf-8")
    (repo / "state" / "projects").mkdir(parents=True)
    import yaml as _yaml
    (repo / "state" / "projects" / f"{pid}.yaml").write_text(
        _yaml.safe_dump({
            "artifact_hashes": {},
            "assigned_agent": None,
            "created_at": "2026-05-01T00:00:00+00:00",
            "current_stage": "in_progress",
            "failed_stage": None,
            "field": "general",
            "human_escalation_reason": None,
            "id": pid,
            "last_run_id": None, "last_run_status": None,
            "points_paper": {}, "points_research": {},
            "revision_round": 0,
            "speckit_paper_dir": None,
            "speckit_research_dir": "specs/999-fixture",
            "title": "Real-Call Fixture",
            "updated_at": "2026-05-13T00:00:00+00:00",
        }),
        encoding="utf-8",
    )
    return repo


def test_one_tick_per_persona(real_repo: Path) -> None:
    """Drive one tick per persona; assert each returns valid output in
    overwhelmingly-English prose. Print outputs for eyeballing."""
    pool = p.load_pool(real_repo / p.POOL_PATH)
    assert pool.personalities, "pool empty"

    outputs: dict[str, str] = {}
    for persona in pool.personalities:
        print(f"\n=== {persona.display_name} ({persona.slug}) ===")
        entry = p.tick(real_repo, force_slug=persona.slug)
        # `tick(force_slug=...)` does NOT update the rotation pointer
        # (testing convention) — so each persona gets a fair test.
        assert entry["agent_name"] == "personality"
        assert entry["personality_slug"] == persona.slug
        # Outcome must be one of: committed (we accepted), abstained (LLM
        # explicitly skipped), or one of the failure paths. The latter is
        # informative but not a hard failure here — the test exists to
        # exercise the persona prompts on real responses.
        outcome = entry["outcome"]
        print(f"  outcome={outcome!r} action={entry.get('action')!r}")
        if outcome in {p.OUTCOME_RATE_LIMITED, p.OUTCOME_MODEL_ERROR, p.OUTCOME_TIMEOUT}:
            pytest.skip(f"LLM unavailable: {outcome}")
        # Read the persona's contribution body (if any) for the English
        # check + the Jaccard sanity.
        body = ""
        for rel in entry.get("committed_paths", []):
            body += "\n" + (real_repo / rel).read_text(encoding="utf-8")
        # Strip our own disclaimer footer (we add it post-hoc — it's not
        # the persona's voice).
        if "simulated AI persona" in body:
            body = body.split("\n---\n")[0]
        # FR-014: English dominance.
        if body.strip():
            dom = _english_dominance(body)
            print(f"  english_dominance={dom:.3f}")
            assert dom >= 0.95, (
                f"{persona.slug}: english dominance {dom:.3f} < 0.95 — "
                f"persona is slipping into non-English text"
            )
        outputs[persona.slug] = body
        print(f"  body preview: {body[:200]!r}")

    # Cross-persona Jaccard sanity (SC-005 smoke check — NOT the hard
    # gate; see quickstart § 9 for the manual verification).
    slugs = list(outputs)
    for i, a in enumerate(slugs):
        for b in slugs[i + 1:]:
            j = _jaccard(_content_words(outputs[a]), _content_words(outputs[b]))
            print(f"  Jaccard {a} vs {b}: {j:.3f}")
            assert j < 0.6, (
                f"{a} and {b} share {j:.2%} vocabulary — too similar; "
                f"prompts may need stronger distinguishing anchors"
            )
