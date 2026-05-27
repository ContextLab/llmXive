"""Backend router (T020) — falls back through a chain on transient errors.

The agent registry declares a default backend and an ordered list of
fallback backends per agent. The router is configured per-call from
those declarations.
"""

from __future__ import annotations

from typing import Iterable

from llmxive.backends.base import (
    BaseBackend,
    BackendError,
    ChatMessage,
    ChatResponse,
    PermanentBackendError,
    TransientBackendError,
)
from llmxive.backends.dartmouth import DartmouthBackend
from llmxive.backends.huggingface import HuggingFaceBackend
from llmxive.backends.local import LocalBackend


_REGISTRY: dict[str, type[BaseBackend]] = {
    "dartmouth": DartmouthBackend,
    "huggingface": HuggingFaceBackend,
    "local": LocalBackend,
}


def make_backend(name: str) -> BaseBackend:
    cls = _REGISTRY.get(name)
    if cls is None:
        raise PermanentBackendError(f"unknown backend: {name!r}")
    return cls()  # type: ignore[call-arg]


# Per-backend model-fallback chain. When the primary model on a
# backend hits transient errors after retries, try these models in
# order before falling through to the next backend. This keeps
# pipeline runs alive when one Dartmouth-hosted model has a vLLM
# outage but other models on the same backend are healthy.
MODEL_FALLBACKS: dict[str, list[str]] = {
    # Qwen 3.5 122b is a reasoning model; gpt-oss-120b is the closest
    # peer in capability (also reasoning-capable, similar parameter count).
    # gemma-4-31B-it is the free general fallback. All three are free
    # (cost-per-token == 0) per chat.dartmouth.edu/api/models.
    "qwen.qwen3.5-122b": ["openai.gpt-oss-120b", "google.gemma-4-31B-it"],
    "openai.gpt-oss-120b": ["qwen.qwen3.5-122b", "google.gemma-4-31B-it"],
    "google.gemma-4-31B-it": ["openai.gpt-oss-120b", "qwen.qwen3.5-122b"],
}


def chat_with_fallback(
    messages: Iterable[ChatMessage],
    *,
    default_backend: str,
    fallback_backends: list[str],
    model: str,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> ChatResponse:
    """Try default backend; on TransientBackendError, walk the fallback chain.

    If `max_tokens` is None we default to 8192 — Spec Kit agents (Tasker,
    Specifier, Planner, paper-writers) frequently exceed the per-model
    silent default (often 1024) and produce truncated output otherwise.

    Per backend, retries the requested `model` 3x. On persistent
    transient errors, tries each model in MODEL_FALLBACKS[model] (1
    attempt each) on the SAME backend before falling through to the
    next backend. This handles single-model vLLM outages on Dartmouth
    where other models on the same backend are still healthy.
    """
    import time as _time

    if max_tokens is None:
        # 32K default — tokens cost time but not money on Dartmouth's
        # community plan, so we use the largest sensible budget.
        # Implementer artifacts are full files (model classes,
        # baselines, integration tests) that frequently exceeded 8K
        # and got truncated mid-dict producing SyntaxError. 32K covers
        # essentially all single-file outputs (qwen3.5-122b 32K ctx,
        # gpt-oss-120b and gemma-3-27b-it have 128K ctx so headroom
        # for the prompt is plenty).
        max_tokens = 32768
    chain = [default_backend, *fallback_backends]
    errors: list[str] = []
    msg_list = list(messages)
    for name in chain:
        try:
            backend = make_backend(name)
        except PermanentBackendError as exc:
            errors.append(f"{name}(init): {exc}")
            continue
        # Try the primary model with retries, then fall back through
        # peer models on the same backend.
        models_to_try = [model] + [m for m in MODEL_FALLBACKS.get(model, []) if m != model]
        for model_idx, m in enumerate(models_to_try):
            attempts = 3 if model_idx == 0 else 1
            permanent_for_this_model = False
            for attempt in range(attempts):
                if attempt:
                    _time.sleep(2.0 * attempt)
                try:
                    return backend.chat(
                        msg_list,
                        model=m,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                except TransientBackendError as exc:
                    errors.append(
                        f"{name}/{m}(transient attempt {attempt + 1}): {exc}"
                    )
                    # "Reasoning budget exhausted" means the SAME model
                    # will exhaust its budget AGAIN on retry — skip
                    # remaining same-model attempts and fall straight
                    # to peer-model fallback. Saves up to 2x3min=6min
                    # per call.
                    if "reasoning budget exhausted" in str(exc):
                        break
                    if attempt == attempts - 1:
                        break  # done with this model, try next
                    continue
                except PermanentBackendError as exc:
                    errors.append(f"{name}/{m}(permanent): {exc}")
                    permanent_for_this_model = True
                    break  # don't retry permanent failures
            # If permanent failure on the PRIMARY model (e.g., auth issue),
            # don't bother trying peer models on the same backend.
            if permanent_for_this_model and model_idx == 0:
                break
    raise BackendError(
        "every backend in chain "
        + repr(chain)
        + " failed; errors: "
        + " | ".join(errors)
    )


__all__ = ["chat_with_fallback", "make_backend"]
