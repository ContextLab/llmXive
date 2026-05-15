"""Unit tests for llmxive.speckit._diff_guard (spec 010 fix).

Catches the family of diff shapes that the previous guard missed and
that caused 8 production .md files to be polluted with `--- a/<path>`
and `+++ b/<path>` headers committed verbatim.
"""

from __future__ import annotations

import unittest

from llmxive.speckit._diff_guard import looks_like_diff, refuse_if_diff


class TestLooksLikeDiff(unittest.TestCase):
    def test_clean_markdown_is_not_a_diff(self) -> None:
        text = "# My Spec\n\n## User scenarios\n\nReal content here.\n"
        ok, reason = looks_like_diff(text)
        self.assertFalse(ok, reason)

    def test_empty_string_is_not_a_diff(self) -> None:
        self.assertEqual(looks_like_diff(""), (False, ""))
        self.assertEqual(looks_like_diff("   \n\n  "), (False, ""))

    def test_hunk_only_lead_is_diff(self) -> None:
        text = "@@ -145,7 +145,7 @@\n some context\n+added\n-removed\n"
        ok, reason = looks_like_diff(text)
        self.assertTrue(ok, reason)
        self.assertIn("@@", reason)

    def test_full_unified_diff_is_caught(self) -> None:
        """The exact pollution shape we observed in PROJ-001 tasks.md."""
        text = (
            "--- a/tasks.md\n"
            "+++ b/tasks.md\n"
            "@@ -145,7 +145,7 @@\n"
            " context\n"
            "+added\n"
            "-removed\n"
        )
        ok, reason = looks_like_diff(text)
        self.assertTrue(ok, reason)

    def test_unified_diff_file_marker_alone_is_caught(self) -> None:
        text = "--- a/spec.md\nsome stuff after the marker\n"
        ok, reason = looks_like_diff(text)
        self.assertTrue(ok, reason)
        self.assertIn("unified-diff file marker", reason)

    def test_plus_plus_plus_lead_is_caught(self) -> None:
        text = "+++ b/tasks.md\n@@ -1,4 +1,4 @@\n"
        ok, reason = looks_like_diff(text)
        self.assertTrue(ok, reason)

    def test_two_markers_anywhere_is_caught(self) -> None:
        """Even if a diff doesn't lead the file, two markers anywhere means
        the LLM emitted a patch in the middle of prose."""
        text = (
            "# Some prose\n"
            "\n"
            "Then this snippet:\n"
            "\n"
            "--- a/foo.md\n"
            "+++ b/foo.md\n"
            "\n"
            "More prose.\n"
        )
        ok, reason = looks_like_diff(text)
        self.assertTrue(ok, reason)

    def test_context_diff_format_is_caught(self) -> None:
        text = "*** Some Title\n--- Other Title\n***************\n"
        ok, reason = looks_like_diff(text)
        self.assertTrue(ok, reason)

    def test_realistic_spec_markdown_passes(self) -> None:
        """Real spec.md content (with em-dashes, headings, etc.) MUST NOT
        be mis-classified as a diff."""
        text = (
            "# Feature Specification: Real Spec\n"
            "\n"
            "**Created**: 2026-05-15\n"
            "\n"
            "## User Scenarios\n"
            "\n"
            "Story 1 — the user does X and expects Y.\n"
            "\n"
            "## Requirements\n"
            "\n"
            "- FR-001: System MUST do A\n"
            "- FR-002: System MUST do B\n"
        )
        ok, reason = looks_like_diff(text)
        self.assertFalse(ok, reason)

    def test_horizontal_rule_with_dashes_is_not_a_diff(self) -> None:
        """Markdown HR rule (---) MUST NOT trigger the diff guard."""
        text = "Some content.\n\n---\n\nMore content after a horizontal rule.\n"
        ok, reason = looks_like_diff(text)
        self.assertFalse(ok, reason)


class TestRefuseIfDiff(unittest.TestCase):
    def test_clean_text_no_raise(self) -> None:
        refuse_if_diff("# Real spec\n\nbody\n", artifact_kind="spec.md")

    def test_diff_raises(self) -> None:
        text = "--- a/tasks.md\n+++ b/tasks.md\n@@ -1,4 +1,4 @@\n"
        with self.assertRaises(RuntimeError) as cm:
            refuse_if_diff(text, artifact_kind="tasks.md")
        self.assertIn("tasks.md", str(cm.exception))
        self.assertIn("diff", str(cm.exception).lower())


if __name__ == "__main__":
    unittest.main()
