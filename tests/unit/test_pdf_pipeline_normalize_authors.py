"""T046: tests for normalize_authors (FR-016 canonical \\authorblock)."""

from __future__ import annotations

import unittest

from llmxive.pipeline.pdf_pipeline.normalize_authors import (
    _split_authors, _strip_thanks, normalize,
)


class TestStripThanks(unittest.TestCase):
    def test_strips_thanks(self):
        self.assertEqual(_strip_thanks(r"Smith\thanks{Author note}"), "Smith")

    def test_strips_footnote(self):
        self.assertEqual(_strip_thanks(r"Smith\footnote{a note}"), "Smith")


class TestSplitAuthors(unittest.TestCase):
    def test_simple_and(self):
        names = _split_authors(r"Jane Smith \and John Doe")
        self.assertEqual(names, ["Jane Smith", "John Doe"])

    def test_backslash_backslash(self):
        names = _split_authors(r"Jane Smith \\ John Doe \\ Susan Roe")
        self.assertEqual(names, ["Jane Smith", "John Doe", "Susan Roe"])

    def test_strips_emails(self):
        names = _split_authors(r"Jane Smith jane@example.com \and John Doe")
        self.assertEqual(names, ["Jane Smith", "John Doe"])

    def test_strips_parenthetical_affil(self):
        names = _split_authors(r"Jane Smith (Dartmouth) \and John Doe (MIT)")
        self.assertEqual(names, ["Jane Smith", "John Doe"])


class TestNormalize(unittest.TestCase):
    def test_simple_author_replaced_with_authorblock(self):
        src = r"""\documentclass{article}
\title{X}
\author{Jane Smith \and John Doe}
\begin{document}
\end{document}
"""
        out = normalize(src)
        self.assertIn(r"\authorblock{Jane Smith, John Doe}", out)
        self.assertNotIn(r"\author{Jane Smith \and John Doe}", out)

    def test_no_author_macro_unchanged(self):
        src = "\\documentclass{article}\n\\begin{document}\nbody\n\\end{document}\n"
        self.assertEqual(normalize(src), src)

    def test_collects_emails(self):
        src = r"""\author{Jane Smith jane@dartmouth.edu \and John Doe john@mit.edu}"""
        out = normalize(src)
        self.assertIn("jane@dartmouth.edu", out)
        self.assertIn("john@mit.edu", out)

    def test_collects_affiliation(self):
        src = (r"\author{Jane Smith \and John Doe}" + "\n" +
               r"\affiliation{Dartmouth College; MIT}")
        out = normalize(src)
        self.assertIn(r"\authorblock{Jane Smith, John Doe}{Dartmouth College; MIT}", out)


if __name__ == "__main__":
    unittest.main()
