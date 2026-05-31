"""Unit tests for llmxive.audit.liveness (spec 010, T008).

Mocks the httpx layer; verifies cache behavior. Real network calls are
covered by tests/real_call/test_personality_liveness_real.py (T009).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import httpx

from llmxive.audit import liveness


class _FakeResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code


class TestCheckPointer(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cache_path = Path(self.tmp.name) / "liveness-cache.json"

    def test_cache_hit_within_ttl_skips_head(self) -> None:
        # Pre-populate cache with a fresh entry.
        liveness._save_cache(
            {
                "2202.01933": {
                    "status": "pass",
                    "http_code": 200,
                    "checked_at": liveness._now_iso(),
                }
            },
            self.cache_path,
        )
        with patch.object(httpx, "head") as mock_head:
            result = liveness.check_pointer("arxiv", "2202.01933", cache_path=self.cache_path)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["http_code"], 200)
        mock_head.assert_not_called()

    def test_cache_miss_issues_head(self) -> None:
        with patch.object(httpx, "head", return_value=_FakeResponse(200)) as mock_head:
            result = liveness.check_pointer("arxiv", "2202.01933", cache_path=self.cache_path)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["http_code"], 200)
        mock_head.assert_called_once()
        # Cache file created.
        self.assertTrue(self.cache_path.exists())
        cache = json.loads(self.cache_path.read_text())
        self.assertIn("2202.01933", cache)

    def test_expired_cache_triggers_fresh_head(self) -> None:
        liveness._save_cache(
            {
                "10.1000/example": {
                    "status": "pass",
                    "http_code": 200,
                    "checked_at": "2020-01-01T00:00:00Z",  # very old
                }
            },
            self.cache_path,
        )
        with patch.object(httpx, "head", return_value=_FakeResponse(200)) as mock_head:
            liveness.check_pointer("doi", "10.1000/example", cache_path=self.cache_path)
        mock_head.assert_called_once()

    def test_non_2xx_3xx_is_fail(self) -> None:
        with patch.object(httpx, "head", return_value=_FakeResponse(404)):
            result = liveness.check_pointer(
                "url", "https://nonexistent.example/abc", cache_path=self.cache_path
            )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["http_code"], 404)

    def test_request_error_is_fail(self) -> None:
        with patch.object(httpx, "head", side_effect=httpx.RequestError("connection refused")):
            result = liveness.check_pointer(
                "url", "https://broken.example/", cache_path=self.cache_path
            )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["http_code"], 0)

    def test_invalid_kind_raises(self) -> None:
        with self.assertRaises(liveness.InvalidPointerKind):
            liveness.check_pointer("blog", "https://example.com/", cache_path=self.cache_path)

    def test_405_falls_back_to_get(self) -> None:
        with patch.object(httpx, "head", return_value=_FakeResponse(405)):
            with patch.object(httpx, "get", return_value=_FakeResponse(200)) as mock_get:
                result = liveness.check_pointer(
                    "arxiv", "1234.56789", cache_path=self.cache_path
                )
        self.assertEqual(result["status"], "pass")
        mock_get.assert_called_once()


class TestCacheIO(unittest.TestCase):
    def test_load_empty_cache(self) -> None:
        with TemporaryDirectory() as d:
            p = Path(d) / "cache.json"
            self.assertEqual(liveness._load_cache(p), {})

    def test_load_corrupt_cache_returns_empty(self) -> None:
        with TemporaryDirectory() as d:
            p = Path(d) / "cache.json"
            p.write_text("{not valid json")
            self.assertEqual(liveness._load_cache(p), {})

    def test_save_creates_parent(self) -> None:
        with TemporaryDirectory() as d:
            p = Path(d) / "nested" / "subdir" / "cache.json"
            liveness._save_cache({"foo": {"status": "pass"}}, p)
            self.assertTrue(p.exists())


if __name__ == "__main__":
    unittest.main()
