"""promptfoo custom provider routing through the llmXive backend router.

Why a custom provider instead of promptfoo's built-in ``openai:`` one:
the router is the project's single LLM entry point (Constitution I) —
it owns the free-model guard, per-model circuit breakers, peer-model
fallback across configured free peer models, and the reasoning token budget.
Bypassing it would eval prompts under different serving semantics than
production.

Model selection is the production one (spec 026): the call names a capability
PROFILE and the selector resolves the chain from the capability policy and the
live catalog.
  - default: profile ``deep_review`` (what the reviewer prompts run under); the
    model that must answer is the selector's LEADER for that profile.
  - LLMXIVE_EVAL_PROFILE=<profile> evaluates under another profile.
  - LLMXIVE_EVAL_MODEL=<model-id> asks for a specific model. It is honoured
    only if the selector already offers that model for the profile (it is moved
    to the front, never added), e.g. the local transformers checkpoint under
    LLMXIVE_EVAL_PROFILE=standard_generation.
Either way a reply from any OTHER model is an eval error: a peer's answer
cannot certify the prompt against the model being evaluated.

promptfoo contract: ``call_api(prompt, options, context) -> {"output": str}``.
The rendered prompt file is the SYSTEM message (matching how agents load
``agents/prompts/*.md``); the test case's ``user_payload`` var is the
USER message (matching ``build_messages``'s artifact bundle).
"""

from __future__ import annotations

import os


def call_api(prompt: str, options: dict, context: dict) -> dict:
    from llmxive.backends.base import ChatMessage
    from llmxive.backends.router import REASONING_MAX_TOKENS
    from llmxive.model_selection import route

    profile = os.environ.get("LLMXIVE_EVAL_PROFILE", "deep_review")
    user_payload = str(
        ((context or {}).get("vars") or {}).get("user_payload")
        or "Review the supplied artifacts per the contract."
    )
    messages = [
        ChatMessage(role="system", content=prompt),
        ChatMessage(role="user", content=user_payload),
    ]
    model = os.environ.get("LLMXIVE_EVAL_MODEL") or None
    try:
        if model is None:
            # The model under evaluation is whoever the selector ranks first
            # for this profile right now.
            model = route.resolve_chain(
                messages, profile=profile, max_tokens=REASONING_MAX_TOKENS,
            )[1].candidates[0].model_ref.model_id
        response = route.route_chat(
            messages,
            profile=profile,
            caller_model=model,
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
