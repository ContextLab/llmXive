"""T037: PDF audit text-level checks (literal commands, cite styles, section gaps)."""

from __future__ import annotations

import unittest

from llmxive.pipeline.pdf_pipeline.audit import (
    _check_cite_style,
    _check_literal_commands,
    _check_section_monotonicity,
)


class TestLiteralCommands(unittest.TestCase):
    def test_clean_text_no_failures(self) -> None:
        text = "This is normal scientific prose, no LaTeX commands."
        self.assertEqual(_check_literal_commands(text), [])

    def test_verb_command_detected(self) -> None:
        text = r"To install run \verb{pip install foo}."
        failures = _check_literal_commands(text)
        self.assertGreater(len(failures), 0)
        self.assertEqual(failures[0]["kind"], "literal_command_text")
        self.assertEqual(failures[0]["class"], "source_fixable")

    def test_texttt_command_detected(self) -> None:
        text = r"The function \texttt{foo_bar} processes input."
        self.assertGreater(len(_check_literal_commands(text)), 0)


class TestCiteStyle(unittest.TestCase):
    def test_square_bracket_passes(self) -> None:
        text = "Prior work [1] and [2,3] establish this."
        self.assertEqual(_check_cite_style(text), [])

    def test_author_year_detected(self) -> None:
        text = "Prior work (Smith, 2024) established this."
        failures = _check_cite_style(text)
        self.assertGreater(len(failures), 0)
        self.assertEqual(failures[0]["kind"], "non_square_bracket_cite")

    def test_et_al_detected(self) -> None:
        text = "Recent work (Smith et al., 2023) showed..."
        failures = _check_cite_style(text)
        self.assertGreater(len(failures), 0)

    def test_superscript_detected(self) -> None:
        text = "This is supported¹ by prior work²."
        failures = _check_cite_style(text)
        self.assertGreater(len(failures), 0)


class TestSectionMonotonicity(unittest.TestCase):
    def test_monotonic_passes(self) -> None:
        pages = [
            "1 Introduction\n\nProse...",
            "2 Methods\n\nProse...",
            "3 Results\n\nProse...",
        ]
        self.assertEqual(_check_section_monotonicity(pages), [])

    def test_gap_detected(self) -> None:
        pages = [
            "1 Introduction\n\nProse...",
            "2 Methods\n\nProse...",
            "4 Discussion\n\nProse...",  # missing section 3
        ]
        failures = _check_section_monotonicity(pages)
        self.assertGreater(len(failures), 0)
        self.assertEqual(failures[0]["kind"], "section_number_gap")
        self.assertIn("3", failures[0]["evidence"])

    def test_empty_pages_no_failure(self) -> None:
        self.assertEqual(_check_section_monotonicity([]), [])
        self.assertEqual(_check_section_monotonicity(["", ""]), [])


if __name__ == "__main__":
    unittest.main()
