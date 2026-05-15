"""T039: classify_failure unit tests covering FR-018 classification matrix."""

from __future__ import annotations

import unittest

from llmxive.pipeline.pdf_pipeline.classify_failure import classify


class TestClassifyFailure(unittest.TestCase):
    def test_audit_tool_crash_always_classified_as_crash(self) -> None:
        self.assertEqual(
            classify("audit_tool_crash", "stack trace", source_available=True),
            "audit_tool_crash",
        )
        self.assertEqual(
            classify("audit_tool_crash", "stack trace", source_available=False),
            "audit_tool_crash",
        )

    def test_source_missing_overrides_other_kinds(self) -> None:
        for kind in (
            "literal_command_text",
            "non_square_bracket_cite",
            "non_canonical_authorblock",
            "off_spec_figure_width",
            "section_number_gap",
        ):
            self.assertEqual(
                classify(kind, "evidence", source_available=False),
                "source_missing",
                f"kind={kind} with no source should be source_missing",
            )

    def test_source_fixable_kinds(self) -> None:
        for kind in (
            "literal_command_text",
            "non_square_bracket_cite",
            "non_canonical_authorblock",
            "off_spec_figure_width",
        ):
            self.assertEqual(
                classify(kind, "evidence", source_available=True),
                "source_fixable",
                f"kind={kind} with source should be source_fixable",
            )

    def test_section_number_gap_is_unsupported(self) -> None:
        self.assertEqual(
            classify("section_number_gap", "1, 2, 4", source_available=True),
            "unsupported_construct",
        )


if __name__ == "__main__":
    unittest.main()
