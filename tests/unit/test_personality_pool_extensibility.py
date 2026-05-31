"""Pool-extensibility tests (T051 + T052, US2 / FR-020).

Asserts the extensibility property: adding an 11th personality file is
all it takes to bring it into the rotation. No code changes, no template
edits — Story 2 / FR-020. Drives :func:`personality.load_pool` and
:func:`personality.select_next` over tmp-dir fixtures of varying sizes.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.agents import personality as p

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "personality"


def _seed_pool(pool_dir: Path, n: int) -> list[str]:
    """Create N valid personality files in `pool_dir` with deterministic
    slugs `p-001`...`p-NNN`. Returns the slugs in lex order."""
    pool_dir.mkdir(parents=True, exist_ok=True)
    slugs = []
    for i in range(n):
        slug = f"p-{i:03d}"
        slugs.append(slug)
        (pool_dir / f"{slug}.md").write_text(
            f"---\n"
            f'display_name: "Persona {i:03d}"\n'
            f'summary: "Test persona {i:03d} for extensibility tests."\n'
            f'sources: ["source-one", "source-two", "source-three"]\n'
            f"---\n\nBody {i}\n",
            encoding="utf-8",
        )
    return sorted(slugs)


class TestPoolExtensibility:
    def test_adding_11th_file_appears_in_pool(self, tmp_path: Path) -> None:
        pool = tmp_path / "pool"
        _seed_pool(pool, 10)
        # Snapshot the 10-entry pool.
        res = p.load_pool(pool)
        assert len(res.personalities) == 10
        # Now add an 11th file.
        (pool / "p-010.md").write_text(
            "---\n"
            'display_name: "New Persona"\n'
            'summary: "Added after the original ten."\n'
            'sources: ["source-A", "source-B", "source-C"]\n'
            "---\n\nBody\n",
            encoding="utf-8",
        )
        res2 = p.load_pool(pool)
        # Without re-running tests or restarting anything, the 11th
        # personality is now in the pool.
        assert len(res2.personalities) == 11
        slugs = [pp.slug for pp in res2.personalities]
        assert "p-010" in slugs

    def test_11th_appears_in_rotation_within_one_cycle(self, tmp_path: Path) -> None:
        pool = tmp_path / "pool"
        _slugs = _seed_pool(pool, 10)
        # Drive the rotation through all 10 starting from the first.
        res = p.load_pool(pool)
        # Add the 11th BEFORE we visit it.
        (pool / "p-010.md").write_text(
            "---\n"
            'display_name: "Eleventh Persona"\n'
            'summary: "Added mid-rotation; the next cycle includes it."\n'
            'sources: ["source-A", "source-B", "source-C"]\n'
            "---\n\nBody\n",
            encoding="utf-8",
        )
        # Reload — the pool has 11 entries now.
        res = p.load_pool(pool)
        # Walk the rotation: starting from first, advance 10 times. Each
        # advance picks a unique slug. After all 11 advances we've visited
        # every slug.
        visited: list[str] = []
        last_used = None
        for _ in range(11):
            nxt = p.select_next(res.personalities, last_used)
            visited.append(nxt.slug)
            last_used = nxt.slug
        assert set(visited) == set([pp.slug for pp in res.personalities])
        # The new slug appears exactly once.
        assert visited.count("p-010") == 1

    def test_deleting_file_removes_from_rotation_immediately(self, tmp_path: Path) -> None:
        """Inverse of extensibility — a deleted persona vanishes from the
        rotation without breaking it."""
        pool = tmp_path / "pool"
        _seed_pool(pool, 5)
        (pool / "p-002.md").unlink()
        res = p.load_pool(pool)
        slugs = [pp.slug for pp in res.personalities]
        assert "p-002" not in slugs
        assert len(slugs) == 4


class TestMalformedFileSkipped:
    def test_malformed_file_does_not_break_rotation(self, tmp_path: Path) -> None:
        """Story 2 scenario 2: a malformed personality file is skipped;
        the rotation continues over the well-formed entries."""
        pool = tmp_path / "pool"
        _seed_pool(pool, 5)
        # Replace one entry with a malformed file (missing display_name).
        (pool / "p-002.md").write_text(
            "---\n"
            'summary: "no display_name here"\n'
            'sources: ["source-A", "source-B", "source-C"]\n'
            "---\n\nBody\n",
            encoding="utf-8",
        )
        res = p.load_pool(pool)
        # Well-formed entries: 4 of 5.
        assert len(res.personalities) == 4
        # Error count: 1 (the malformed one).
        assert res.error_count == 1
        assert "display_name" in res.errors[0]["reason"]
        # Rotation continues without crashing.
        last_used = None
        for _ in range(4):
            nxt = p.select_next(res.personalities, last_used)
            assert nxt is not None
            last_used = nxt.slug
