"""T056a: \\unsupportedblock fails loudly per FR-020.

Unit-level: the restyle pipeline correctly wraps configured unsupported
environments in \\unsupportedblock so lualatex errors out rather than
silently rendering raw text.

This test does NOT invoke lualatex itself (CI may lack the toolchain);
the integration of `\\unsupportedblock -> \\@latex@error` lives in
papers/.style/llmxive.cls and is exercised in CI by the registry e2e
test (T049). Here we verify the source-rewrite behavior.
"""

from __future__ import annotations

import unittest

from llmxive.pipeline.pdf_pipeline import restyle


class TestUnsupportedBlockRewrite(unittest.TestCase):
    def setUp(self):
        # Patch in a fake unsupported env so the test is self-contained
        self._saved = list(restyle.UNSUPPORTED_ENVS)
        restyle.UNSUPPORTED_ENVS.append("mycustomenv")

    def tearDown(self):
        restyle.UNSUPPORTED_ENVS.clear()
        restyle.UNSUPPORTED_ENVS.extend(self._saved)

    def test_unsupported_env_wrapped(self):
        src = (
            r"\documentclass{article}" + "\n" +
            r"\begin{document}" + "\n" +
            r"\begin{mycustomenv}body content\end{mycustomenv}" + "\n" +
            r"\end{document}"
        )
        out = restyle.restyle_source(src)
        self.assertIn(r"\unsupportedblock{mycustomenv}", out)
        # Source's original \begin/\end is gone
        self.assertNotIn(r"\begin{mycustomenv}", out)
        self.assertNotIn(r"\end{mycustomenv}", out)
        # documentclass swapped to llmxive
        self.assertIn(r"\documentclass{llmxive}", out)

    def test_no_unsupported_envs_passthrough(self):
        src = (
            r"\documentclass{article}" + "\n" +
            r"\begin{document}body\end{document}"
        )
        out = restyle.restyle_source(src)
        self.assertIn(r"\documentclass{llmxive}", out)
        self.assertNotIn(r"\unsupportedblock", out)

    def test_class_macro_present_in_cls(self):
        # papers/.style/llmxive.cls MUST define \unsupportedblock so the
        # error path actually fires when lualatex sees it.
        import pathlib
        cls = pathlib.Path(__file__).resolve().parents[2] / "papers" / ".style" / "llmxive.cls"
        text = cls.read_text()
        self.assertIn(r"\newcommand{\unsupportedblock}", text)
        self.assertIn(r"\PackageError{llmxive}", text)


if __name__ == "__main__":
    unittest.main()
