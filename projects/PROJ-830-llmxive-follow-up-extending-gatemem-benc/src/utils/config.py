"""
Utility module to provide a singleton LLM instance that runs on CPU‑only.

The LLM used is the 2.7 B (2 B‑Instruct) Meta‑Llama‑3 model quantized to
int8 via bitsandbytes.  The implementation ensures that the model is
loaded onto the CPU and provides a thin wrapper exposing a ``device``
attribute and a ``generate`` method for minimal inference used in the
unit test ``tests/unit/test_llm_cpu.py``.
"""

import threading
from typing import Any, Dict

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch

# -------------------------------------------------------------------------
# Singleton holder and lock to guarantee thread‑safe lazy initialization.
# -------------------------------------------------------------------------
_llm_instance: Any = None
_init_lock = threading.Lock()


class _CPUOnlyLLMWrapper:
    """
    Simple wrapper around a HuggingFace text‑generation pipeline that
    guarantees CPU‑only execution.

    Attributes
    ----------
    device : str
        Always ``'cpu'`` – the wrapper enforces CPU usage.
    tokenizer : AutoTokenizer
        Tokenizer associated with the model (exposed for testing if needed).
    pipeline : transformers.pipelines.Pipeline
        The underlying text‑generation pipeline.
    """

    def __init__(self, model_name: str = "meta-llama/Meta-Llama-3-2B-Instruct"):
        """
        Load the model in int8 quantised form on the CPU.

        Parameters
        ----------
        model_name : str
            HuggingFace identifier for the Llama‑3 model.
        """
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Load the model with bitsandbytes int8 quantisation.
        # ``device_map='cpu'`` forces placement on the CPU even if a GPU is
        # available.  ``load_in_8bit=True`` requests int8 weights via
        # bitsandbytes, which works on CPU‑only environments.
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="cpu",
            load_in_8bit=True,
            torch_dtype=torch.float16,
        )

        # Build a generation pipeline. ``device=-1`` tells the pipeline to
        # stay on the CPU.
        self.pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device=-1,
            max_new_tokens=5,
            do_sample=False,
        )
        self.device = "cpu"

    def generate(self, prompt: str) -> str:
        """
        Perform a minimal generation on ``prompt`` and return the generated
        text (including the original prompt).

        Parameters
        ----------
        prompt : str
            Input prompt for the LLM.

        Returns
        -------
        str
            The generated text.
        """
        # The pipeline returns a list of dicts; we take the first entry.
        result = self.pipeline(prompt)
        if not result:
            raise RuntimeError("LLM generation returned an empty result.")
        return result[0]["generated_text"]

    def __repr__(self) -> str:
        return f"<CPUOnlyLLMWrapper model={self.model.__class__.__name__} device={self.device}>"

    # Expose a minimal dict‑like interface for compatibility with any
    # legacy code that expects ``model`` and ``tokenizer`` attributes.
    def __getattr__(self, name: str) -> Any:
        if name in ("model", "tokenizer", "pipeline"):
            return getattr(self, name)
        raise AttributeError(name)


def get_llm_singleton() -> _CPUOnlyLLMWrapper:
    """
    Return a singleton instance of the CPU‑only LLM wrapper.

    The first call loads the model; subsequent calls return the cached
    instance.  Thread‑safety is guaranteed via a module‑level lock.

    Returns
    -------
    _CPUOnlyLLMWrapper
        The singleton LLM wrapper.
    """
    global _llm_instance
    if _llm_instance is None:
        with _init_lock:
            if _llm_instance is None:  # Double‑checked locking
                _llm_instance = _CPUOnlyLLMWrapper()
    return _llm_instance
