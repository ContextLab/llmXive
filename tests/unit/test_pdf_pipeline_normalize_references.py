"""T044: tests for normalize_references.

Covers \\citet/\\citep/\\cite* variants, missing-style injection, natbib-aware
mode, and the cite-order requirement (Clarification Q1 / FR-014).
"""

from __future__ import annotations

import unittest

from llmxive.pipeline.pdf_pipeline.normalize_references import (
    normalize, normalize_bib_style, normalize_cite_macros,
    normalize_natbib_to_numeric,
)


class TestCiteMacroNormalization(unittest.TestCase):
    def test_citet_to_cite(self):
        self.assertEqual(normalize_cite_macros(r"as \citet{foo} shows"),
                         r"as \cite{foo} shows")

    def test_citep_to_cite(self):
        self.assertEqual(normalize_cite_macros(r"(see \citep{bar})"),
                         r"(see \cite{bar})")

    def test_cite_star_to_cite(self):
        self.assertEqual(normalize_cite_macros(r"\cite*{a,b}"),
                         r"\cite{a,b}")

    def test_plain_cite_unchanged(self):
        self.assertEqual(normalize_cite_macros(r"\cite{x}"),
                         r"\cite{x}")


class TestBibStyleNormalization(unittest.TestCase):
    def test_replaces_existing_style(self):
        s = r"\bibliographystyle{plain}" + "\n" + r"\bibliography{refs}"
        out = normalize_bib_style(s)
        self.assertIn(r"\bibliographystyle{unsrt}", out)
        self.assertNotIn(r"\bibliographystyle{plain}", out)

    def test_replaces_apa_style(self):
        s = r"\bibliographystyle{apa}"
        self.assertIn(r"\bibliographystyle{unsrt}", normalize_bib_style(s))

    def test_injects_when_missing(self):
        s = "Some prose\n" + r"\begin{document}" + "\nbody\n" + r"\end{document}"
        out = normalize_bib_style(s)
        self.assertIn(r"\bibliographystyle{unsrt}", out)
        self.assertTrue(out.index(r"\bibliographystyle{unsrt}") < out.index(r"\begin{document}"))


class TestNatbibNormalization(unittest.TestCase):
    def test_rewrites_natbib_options(self):
        s = r"\usepackage[authoryear]{natbib}"
        out = normalize_natbib_to_numeric(s)
        self.assertIn(r"\usepackage[numbers,sort]{natbib}", out)

    def test_adds_options_to_bare_natbib(self):
        s = r"\usepackage{natbib}"
        out = normalize_natbib_to_numeric(s)
        self.assertIn(r"\usepackage[numbers,sort]{natbib}", out)


class TestEndToEnd(unittest.TestCase):
    def test_full_normalize_idempotent(self):
        s = r"""
\documentclass{article}
\usepackage[authoryear]{natbib}
\bibliographystyle{apa}
\begin{document}
See \citet{smith} and \citep{jones,brown}. Also \cite*{star}.
\end{document}
"""
        out1 = normalize(s)
        out2 = normalize(out1)
        self.assertEqual(out1, out2, "normalize must be idempotent")
        # Every \citeX should now be plain \cite
        self.assertNotIn(r"\citet", out1)
        self.assertNotIn(r"\citep", out1)
        # natbib in numeric+sort mode
        self.assertIn(r"\usepackage[numbers,sort]{natbib}", out1)


if __name__ == "__main__":
    unittest.main()
