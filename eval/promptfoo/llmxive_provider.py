"""promptfoo custom provider routing through the llmXive backend router.

Why a custom provider instead of promptfoo's built-in ``openai:`` one:
the router is the project's single LLM entry point (Constitution I) —
it owns the free-model guard, per-model circuit breakers, peer-model
fallback across configured free peer models, and the reasoning token budget.
Bypassing it would eval prompts under different serving semantics than
production.

Backend/model selection mirrors the real-call test suite:
  - default: Dartmouth Chat + the centrally configured primary model (CI)
  - override: LLMXIVE_EVAL_BACKEND=local + LLMXIVE_EVAL_MODEL=<hf-id>
    runs the identical code path through local transformers.

promptfoo contract: ``call_api(prompt, options, context) -> {"output": str}``.
The rendered prompt file is the SYSTEM message (matching how agents load
``agents/prompts/*.md``); the test case's ``user_payload`` var is the
USER message (matching ``build_messages``'s artifact bundle).
"""

from __future__ import annotations

import os


def call_api(prompt: str, options: dict, context: dict) -> dict:
    from llmxive.backends.base import ChatMessage
    from llmxive.backends.router import DEFAULT_MODEL, REASONING_MAX_TOKENS, chat_with_fallback

    backend = os.environ.get("LLMXIVE_EVAL_BACKEND", "dartmouth")
    model = os.environ.get("LLMXIVE_EVAL_MODEL", DEFAULT_MODEL)
    user_payload = str(
        ((context or {}).get("vars") or {}).get("user_payload")
        or "Review the supplied artifacts per the contract."
    )
    try:
        response = chat_with_fallback(
            [
                ChatMessage(role="system", content=prompt),
                ChatMessage(role="user", content=user_payload),
            ],
            default_backend=backend,
            fallback_backends=[],
            model=model,
            # Same decoding policy as the production reviewer/judge calls.
            temperature=0.0,
            max_tokens=REASONING_MAX_TOKENS,
        )
    except Exception as exc:  # surface backend failures as eval errors
        return {"error": f"{type(exc).__name__}: {exc}"}
    if response.model != model:
        return {"error": f"Requested model {model!r}, but provider returned {response.model!r}; "
                         "a peer response cannot certify the configured prompt-eval model"}
    return {
        "output": response.text,
        "tokenUsage": {},
        "cost": response.cost_estimate_usd,
    }
