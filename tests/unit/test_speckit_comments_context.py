"""Unit tests for llmxive.speckit._comments_context.

Spec 011 / FR-013: comments must propagate from `reviews/research/*.md`
into the speckit user prompt so subsequent agent runs are aware of
prior feedback.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from llmxive.speckit._comments_context import (
    DEFAULT_LIMIT,
    PER_COMMENT_MAX_CHARS,
    render_recent_comments_block,
)


class TestRenderRecentCommentsBlock(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project_dir = Path(self.tmp.name) / "PROJ-001-test"
        self.reviews = self.project_dir / "reviews" / "research"
        self.reviews.mkdir(parents=True, exist_ok=True)

    def _write(self, name: str, body: str) -> None:
        (self.reviews / name).write_text(body, encoding="utf-8")

    def test_empty_reviews_dir_returns_empty_string(self) -> None:
        self.assertEqual(render_recent_comments_block(self.project_dir), "")

    def test_no_reviews_dir_returns_empty_string(self) -> None:
        empty = Path(self.tmp.name) / "PROJ-002-empty"
        empty.mkdir()
        self.assertEqual(render_recent_comments_block(empty), "")

    def test_single_comment_renders_heading_and_body(self) -> None:
        self._write("alice__2026-05-01__research.md", "Alice's review of the spec.")
        out = render_recent_comments_block(self.project_dir)
        self.assertIn("# Recent reviewer / personality comments", out)
        self.assertIn("alice__2026-05-01__research.md", out)
        self.assertIn("Alice's review of the spec.", out)

    def test_newest_first_ordering(self) -> None:
        self._write("alice__2026-05-01__research.md", "older")
        self._write("bob__2026-05-15__research.md", "newer")
        out = render_recent_comments_block(self.project_dir)
        bob_idx = out.find("bob__2026-05-15")
        alice_idx = out.find("alice__2026-05-01")
        self.assertGreater(alice_idx, bob_idx, "newer comment should appear first")

    def test_limit_caps_at_default(self) -> None:
        for i in range(DEFAULT_LIMIT + 3):
            self._write(f"persona{i}__2026-05-{i + 1:02d}__research.md", f"body {i}")
        out = render_recent_comments_block(self.project_dir)
        # Count comment headings
        n_h2 = out.count("\n## `")
        self.assertEqual(n_h2, DEFAULT_LIMIT)

    def test_custom_limit_overrides_default(self) -> None:
        for i in range(5):
            self._write(f"persona{i}__2026-05-{i + 1:02d}__research.md", "body")
        out = render_recent_comments_block(self.project_dir, limit=2)
        n_h2 = out.count("\n## `")
        self.assertEqual(n_h2, 2)

    def test_long_body_gets_truncated(self) -> None:
        long_body = "x" * (PER_COMMENT_MAX_CHARS * 2)
        self._write("alice__2026-05-01__research.md", long_body)
        out = render_recent_comments_block(self.project_dir)
        self.assertIn("*[truncated]*", out)
        # The full untruncated body must NOT appear in full
        self.assertLess(out.count("x"), PER_COMMENT_MAX_CHARS * 2)


if __name__ == "__main__":
    unittest.main()
