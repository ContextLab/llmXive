"""
tests/unit/test_data_loader.py
------------------------------

Unit tests for the ``verify_urls`` function (task T001a) implemented in
``code/utils/data_loader.py`` (with the ``exponential_backoff`` decorator
from ``code/pipeline/loader.py``), plus the ``download_and_checksum``
helper tests (task T001b) implemented in ``code/pipeline/loader.py``.

All HTTP interactions for the URL-verification tests are mocked via
``monkeypatch`` so that no real network traffic occurs and the
exponential-back-off sleeps (30 s initial delay) do not stall the test
run.  The retry behaviour mandated by FR-011 (initial wait = 30 s,
max 5 retries) is verified by counting calls and inspecting the
(suppressed) sleep durations.
"""

import os
import sys

import pytest
import requests


# ----------------------------------------------------------------------
# Import bootstrap: locate the project's ``code/`` directory (the parent
# package root that contains ``utils/`` and ``pipeline/``) and put it on
# ``sys.path`` so the sibling modules can be imported regardless of the
# directory pytest was invoked from.
# ----------------------------------------------------------------------
def _find_code_root():
    here = os.path.dirname(os.path.abspath(__file__))
    candidate = here
    for _ in range(6):
        if os.path.isfile(os.path.join(candidate, "pipeline", "loader.py")):
            return candidate
        # also allow the layout where tests live under ``code/tests/``
        sub = os.path.join(candidate, "code")
        if os.path.isfile(os.path.join(sub, "pipeline", "loader.py")):
            return sub
        candidate = os.path.dirname(candidate)
    raise ImportError(
        "Could not locate the project 'code' directory containing "
        "pipeline/loader.py from " + here
    )


_CODE_ROOT = _find_code_root()
if _CODE_ROOT not in sys.path:
    sys.path.insert(0, _CODE_ROOT)

from utils.data_loader import verify_urls  # noqa: E402
from pipeline.loader import download_and_checksum, calculate_directory_checksum  # noqa: E402
import pipeline.loader as _pl  # noqa: E402


# ----------------------------------------------------------------------
# Helpers: a fake ``requests`` response and a recording ``requests.head``.
# ----------------------------------------------------------------------
class _FakeResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(
                f"{self.status_code} Error for url"
            )


def _install_head(monkeypatch, behaviours):
    """Patch ``requests.head`` with a scripted sequence of behaviours.

    ``behaviours`` is a list whose entries are either an HTTP status code
    (int) or an ``Exception`` instance to raise.  Each call consumes one
    entry; a ``RuntimeError`` is raised if the script is exhausted.
    Returns a list recording the URLs requested.
    """
    calls = []
    it = iter(behaviours)

    def fake_head(url, timeout=5, allow_redirects=True):
        calls.append(url)
        try:
            entry = next(it)
        except StopIteration:
            raise RuntimeError("unexpected extra request to " + url)
        if isinstance(entry, Exception):
            raise entry
        return _FakeResponse(entry)

    monkeypatch.setattr(requests, "head", fake_head)
    return calls


def _suppress_sleeps(monkeypatch):
    """Replace ``time.sleep`` used by the back-off decorator with a recorder.

    Returns the list that collects the requested sleep durations so tests
    can assert the FR-011 back-off schedule without actually waiting.
    """
    sleeps = []
    monkeypatch.setattr(_pl.time, "sleep", lambda s: sleeps.append(s))
    return sleeps


# ----------------------------------------------------------------------
# verify_urls tests (T001a)
# ----------------------------------------------------------------------
def test_verify_urls_success(monkeypatch):
    """All reachable URLs -> True, one HEAD request per URL, no retries."""
    urls = [
        "https://example.com/dataset1",
        "https://example.org/data2",
    ]
    calls = _install_head(monkeypatch, [200, 200])
    sleeps = _suppress_sleeps(monkeypatch)

    assert verify_urls(urls) is True
    assert calls == urls  # each URL probed exactly once, in order
    assert sleeps == []   # no retries were needed


