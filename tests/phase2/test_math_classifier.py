"""Tests for the LLM math-classifier (spec 006 / contracts/math-classifier.md).

Pure-function parser tests + verdict-cache behavior (via a recording
backend, no real LLM) + a real-LLM smoke gated on
DARTMOUTH_CHAT_API_KEY + LLMXIVE_REAL_TESTS so CI without the key passes.

Per Constitution Principle III: the cache + parse + fail-open paths run
the real code; only `chat_with_fallback` is monkeypatched in the offline
tests. The gated smoke makes a real call.
"""

from __future__ import annotations

import json
import os

import pytest

from llmxive.credentials import load_dartmouth_key
from llmxive.librarian import math_classifier as mc
from llmxive.librarian.math_classifier import (
    MathClassifierResult,
    _parse_verdict,
    classify,
)

HAS_DM_KEY = bool(load_dartmouth_key(prompt_if_missing=False))
REAL = os.environ.get("LLMXIVE_REAL_TESTS") == "1"


# --- test double: recording backend --------------------------------------


class _RecordingBackend:
    """Stand-in for `chat_with_fallback`: returns a canned text and counts
    calls. If ``raise_exc`` is set, raises it instead.
    """

    def __init__(self, text: str = "YES\nbecause it's a theorem question", raise_exc: Exception | None = None):
        self.text = text
        self.raise_exc = raise_exc
        self.calls = 0

    def __call__(self, messages, *, default_backend, fallback_backends, model):
        self.calls += 1
        if self.raise_exc is not None:
            raise self.raise_exc

        class _Resp:
            pass

        r = _Resp()
        r.text = self.text
        return r


def _patch_backend(monkeypatch, backend: _RecordingBackend) -> _RecordingBackend:
    monkeypatch.setattr(mc, "chat_with_fallback", backend)
    return backend


_PLUMBING = dict(
    model="qwen.qwen3.5-122b",
    default_backend="dartmouth",
    fallback_backends=["local"],
)


# --- T022: parser ---------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("YES\nbecause it's about a theorem", True),
        ("yes — sure", True),
        ("  YES  ", True),
        ("NO\nit's an empirical ML question", False),
        ("no", False),
        ("\n\nNO, definitely not", False),
        ("hmm, maybe?", None),
        ("", None),
        ("Affirmative.", None),
    ],
)
def test_parse_verdict(text, expected) -> None:
    assert _parse_verdict(text) is expected


def test_classify_parses_yes(monkeypatch, tmp_path) -> None:
    _patch_backend(monkeypatch, _RecordingBackend("YES\nbecause it's a theorem"))
    res = classify(
        "what is the sharp constant in the Sobolev inequality",
        None,
        project_id=None,
        librarian_prompt_version="1.6.0",
        repo_root=tmp_path,
        **_PLUMBING,
    )
    assert isinstance(res, MathClassifierResult)
    assert res == MathClassifierResult(invoked=True, verdict=True, error=None, cached=False)


def test_classify_parses_no(monkeypatch, tmp_path) -> None:
    _patch_backend(monkeypatch, _RecordingBackend("NO\nempirical question"))
    res = classify("does data scaling improve calibration", None, project_id=None,
                   librarian_prompt_version="1.6.0", repo_root=tmp_path, **_PLUMBING)
    assert res.verdict is False
    assert res.error is None
    assert res.invoked is True


def test_classify_unparseable_fails_open(monkeypatch, tmp_path, caplog) -> None:
    _patch_backend(monkeypatch, _RecordingBackend("I'm not sure, could be either"))
    res = classify("ambiguous", None, project_id=None,
                   librarian_prompt_version="1.6.0", repo_root=tmp_path, **_PLUMBING)
    assert res == MathClassifierResult(invoked=True, verdict=False, error=None, cached=False)
    assert any("unparseable" in r.message for r in caplog.records)


# --- T023: cache behavior + backend-failure path -------------------------


