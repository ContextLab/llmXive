"""Web-data personalities block tests (T055, US6 / FR-024).

Asserts that `_build_personalities_block` emits the array consumed by the
About-page Personality Registry modal, in the right shape, sorted by slug,
with well-formed prompt URLs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from llmxive.web_data import _build_personalities_block


def _seed_pool(pool_dir: Path, n: int) -> None:
    pool_dir.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        (pool_dir / f"p-{i:03d}.md").write_text(
            f"---\n"
            f'display_name: "Persona {i:03d}"\n'
            f'summary: "Test persona {i:03d} short summary."\n'
            f'sources: ["source-one", "source-two", "source-three"]\n'
            f"---\n\nBody\n",
            encoding="utf-8",
        )


@pytest.fixture
def repo_with_pool(tmp_path: Path) -> Path:
    pool = tmp_path / "agents" / "prompts" / "personalities"
    _seed_pool(pool, 3)
    return tmp_path


def test_block_emits_one_entry_per_personality(repo_with_pool: Path) -> None:
    block = _build_personalities_block(repo_with_pool)
    assert len(block) == 3


def test_block_sorted_by_slug(repo_with_pool: Path) -> None:
    block = _build_personalities_block(repo_with_pool)
    slugs = [b["slug"] for b in block]
    assert slugs == sorted(slugs)


def test_entry_has_all_required_fields(repo_with_pool: Path) -> None:
    block = _build_personalities_block(repo_with_pool)
    required = {"slug", "display_name", "summary", "sources",
                "prompt_repo_path", "prompt_raw_url", "prompt_github_url"}
    for entry in block:
        assert required.issubset(entry.keys()), f"missing keys: {required - entry.keys()}"


def test_prompt_urls_are_well_formed(repo_with_pool: Path) -> None:
    block = _build_personalities_block(repo_with_pool)
    for entry in block:
        assert entry["prompt_raw_url"].startswith("https://raw.githubusercontent.com/")
        assert entry["prompt_raw_url"].endswith(f"/agents/prompts/personalities/{entry['slug']}.md")
        assert entry["prompt_github_url"].startswith("https://github.com/")
        assert entry["prompt_github_url"].endswith(f"/agents/prompts/personalities/{entry['slug']}.md")
        assert entry["prompt_repo_path"] == f"agents/prompts/personalities/{entry['slug']}.md"


def test_no_pool_dir_returns_empty_list(tmp_path: Path) -> None:
    # No agents/prompts/personalities/ at all → empty block.
    block = _build_personalities_block(tmp_path)
    assert block == []


def test_malformed_file_skipped(tmp_path: Path) -> None:
    pool = tmp_path / "agents" / "prompts" / "personalities"
    _seed_pool(pool, 2)
    # Add a malformed file.
    (pool / "bad.md").write_text(
        '---\nsummary: "no display_name"\nsources: ["a-source", "b-source", "c-source"]\n---\n\nBody\n',
        encoding="utf-8",
    )
    block = _build_personalities_block(tmp_path)
    # 2 valid entries — the malformed one is skipped silently.
    assert len(block) == 2
    assert "bad" not in {b["slug"] for b in block}


def test_live_pool_emits_expected_count(tmp_path: Path) -> None:
    """Integration smoke: run against the actual repo pool.

    Roster as of 2026-05-16: 15 personas (Aristotle and Socrates were
    rotated out in PR #185 in favor of 7 modern scientific figures;
    see notes in test_personality_prompt_schema.py for the rationale)."""
    repo = Path(__file__).resolve().parents[2]
    pool_dir = repo / "agents" / "prompts" / "personalities"
    if not pool_dir.is_dir():
        pytest.skip("live pool not present")
    block = _build_personalities_block(repo)
    slugs = {e["slug"] for e in block}
    canonical = {
        # v1 retained
        "ada-lovelace", "dan-rockmore", "daniel-kahneman",
        "david-krakauer", "geoffrey-west", "john-von-neumann",
        "marie-curie", "rosalind-franklin",
        # 2026-05-16 additions — replacing aristotle/socrates
        "alan-turing", "albert-einstein", "eric-kandel",
        "freeman-dyson", "linus-pauling", "richard-feynman",
        "stephen-wolfram",
    }
    missing = canonical - slugs
    assert not missing, f"missing canonical personas from emitted block: {sorted(missing)}"