def test_verify_urls_empty_list(monkeypatch):
    """An empty URL list is trivially verified."""
    calls = _install_head(monkeypatch, [])
    assert verify_urls([]) is True
    assert calls == []


def test_verify_urls_failure_raises(monkeypatch):
    """An unreachable URL raises ValueError naming the URL after retries."""
    urls = [
        "https://example.com/ok",
        "https://example.org/missing",
    ]
    # First URL succeeds; the second persistently returns 404.
    calls = _install_head(monkeypatch, [200] + [404] * 6)
    sleeps = _suppress_sleeps(monkeypatch)

    with pytest.raises(ValueError) as excinfo:
        verify_urls(urls)

    # The error message must identify the failing URL.
    assert urls[1] in str(excinfo.value)

    # The failing URL is retried up to the maximum defined by the
    # exponential_backoff decorator: 1 initial attempt + 5 retries = 6.
    failing_calls = [u for u in calls if u == urls[1]]
    assert len(failing_calls) == 6
    # The successful URL was only probed once.
    assert calls.count(urls[0]) == 1


def test_verify_urls_backoff_schedule(monkeypatch):
    """FR-011: retries use an initial wait of 30 s that doubles each time."""
    url = "https://example.com/flaky"
    _install_head(monkeypatch, [503] * 6)
    sleeps = _suppress_sleeps(monkeypatch)

    with pytest.raises(ValueError):
        verify_urls([url])

    # 5 retries -> 5 sleep calls.  Each sleep is the current delay
    # (30, 60, 120, 240, 480) plus a jitter of up to 10% of the delay.
    assert len(sleeps) == 5
    base_delays = [30, 60, 120, 240, 480]
    for slept, base in zip(sleeps, base_delays):
        assert base <= slept <= base * 1.1


def test_verify_urls_transient_error_then_success(monkeypatch):
    """A transient network error is retried and then succeeds."""
    url = "https://example.com/transient"
    calls = _install_head(
        monkeypatch,
        [requests.ConnectionError("connection reset"), 200],
    )
    sleeps = _suppress_sleeps(monkeypatch)

    assert verify_urls([url]) is True
    assert calls == [url, url]  # one failure, one successful retry
    assert len(sleeps) == 1     # a single back-off wait occurred
    assert 30 <= sleeps[0] <= 33  # initial delay ~30 s (+ jitter)


# ----------------------------------------------------------------------
# download_and_checksum tests (T001b)
# ----------------------------------------------------------------------
def test_download_and_checksum_writes_sha256(tmp_path):
    """
    Verify that ``download_and_checksum``:
    1. Downloads a real HuggingFace dataset (a tiny public dataset).
    2. Returns a 64-character SHA-256 hex digest.
    3. Writes a ``SHA256SUM`` file alongside the downloaded data.
    4. The checksum recorded in the file matches the directory checksum
       computed independently.
    """
    # Use a very small dataset to keep test runtime low.
    dataset_name = "ag_news"  # small, hosted on the HuggingFace Hub
    dest_dir = tmp_path / "ag_news"

    checksum = download_and_checksum(dataset_name, str(dest_dir))

    # A SHA-256 string was returned.
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 hex digest length

    # The SHA256SUM file must exist and be non-empty.
    sha_file = dest_dir / "SHA256SUM"
    assert sha_file.is_file()
    file_content = sha_file.read_text().strip()
    assert file_content, "SHA256SUM file should contain the checksum"

    # The recorded checksum matches the independently computed
    # directory checksum.
    dir_checksum = calculate_directory_checksum(str(dest_dir))
    assert file_content == dir_checksum
    assert checksum == dir_checksum


def test_download_and_checksum_is_idempotent(tmp_path):
    """A second call with an existing SHA256SUM returns the cached value."""
    dataset_name = "ag_news"
    dest_dir = tmp_path / "ag_news"

    first = download_and_checksum(dataset_name, str(dest_dir))

    # Corrupt nothing, just call again: the cached checksum is returned
    # without re-downloading (the call is fast and returns same value).
    second = download_and_checksum(dataset_name, str(dest_dir))
    assert first == second