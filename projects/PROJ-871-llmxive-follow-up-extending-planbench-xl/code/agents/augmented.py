import os
import json
import re
import time
import fnmatch
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent


class AugmentedAgent(BaseAgent):
    """Augmented agent with failure signature retrieval.

    This agent uses the same LLM as the baseline but, after each
    generation, checks the output against a static failure‑signature
    index.  If a signature matches, a lightweight recovery strategy
    (re‑planning) is triggered via a second LLM call.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # Configuration -------------------------------------------------
        config = config or {}
        self.signature_index_path = config.get("signature_index_path")
        self.model_name = config.get(
            "model_name", "meta-llama/Meta-Llama-3-8B"
        )
        self.max_tokens = config.get("max_tokens", 512)
        self.temperature = config.get("temperature", 0.7)

        # Runtime state -------------------------------------------------
        self.signature_index: Dict[str, str] = self._load_signature_index()
        self.model = None
        self.tokenizer = None
        self.llm_call_count = 0  # tracks how many LLM calls we make

        # Model loading -------------------------------------------------
        self._load_model()

    # -----------------------------------------------------------------
    # Helper methods
    # -----------------------------------------------------------------
    def _load_signature_index(self) -> Dict[str, str]:
        """Load the failure‑signature index from JSON.

        The index is a list of objects of the form:
            {
                "tool_id": "<id>",
                "pattern_string": "<wildcard‑compatible pattern>"
            }

        Returns a dict mapping ``tool_id`` → ``pattern_string`` for fast
        lookup.  If the file does not exist we return an empty dict,
        which effectively disables signature‑based recovery.
        """
        if not self.signature_index_path or not os.path.exists(
            self.signature_index_path
        ):
            return {}

        with open(self.signature_index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Convert list → dict for O(1) look‑ups.
            return {
                entry["tool_id"]: entry["pattern_string"] for entry in data
            }

    def _load_model(self) -> None:
        """Load the quantised Llama‑3‑8B model using bitsandbytes."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            import torch

            quant_cfg = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=quant_cfg,
                device_map="auto",
                torch_dtype=torch.float16,
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to load LLM model: {exc}") from exc

    def _check_failure_signature(self, tool_output: str) -> Optional[str]:
        """Return the matching ``tool_id`` if a failure signature is found.

        Matching uses ``fnmatch`` which supports ``*`` and ``?`` wild‑cards
        as required by the specification.  If no pattern matches, ``None``
        is returned.
        """
        for tool_id, pattern in self.signature_index.items():
            # ``fnmatch`` handles both exact and wildcard matches.
            if fnmatch.fnmatch(tool_output, pattern):
                return tool_id
        return None

    def _replan(self, task: Dict[str, Any], failure_context: str) -> Dict[str, Any]:
        """Generate a new plan after a failure has been detected."""
        prompt = (
            f"Task: {task.get('instruction', '')}\n"
            f"Context: {task.get('context', '')}\n"
            f"Previous failure: {failure_context}\n"
            "Please re‑plan and execute the task, avoiding the previous failure."
        )

        inputs = (
            self.tokenizer(prompt, return_tensors="pt")
            .to(self.model.device)
        )
        self.llm_call_count += 1
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_tokens,
            temperature=self.temperature,
            do_sample=True,
        )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        return {
            "status": "replanned",
            "response": response,
            "recovery_strategy": "replan",
        }

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent on a single ``task``.

        The method returns a dictionary containing at least:
            - ``task_id``
            - ``final_status`` (``success`` / ``failure`` / ``replanned``)
            - ``signature_triggered`` (bool)
            - ``execution_time`` (seconds)
            - ``response`` (LLM output)
        """
        start = time.time()

        # -----------------------------------------------------------------
        # 1. Initial LLM call
        # -----------------------------------------------------------------
        prompt = f"Task: {task.get('instruction', '')}\n"
        if task.get("context"):
            prompt += f"Context: {task['context']}\n"

        inputs = (
            self.tokenizer(prompt, return_tensors="pt")
            .to(self.model.device)
        )
        self.llm_call_count += 1
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_tokens,
            temperature=self.temperature,
            do_sample=True,
        )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # -----------------------------------------------------------------
        # 2. Signature check
        # -----------------------------------------------------------------
        signature_tool = self._check_failure_signature(response)
        signature_triggered = signature_tool is not None

        if signature_triggered:
            # -----------------------------------------------------------------
            # 3. Recovery via re‑planning
            # -----------------------------------------------------------------
            recovery = self._replan(
                task,
                f"Detected failure signature for tool '{signature_tool}'",
            )
            final_status = recovery["status"]
            response = recovery["response"]
            recovery_strategy = recovery["recovery_strategy"]
        else:
            final_status = "success"
            recovery_strategy = None

        elapsed = time.time() - start

        return {
            "task_id": task.get("id", task.get("task_id", "unknown")),
            "response": response,
            "final_status": final_status,
            "execution_time": elapsed,
            "agent_type": "augmented",
            "signature_triggered": signature_triggered,
            "recovery_strategy": recovery_strategy,
            "llm_calls_made": self.llm_call_count,
        }

    def reset(self) -> None:
        """Reset any internal state (not used for the current agent)."""
        self.llm_call_count = 0