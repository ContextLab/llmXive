"""sniff_format must survive a RAW urllib3 read-timeout, not crash the run.

Live PROJ-492 run-22 failure: verifying a cited Hugging Face dataset hit
``HTTPSConnectionPool(host='us.aws.cdn.hf.co'): Read timed out`` during
``r.raw.read`` — a urllib3 ReadTimeoutError, which is NOT a requests.RequestException
NOR an OSError, so the old ``except (requests.RequestException, OSError)`` missed it
and the timeout propagated all the way to ``[run] FAIL``, killing the whole
pipeline run. Verifying a dataset URL is best-effort: a transient network failure
must yield a "couldn't verify" FormatReport, never an exception.
"""

from __future__ import annotations

from unittest import mock

import urllib3

from llmxive.librarian import dataset_resolver as dr


class _RaisingRaw:
    def read(self, *a, **k):
        raise urllib3.exceptions.ReadTimeoutError(None, "u", "Read timed out")


class _Resp:
    status_code = 200
    raw = _RaisingRaw()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_sniff_format_survives_raw_urllib3_read_timeout() -> None:
    with mock.patch.object(dr.requests, "get", return_value=_Resp()):
        rep = dr.sniff_format("https://us.aws.cdn.hf.co/some/dataset")
    assert rep.parsed is False
    assert rep.format is None
    assert "Read timed out" in (rep.error or "")


def test_sniff_format_survives_requests_and_os_errors() -> None:
    """Regression: the originally-handled error classes still don't crash."""
    import requests

    for exc in (requests.exceptions.ConnectionError("boom"), OSError("socket")):
        with mock.patch.object(dr.requests, "get", side_effect=exc):
            rep = dr.sniff_format("https://example.com/x")
        assert rep.parsed is False
