"""Local-inference fallback backend (T020).

Loads a small open-weight model via transformers. Used only as a last-
resort fallback for the smallest agents (status reporter, advancement
evaluator) where a 3B-class model is sufficient.
"""

from __future__ import annotations

from typing import Iterable

from llmxive.backends.base import (
    BaseBackend,
    ChatMessage,
    ChatResponse,
    PermanentBackendError,
)


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
    ) -> ChatResponse:
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore[import-not-found]
        except ImportError as exc:
            raise PermanentBackendError(
                "transformers is not installed; required by local backend"
            ) from exc

        tokenizer = AutoTokenizer.from_pretrained(model)
        llm = AutoModelForCausalLM.from_pretrained(model)
        prompt = "\n".join(f"{m.role}: {m.content}" for m in messages) + "\nassistant:"
        inputs = tokenizer(prompt, return_tensors="pt")
        out = llm.generate(
            **inputs,
            max_new_tokens=max_tokens or 256,
            temperature=temperature or 0.7,
        )
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
