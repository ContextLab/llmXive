"""LLM math-classifier for the librarian (spec 006, amends spec 005).

Decides whether a research question is a **pure-mathematics theorem /
proof / formal-structure question** — the kind for which TheoremSearch
(a semantic search over theorem *statements*) is a useful third
candidate source alongside Semantic Scholar and arXiv.

This module is consulted **only** for projects whose field is NOT in
``{"mathematics", "statistics"}`` — those two fields query TheoremSearch
unconditionally and skip the classifier entirely (the librarian sets a
``{"invoked": False, ...}`` audit object directly). For every other
field, ``LibrarianAgent.invoke()`` calls ``classify(...)`` once: a math
verdict turns on a TheoremSearch query for that invocation.

Design (per ``specs/006-theoremsearch-backend/contracts/math-classifier.md``):
  - **Per-project verdict cache** at
    ``state/librarian-cache/math-classifier-verdicts.json`` keyed
    ``f"{project_id}::{librarian_prompt_version}"`` — a re-run on the
    same project under the same prompt version replays the verdict with
    NO LLM call. ``project_id is None`` (standalone smoke tests) → no
    cache read/write.
  - **Fail open to False** on a backend failure (router raises, all
    fallbacks exhausted, timeout, …) — the librarian must still complete
    on SS+arXiv, so a classifier outage degrades to "non-math" rather
    than hard-failing. A backend failure emits a *loud* stderr
    diagnostic (matching the ``[arxiv]`` / ``[query-extractor]`` logging
    style) and sets ``error``; error outcomes are NOT cached (a transient
    blip shouldn't poison the cache — the next run retries).
  - An **unparseable-but-returned** response also fails open
    (``verdict=False``) but with ``error=None`` + a logged warning —
    distinct from a backend failure.

Constitution Principle I: the classifier is plumbing inside the
librarian, not a competing agent. It chooses *whether* to consult a
backend; the librarian remains the single verifier.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import json
import logging
import sys
from pathlib import Path

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage
from llmxive.backends.router import chat_with_fallback

LOGGER = logging.getLogger(__name__)

MATH_CLASSIFIER_PROMPT_PATH = "agents/prompts/math_classifier.md"
_VERDICT_CACHE_RELPATH = ("state", "librarian-cache", "math-classifier-verdicts.json")


@dataclasses.dataclass(frozen=True)
class MathClassifierResult:
    """Outcome of one math-classifier decision (data-model.md E-TS3).

    ``cached`` is in-memory only — it is dropped when this is serialized
    into the ``math_classifier`` audit object on ``LibrarianResult``.
    """

    invoked: bool
    verdict: bool | None
    error: str | None
    cached: bool


# --- verdict cache --------------------------------------------------------


def _verdict_cache_path(repo_root: Path) -> Path:
    return repo_root.joinpath(*_VERDICT_CACHE_RELPATH)


def _read_verdict_cache(repo_root: Path) -> dict[str, dict[str, object]]:
    """Load the flat verdict-cache dict; absent/malformed → ``{}`` (logged)."""
    path = _verdict_cache_path(repo_root)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        LOGGER.warning(
            "[math-classifier] malformed verdict cache %s (%s); treating as empty",
            path,
            exc,
        )
        return {}
    if not isinstance(data, dict):
        LOGGER.warning(
            "[math-classifier] verdict cache %s is not a JSON object; treating as empty",
            path,
        )
        return {}
    return data


def _write_verdict_cache_entry(repo_root: Path, key: str, verdict: bool) -> None:
    """Merge-write one ``{key: {"verdict": ..., "classified_at": ...}}`` entry."""
    path = _verdict_cache_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _read_verdict_cache(repo_root)
    data[key] = {
        "verdict": bool(verdict),
        "classified_at": _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


# --- response parsing -----------------------------------------------------


def _parse_verdict(text: str) -> bool | None:
    """First non-empty line, uppercased: ``YES…`` → True, ``NO…`` → False,
    anything else → ``None`` (unparseable).
    """
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        upper = stripped.upper()
        if upper.startswith("YES"):
            return True
        if upper.startswith("NO"):
            return False
        return None
    return None


# --- public API -----------------------------------------------------------


def classify(
    question: str,
    idea_body_excerpt: str | None,
    *,
    project_id: str | None,
    librarian_prompt_version: str,
    model: str,
    default_backend: str,
    fallback_backends: list[str],
    repo_root: Path | None = None,
) -> MathClassifierResult:
    """Decide whether ``question`` is a pure-math theorem/proof/formal-structure
    question. See module docstring for caching + failure semantics.
    """
    repo_root = repo_root or Path.cwd()

    # 1. Cache check (only when we have a project to key on).
    cache_key: str | None = None
    if project_id is not None:
        cache_key = f"{project_id}::{librarian_prompt_version}"
        cached = _read_verdict_cache(repo_root).get(cache_key)
        if isinstance(cached, dict) and "verdict" in cached:
            return MathClassifierResult(
                invoked=True,
                verdict=bool(cached["verdict"]),
                error=None,
                cached=True,
            )

    # 2. LLM call. The prompt template is a committed package asset (it
    # lives next to this module's source tree), NOT under the caller's
    # ``repo_root`` — load it with the package default so a caller passing
    # a scratch ``repo_root`` (e.g. for cache isolation in tests) still
    # finds the prompt.
    excerpt = (idea_body_excerpt or "").strip() or "(none provided)"
    system_prompt = render_prompt(MATH_CLASSIFIER_PROMPT_PATH, {})
    user_payload = (
        f"# Research question\n\n{(question or '').strip()}\n\n"
        f"# Idea body excerpt\n\n{excerpt}\n\n"
        "# Task\n\nReply `YES` or `NO` on the first line, then a one-sentence "
        "rationale on the second line. Nothing else."
    )
    try:
        response = chat_with_fallback(
            [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_payload),
            ],
            default_backend=default_backend,
            fallback_backends=list(fallback_backends),
            model=model,
        )
    except Exception as exc:  # fail open by design — librarian must proceed on SS+arXiv
        msg = str(exc)
        print(
            f"[math-classifier] backend failure; treating question as non-math "
            f"(TheoremSearch skipped): {msg}",
            file=sys.stderr,
        )
        LOGGER.warning("[math-classifier] backend failure (fail-open to non-math): %s", msg)
        return MathClassifierResult(invoked=True, verdict=False, error=msg, cached=False)

    verdict = _parse_verdict(response.text)
    if verdict is None:
        snippet = (response.text or "").strip().replace("\n", " ")[:80]
        LOGGER.warning(
            "[math-classifier] unparseable response, defaulting to non-math: %s",
            snippet,
        )
        return MathClassifierResult(invoked=True, verdict=False, error=None, cached=False)

    # 3. Cache write (fresh successful verdict + a project to key on).
    if cache_key is not None:
        try:
            _write_verdict_cache_entry(repo_root, cache_key, verdict)
        except OSError as exc:
            LOGGER.warning("[math-classifier] could not write verdict cache: %s", exc)

    return MathClassifierResult(invoked=True, verdict=verdict, error=None, cached=False)


def is_math_theory_question(
    question: str,
    idea_body_excerpt: str | None = None,
    *,
    project_id: str | None = None,
    librarian_prompt_version: str = "0.0.0",
    model: str = "qwen.qwen3.5-122b",
    default_backend: str = "dartmouth",
    fallback_backends: list[str] | None = None,
    repo_root: Path | None = None,
) -> bool:
    """Thin convenience wrapper: ``classify(...).verdict or False``."""
    return bool(
        classify(
            question,
            idea_body_excerpt,
            project_id=project_id,
            librarian_prompt_version=librarian_prompt_version,
            model=model,
            default_backend=default_backend,
            fallback_backends=list(fallback_backends or ("local",)),
            repo_root=repo_root,
        ).verdict
    )


__all__ = [
    "MATH_CLASSIFIER_PROMPT_PATH",
    "MathClassifierResult",
    "classify",
    "is_math_theory_question",
]
