"""T027: _real_only_guard.py unit tests (FR-009 + FR-010).

Verifies:
  - Real artifact passes silently
  - Template artifact raises TemplateRefused with an actionable missing-context message
  - Missing-file path raises FileNotFoundError
"""

from __future__ import annotations

import unittest
from pathlib import Path

from llmxive.speckit._real_only_guard import (
    TemplateRefused,
    assert_real_or_raise,
    is_real,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_REAL = REPO_ROOT / "tests" / "fixtures" / "audit" / "speckit_real" / "spec.md"
FIXTURE_TEMPLATE = REPO_ROOT / "tests" / "fixtures" / "audit" / "speckit_template" / "spec.md"


class TestRealOnlyGuard(unittest.TestCase):
    def test_real_artifact_passes_silently(self):
        # Real fixture passes without raising
        assert_real_or_raise(FIXTURE_REAL, repo_root=REPO_ROOT)

    def test_is_real_returns_true_for_real(self):
        self.assertTrue(is_real(FIXTURE_REAL, repo_root=REPO_ROOT))

    def test_template_artifact_raises_template_refused(self):
        with self.assertRaises(TemplateRefused) as cm:
            assert_real_or_raise(FIXTURE_TEMPLATE, repo_root=REPO_ROOT)
        exc = cm.exception
        self.assertEqual(exc.classification, "template")
        self.assertIsNotNone(exc.missing_context)
        # Error message must mention progression points NOT being incremented (SC-004)
        self.assertIn("progression points", str(exc))
        self.assertIn("NOT incremented", str(exc))

    def test_is_real_returns_false_for_template(self):
        self.assertFalse(is_real(FIXTURE_TEMPLATE, repo_root=REPO_ROOT))

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            assert_real_or_raise("/tmp/nonexistent_path_009.md", repo_root=REPO_ROOT)

    def test_actionable_error_for_action_required(self):
        # Fixture has ACTION REQUIRED markers — error should mention them
        with self.assertRaises(TemplateRefused) as cm:
            assert_real_or_raise(FIXTURE_TEMPLATE, repo_root=REPO_ROOT)
        # The fixture has ACTION REQUIRED in a comment + bracketed placeholders.
        # The auditor will fire 'literal_template_phrases>=3' first; missing_context
        # will be one of the two messages.
        missing = cm.exception.missing_context
        self.assertTrue(
            "placeholders" in missing or "ACTION REQUIRED" in missing or "bracketed" in missing,
            f"unexpected missing_context: {missing!r}",
        )


if __name__ == "__main__":
    unittest.main()
