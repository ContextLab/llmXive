"""Real-network test for llmxive.audit.liveness (spec 010, T009).

Gated by LLMXIVE_NETWORK_TESTS=1 so CI runs without internet don't fail.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from llmxive.audit import liveness


@unittest.skipUnless(
    os.environ.get("LLMXIVE_NETWORK_TESTS") == "1",
    "set LLMXIVE_NETWORK_TESTS=1 to run real-network tests",
)
class TestLivenessReal(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cache = Path(self.tmp.name) / "cache.json"

    def test_real_arxiv_pass(self) -> None:
        # 2202.01933 is a real, well-known arXiv paper.
        result = liveness.check_pointer("arxiv", "2202.01933", cache_path=self.cache)
        self.assertEqual(result["status"], "pass", result)
        self.assertIn(result["http_code"], {200, 301, 302})

    def test_real_doi_pass(self) -> None:
        # 10.1038/171737a0 — Watson & Crick (1953); resolves via doi.org.
        result = liveness.check_pointer("doi", "10.1038/171737a0", cache_path=self.cache)
        self.assertEqual(result["status"], "pass", result)

    def test_nonexistent_arxiv_fail(self) -> None:
        # 0000.00000 — syntactically arXiv-shaped but doesn't exist.
        result = liveness.check_pointer("arxiv", "0000.00000", cache_path=self.cache)
        self.assertEqual(result["status"], "fail", result)


if __name__ == "__main__":
    unittest.main()