def test_cache_hit_skips_llm(monkeypatch, tmp_path) -> None:
    be = _patch_backend(monkeypatch, _RecordingBackend("YES\nfirst call computes"))
    kw = dict(project_id="PROJ-999-test", librarian_prompt_version="1.6.0",
              repo_root=tmp_path, **_PLUMBING)
    r1 = classify("a theorem question", None, **kw)
    assert r1.verdict is True and r1.cached is False and be.calls == 1
    # The cache file now exists with the verdict.
    cache_file = tmp_path / "state" / "librarian-cache" / "math-classifier-verdicts.json"
    assert cache_file.exists()
    data = json.loads(cache_file.read_text())
    assert data["PROJ-999-test::1.6.0"]["verdict"] is True
    # Second call → served from cache, NO LLM call.
    r2 = classify("a theorem question", None, **kw)
    assert r2 == MathClassifierResult(invoked=True, verdict=True, error=None, cached=True)
    assert be.calls == 1  # unchanged


def test_cache_miss_on_prompt_version_change(monkeypatch, tmp_path) -> None:
    be = _patch_backend(monkeypatch, _RecordingBackend("YES\n..."))
    classify("q", None, project_id="PROJ-1-x", librarian_prompt_version="1.6.0",
             repo_root=tmp_path, **_PLUMBING)
    assert be.calls == 1
    # Different prompt version → different key → re-classifies.
    classify("q", None, project_id="PROJ-1-x", librarian_prompt_version="1.7.0",
             repo_root=tmp_path, **_PLUMBING)
    assert be.calls == 2


def test_project_id_none_never_caches(monkeypatch, tmp_path) -> None:
    be = _patch_backend(monkeypatch, _RecordingBackend("NO\n..."))
    for _ in range(3):
        classify("q", None, project_id=None, librarian_prompt_version="1.6.0",
                 repo_root=tmp_path, **_PLUMBING)
    assert be.calls == 3
    assert not (tmp_path / "state" / "librarian-cache" / "math-classifier-verdicts.json").exists()


def test_malformed_cache_treated_as_empty(monkeypatch, tmp_path, caplog) -> None:
    cache_file = tmp_path / "state" / "librarian-cache" / "math-classifier-verdicts.json"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_text("{ this is not valid json")
    be = _patch_backend(monkeypatch, _RecordingBackend("YES\n..."))
    res = classify("q", None, project_id="PROJ-2-y", librarian_prompt_version="1.6.0",
                   repo_root=tmp_path, **_PLUMBING)
    assert res.verdict is True and be.calls == 1
    assert any("malformed" in r.message for r in caplog.records)
    # The malformed file was overwritten with a valid one containing the new entry.
    data = json.loads(cache_file.read_text())
    assert data["PROJ-2-y::1.6.0"]["verdict"] is True


def test_backend_failure_fails_open_loudly_and_does_not_cache(monkeypatch, tmp_path, capsys) -> None:
    be = _patch_backend(monkeypatch, _RecordingBackend(raise_exc=RuntimeError("router exhausted")))
    res = classify("q", None, project_id="PROJ-3-z", librarian_prompt_version="1.6.0",
                   repo_root=tmp_path, **_PLUMBING)
    assert res.invoked is True and res.verdict is False
    assert res.error == "router exhausted"
    assert res.cached is False
    # Loud stderr diagnostic.
    err = capsys.readouterr().err
    assert "[math-classifier]" in err and "treating question as non-math" in err
    # No exception propagated; cache NOT written (error outcomes don't poison it).
    assert not (tmp_path / "state" / "librarian-cache" / "math-classifier-verdicts.json").exists()
    assert be.calls == 1


# --- T024: real-LLM smoke ------------------------------------------------


@pytest.mark.skipif(not (HAS_DM_KEY and REAL), reason="needs DARTMOUTH_CHAT_API_KEY + LLMXIVE_REAL_TESTS=1")
def test_real_llm_smoke(tmp_path) -> None:
    # A plainly-math question → YES.
    r_math = classify(
        "what is the tightest known concentration inequality for sums of bounded "
        "independent random variables, and in which paper is it proved?",
        None,
        project_id=None,
        librarian_prompt_version="1.6.0",
        repo_root=tmp_path,
        **_PLUMBING,
    )
    assert r_math.error is None, r_math
    assert r_math.verdict is True, r_math

    # A plainly-non-math question → NO.
    r_emp = classify(
        "how does code-clone density correlate with LLM perplexity on Python?",
        None,
        project_id=None,
        librarian_prompt_version="1.6.0",
        repo_root=tmp_path,
        **_PLUMBING,
    )
    assert r_emp.error is None, r_emp
    assert r_emp.verdict is False, r_emp
