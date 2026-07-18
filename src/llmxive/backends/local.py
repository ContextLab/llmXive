"""Local-inference fallback backend (T020).

Loads a small open-weight model via transformers. Used only as a last-
resort fallback for the smallest agents (status reporter, advancement
evaluator) where a 3B-class model is sufficient.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from llmxive.backends.base import (
    BackendUnavailable,
    BaseBackend,
    ChatMessage,
    ChatResponse,
)

# Loaded (tokenizer, model) pairs, keyed by model id. Loading a checkpoint
# dominates call latency; deterministic-judge tests and multi-candidate
# filter passes call chat() repeatedly with the same model. Values are
# untyped because transformers is a lazy optional import here.
_MODEL_CACHE: dict[str, tuple[Any, Any]] = {}


class LocalBackend(BaseBackend):
    name = "local"
    is_paid = False

    def __init__(self) -> None:
        # Lazy import; transformers is a heavy dep we only require if local
        # is actually selected.
        pass

    def list_models(self) -> list[str]:
        return ["Qwen/Qwen2.5-3B-Instruct"]

    def chat(
        self,
        messages: Iterable[ChatMessage],
        *,
        model: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        deadline_s: float | None = None,
    ) -> ChatResponse:
        # ``deadline_s`` (spec 026 execute's ExecutionOptions) is accepted for a
        # uniform backend signature but is ADVISORY here: local CPU generation is a
        # single blocking ``generate`` bounded by ``max_new_tokens`` and cannot be
        # abandoned mid-call, so there is no wall-clock enforcement to apply.
        _ = deadline_s
        try:
            from transformers import (  # type: ignore[import-not-found]
                AutoModelForCausalLM,
                AutoTokenizer,
            )
        except ImportError as exc:
            # Review finding 3: a MISSING optional runtime is NOT a request-level
            # permanent refusal — it is a backend-UNAVAILABLE condition. Raising
            # BackendUnavailable makes ``execute``/``disposition_of`` ADVANCE the
            # chain (a selected-but-unusable local fallback must not strand the run
            # before a later guarded paid candidate), while still fast-failing this
            # candidate (no same-model retry).
            raise BackendUnavailable(
                "transformers is not installed; local backend runtime unavailable"
            ) from exc

        if model in _MODEL_CACHE:
            tokenizer, llm = _MODEL_CACHE[model]
        else:
            # A checkpoint that cannot be fetched/loaded (no network, missing
            # weights, OOM) is likewise a backend-availability failure, not a
            # request refusal — surface it as BackendUnavailable so the chain
            # advances rather than aborts.
            try:
                tokenizer = AutoTokenizer.from_pretrained(model)
                llm = AutoModelForCausalLM.from_pretrained(model)
            except Exception as exc:
                raise BackendUnavailable(
                    f"local checkpoint {model!r} could not be loaded "
                    f"({type(exc).__name__}: {exc})"
                ) from exc
            _MODEL_CACHE[model] = (tokenizer, llm)
        msg_list = list(messages)
        # Instruct checkpoints only behave (follow the system prompt, emit
        # EOS instead of rambling) when fed through their chat template;
        # fall back to plain role-prefixed concatenation for bare LMs
        # (e.g. tiny-gpt2) that ship no template.
        if getattr(tokenizer, "chat_template", None):
            prompt = tokenizer.apply_chat_template(
                [{"role": m.role, "content": m.content} for m in msg_list],
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            prompt = "\n".join(f"{m.role}: {m.content}" for m in msg_list) + "\nassistant:"
        inputs = tokenizer(prompt, return_tensors="pt")
        # temperature == 0 means DETERMINISTIC decoding (issue #112: the
        # relevance judge pins temperature 0.0). The previous
        # ``temperature or 0.7`` silently coerced 0.0 → 0.7 because 0.0 is
        # falsy; transformers also rejects temperature=0 unless sampling is
        # disabled, so 0/None map to greedy decoding instead.
        gen_kwargs: dict[str, object] = {"max_new_tokens": max_tokens or 256}
        if temperature is not None and temperature > 0:
            gen_kwargs["do_sample"] = True
            gen_kwargs["temperature"] = temperature
        else:
            gen_kwargs["do_sample"] = False
        out = llm.generate(**inputs, **gen_kwargs)
        text = tokenizer.decode(out[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
        return ChatResponse(
            text=text,
            model=model,
            backend=self.name,
            cost_estimate_usd=0.0,
        )

    def healthcheck(self) -> bool:
        try:
            import transformers  # noqa: F401
            return True
        except ImportError:
            return False


__all__ = ["LocalBackend"]
