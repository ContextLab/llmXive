"""T045: tests for normalize_figures (FR-015 bounded widths)."""

from __future__ import annotations

import unittest

from llmxive.pipeline.pdf_pipeline.normalize_figures import (
    _parse_width_to_ratio, _ratio_to_bucket, normalize,
)


class TestRatioParsing(unittest.TestCase):
    def test_textwidth_fraction(self):
        self.assertAlmostEqual(_parse_width_to_ratio(r"0.45\textwidth"), 0.45)

    def test_linewidth_fraction(self):
        self.assertAlmostEqual(_parse_width_to_ratio(r"0.8\linewidth"), 0.8)

    def test_bare_textwidth(self):
        self.assertEqual(_parse_width_to_ratio(r"\textwidth"), 1.0)

    def test_centimeters(self):
        # 16.5cm ≈ 6.5in (textwidth) -> ratio ~1.0
        r = _parse_width_to_ratio("16.51cm")
        self.assertAlmostEqual(r, 1.0, places=2)

    def test_points(self):
        # ~1in = 72.27pt
        r = _parse_width_to_ratio("72.27pt")
        self.assertAlmostEqual(r, 1.0 / 6.5, places=2)

    def test_unparseable_returns_none(self):
        self.assertIsNone(_parse_width_to_ratio("garbage"))


class TestBucketing(unittest.TestCase):
    def test_narrow(self):
        self.assertEqual(_ratio_to_bucket(0.30), "narrow")

    def test_column(self):
        self.assertEqual(_ratio_to_bucket(0.70), "column")

    def test_full(self):
        self.assertEqual(_ratio_to_bucket(1.00), "full")
        self.assertEqual(_ratio_to_bucket(0.98), "full")


class TestRewrite(unittest.TestCase):
    def test_narrow_width_rewrites_to_bucket(self):
        s = r"\includegraphics[width=0.3\textwidth]{fig1.pdf}"
        out = normalize(s)
        # Single backslash in emitted LaTeX (the fixture bug we fixed)
        self.assertIn(r"width=0.45\linewidth", out)
        self.assertIn("fig1.pdf", out)

    def test_column_width_rewrites_to_linewidth(self):
        s = r"\includegraphics[width=0.7\textwidth]{fig2.png}"
        out = normalize(s)
        self.assertIn(r"width=\linewidth", out)

    def test_full_width_rewrites_to_textwidth(self):
        s = r"\includegraphics[width=\textwidth]{fig3.pdf}"
        out = normalize(s)
        self.assertIn(r"width=\textwidth", out)

    def test_no_width_gets_linewidth(self):
        s = r"\includegraphics{fig4.png}"
        out = normalize(s)
        self.assertIn("width", out)
        self.assertIn("fig4.png", out)

    def test_other_options_preserved(self):
        s = r"\includegraphics[width=0.5\textwidth,keepaspectratio]{f.pdf}"
        out = normalize(s)
        self.assertIn("keepaspectratio", out)

    def test_unparseable_width_left_alone(self):
        s = r"\includegraphics[width=foo-bar]{f.pdf}"
        out = normalize(s)
        # Unparseable -> source unchanged
        self.assertEqual(out, s)


if __name__ == "__main__":
    unittest.main()
