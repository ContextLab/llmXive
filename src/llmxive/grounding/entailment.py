"""Passage location + LLM entailment for full-text claim grounding."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from llmxive.agents.grounding_guard import _number_anchor_re  # reuse number forms
from llmxive.agents.prompts import load_prompt
from llmxive.librarian.verify import jaccard_tokens

logger = logging.getLogger(__name__)

_ENTAILMENT_BLOCK = "agents/prompts/_shared/claim_entailment_block.md"
_REASONING_MAX_TOKENS = 131_072
_DEFAULT_MODEL = "qwen.qwen3.5-122b"
_WINDOW = 320  # chars on each side of an anchor
_MAX_PASSAGES = 5
_SENT_RE = re.compile(r"[^.!?\n]+[.!?]?")

Status = Literal["grounded", "contradicted", "not_found"]


@dataclass(frozen=True, slots=True)
class Verdict:
    status: Status
    evidence: str = ""
    note: str = ""


def locate_passages(full_text: str, *, claim: str, number: str | None) -> list[str]:
    """Return up to _MAX_PASSAGES bounded windows likely to bear on the claim:
    windows around each occurrence of the claim's number, then the
    highest-token-overlap sentences. De-duplicated, order-preserving."""
    text = full_text or ""
    out: list[str] = []

    if number:
        anchor = _number_anchor_re(number)
        if anchor is not None:
            for m in anchor.finditer(text):
                lo, hi = max(0, m.start() - _WINDOW), min(len(text), m.end() + _WINDOW)
                out.append(text[lo:hi].strip())
                if len(out) >= _MAX_PASSAGES:
                    break

    if len(out) < _MAX_PASSAGES:
        sents = [s.strip() for s in _SENT_RE.findall(text) if len(s.strip()) > 20]
        ranked = sorted(sents, key=lambda s: jaccard_tokens(claim, s), reverse=True)
        for s in ranked:
            if jaccard_tokens(claim, s) <= 0.0:
                break
            if not any(s in p for p in out):
                out.append(s)
            if len(out) >= _MAX_PASSAGES:
                break

    # de-dup while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for p in out:
        if p and p not in seen:
            seen.add(p)
            deduped.append(p)
    return deduped[:_MAX_PASSAGES]


def _parse_verdict(reply: str) -> Verdict:
    import yaml

    raw = (reply or "").strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    try:
        obj = yaml.safe_load(raw)
    except Exception:
        obj = None
    if not isinstance(obj, dict):
        return Verdict("not_found", "", "unparseable verdict")
    raw_status = str(obj.get("status", "")).strip().lower()
    status: Status = (
        cast(Status, raw_status)
        if raw_status in ("grounded", "contradicted", "not_found")
        else "not_found"
    )
    return Verdict(status, str(obj.get("evidence") or ""), str(obj.get("note") or ""))


def _chat_reasoning_safe(backend: Any, messages: list[Any], model: str | None) -> Any:
    kwargs: dict[str, Any] = {"max_tokens": _REASONING_MAX_TOKENS}
    if model is not None:
        kwargs["model"] = model
    try:
        return backend.chat(messages, **kwargs)
    except TypeError:
        kwargs.pop("max_tokens", None)
        try:
            return backend.chat(messages, **kwargs)
        except TypeError:
            return backend.chat(messages)


def assess(claim: str, doc: Any, *, backend: Any, model: str | None,
           repo_root: Path | None = None) -> Verdict:
    """One LLM entailment call over the located passages of the source text.
    On any backend/parse error returns not_found (caller flags — no silent pass)."""
    from llmxive.backends.base import ChatMessage
    from llmxive.config import repo_root as _rr

    source_text = doc.full_text or doc.abstract or ""
    if not source_text.strip():
        return Verdict("not_found", "", "no source text")
    number = _extract_claim_number(claim)
    passages = locate_passages(source_text, claim=claim, number=number)
    if not passages:
        return Verdict("not_found", "", "no relevant passages")
    block = load_prompt(_ENTAILMENT_BLOCK, repo_root=repo_root or _rr())
    joined = "\n\n---\n\n".join(passages)
    messages = [
        ChatMessage(role="system", content=block),
        ChatMessage(role="user",
                    content=f"# CLAIM\n{claim}\n\n# PASSAGES\n{joined}\n\n"
                            "Return the single YAML verdict."),
    ]
    try:
        resp = _chat_reasoning_safe(backend, messages, model or _DEFAULT_MODEL)
        reply = getattr(resp, "text", "") or ""
        if not reply.strip():
            raise ValueError("empty entailment reply")
        return _parse_verdict(reply)
    except Exception as exc:
        logger.warning("grounding assess: entailment failed (%s); -> not_found", exc)
        return Verdict("not_found", "", f"entailment error: {type(exc).__name__}")


_CLAIM_NUM_RE = re.compile(r"[-+]?\d[\d,_ ]*(?:\.\d+)?")


def _extract_claim_number(claim: str) -> str | None:
    m = _CLAIM_NUM_RE.search(claim or "")
    return m.group(0).strip() if m else None
