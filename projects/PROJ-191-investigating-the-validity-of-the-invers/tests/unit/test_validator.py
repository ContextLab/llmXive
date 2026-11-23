"""Unit tests for the arXiv ID validator (T013-VALIDATE-IDS).

Network calls are mocked so the tests are deterministic and offline.
"""
import unittest
from unittest.mock import patch, MagicMock

import requests
import sys
from pathlib import Path

    # Ensure the code directory is importable
CODE_ROOT = Path(__file__).resolve().parents[2] / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from data.validator import validate_arxiv_id, validate_required_ids

VALID_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2106.08611v2</id>
    <title>Dynamical measurements of deviations from Newton's 1/r^2 law</title>
  </entry>
</feed>"""

EMPTY_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
</feed>"""

def _mock_response(text, status_code=200):
    resp = MagicMock()
    resp.text = text
    resp.status_code = status_code
    return resp

class TestValidateArxivId(unittest.TestCase):
    def test_valid_id_returns_true(self):
        with patch("data.validator.requests.get",
                   return_value=_mock_response(VALID_RESPONSE)):
            self.assertTrue(validate_arxiv_id("2106.08611"))

    def test_arxiv_prefix_is_stripped(self):
        with patch("data.validator.requests.get",
                   return_value=_mock_response(VALID_RESPONSE)) as mock_get:
            self.assertTrue(validate_arxiv_id("arXiv:2106.08611"))
            self.assertEqual(
                mock_get.call_args.kwargs["params"]["id_list"], "2106.08611")

    def test_missing_entry_raises(self):
        with patch("data.validator.requests.get",
                   return_value=_mock_response(EMPTY_RESPONSE)):
            with self.assertRaises(RuntimeError):
                validate_arxiv_id("9999.99999")

    def test_unreachable_raises(self):
        with patch(
            "data.validator.requests.get",
            side_effect=requests.exceptions.ConnectionError("down"),
        ):
            with self.assertRaises(RuntimeError):
                validate_arxiv_id("2106.08611")

    def test_bad_http_status_raises(self):
        with patch("data.validator.requests.get",
                   return_value=_mock_response("err", status_code=503)):
            with self.assertRaises(RuntimeError):
                validate_arxiv_id("2106.08611")

    def test_malformed_xml_raises(self):
        with patch("data.validator.requests.get",
                   return_value=_mock_response("<not-xml")):
            with self.assertRaises(RuntimeError):
                validate_arxiv_id("2106.08611")

    def test_empty_id_raises(self):
        with self.assertRaises(RuntimeError):
            validate_arxiv_id("arXiv:   ")

    def test_validate_required_ids(self):
        with patch("data.validator.requests.get",
                   return_value=_mock_response(VALID_RESPONSE)):
            results = validate_required_ids()
            self.assertEqual(
                sorted(results.keys()),
                ["2106.08611", "2305.06325"])
            self.assertTrue(all(results.values()))

if __name__ == "__main__":
    unittest.main()