"""One-lane orchestration-harness pilot (issue #295, scope item 1).

Runs the representative implementer micro-lane through a smolagents
``CodeAgent`` whose model adapter delegates EVERY model call to
llmXive's router (``chat_with_fallback``: free-model guard, per-model
circuit breakers, peer-model fallback) — the disqualifying condition is
a harness that bypasses the router, so the adapter is the heart of the
pilot.

The micro-lane mirrors what ``speckit/implement_cmd.py`` orchestrates
for one task: read tasks.md → implement the described artifact → write
it → validate by executing it → mark the checkbox. The bespoke lane's
gate for the same shape of work is the existing (nightly-green)
``tests/real_call/test_implementer_e2e.py``.

Usage (real Dartmouth call, ~1-3 min):
    .venv/bin/python specs/022-audit-phase3-followup/pilot/smolagents_pilot.py

Decision + measurements: see RESULTS.md next to this file. This pilot
deliberately lives OUTSIDE src/ — per the audit's adoption threshold it
is wired into production only if it reduces orchestration LOC and
passes the same gates.
"""

from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

from smolagents import CodeAgent
from smolagents.models import ChatMessage as SmolChatMessage
from smolagents.models import MessageRole, Model

from llmxive.backends.base import ChatMessage
from llmxive.backends.router import chat_with_fallback

PILOT_MODEL = "qwen.qwen3.5-122b"  # the pipeline's free default


class RouterModel(Model):
    """smolagents Model adapter that delegates to llmXive's router.

    This is the ONLY integration code a smolagents lane needs to stay
    inside the router (Constitution I + IV: free-model guard, breakers,
    peer fallback all still apply). Token/cost accounting flows through
    the normal backend path.
    """

    def __init__(self, model_id: str = PILOT_MODEL) -> None:
        super().__init__(model_id=model_id)
        self.calls: list[dict] = []

    def generate(
        self,
        messages: list[SmolChatMessage],
        stop_sequences: list[str] | None = None,
        response_format: dict[str, str] | None = None,
        tools_to_call_from=None,
        **kwargs,
    ) -> SmolChatMessage:
        converted: list[ChatMessage] = []
        for m in messages:
            role = str(getattr(m.role, "value", m.role))
            content = m.content
            if isinstance(content, list):  # smolagents content blocks
                content = "\n".join(
                    str(part.get("text", "")) for part in content
                    if isinstance(part, dict)
                )
            converted.append(ChatMessage(role=role, content=str(content)))

        start = time.monotonic()
        response = chat_with_fallback(
            converted,
            default_backend="dartmouth",
            fallback_backends=[],
            model=self.model_id,
            max_tokens=32_768,  # reasoning-safe budget (see notes/spec-015)
        )
        elapsed = time.monotonic() - start
        text = response.text
        # smolagents' code parser needs the model's code block; qwen
        # reasoning models sometimes wrap thoughts — the parser handles
        # the standard ```python fences itself.
        if stop_sequences:
            for stop in stop_sequences:
                idx = text.find(stop)
                if idx != -1:
                    text = text[:idx]
        self.calls.append(
            {"seconds": round(elapsed, 1), "chars_out": len(text)}
        )
        return SmolChatMessage(role=MessageRole.ASSISTANT, content=text)


TASK_TEMPLATE = """You are the implementer for a research-code task. Work
directory: {workdir}

The file {workdir}/tasks.md contains:

- [ ] T001 Create {workdir}/fib.py defining fib(n) returning the n-th
  Fibonacci number (fib(0)=0, fib(1)=1), plus an executable check that
  fib(10) == 55 when the module is run directly.

Complete T001:
1. Write the implementation to {workdir}/fib.py (use open()/write).
2. Validate it by importing/executing it and checking fib(10) == 55.
3. Update {workdir}/tasks.md, replacing "- [ ]" with "- [X]" for T001.
4. You MUST finish by calling final_answer("T001 COMPLETE") if
   validation passed; otherwise final_answer with the failure. Do not
   stop without calling final_answer. To validate the written file you
   may run it with subprocess ([sys.executable, str(path)]).
"""


def run_pilot() -> dict:
    workdir = Path(tempfile.mkdtemp(prefix="smolagents-pilot-"))
    (workdir / "tasks.md").write_text(
        "- [ ] T001 Create fib.py with fib(n) + self-check\n",
        encoding="utf-8",
    )

    model = RouterModel()
    # Run 2 tuning (recorded in RESULTS.md): run 1 hit the step cap before
    # the checkbox step, and the default sandbox blocked importing the
    # just-written module (the implementer's core validate-by-executing
    # pattern). `subprocess` must be explicitly authorized for file-level
    # validation — i.e., the sandbox value evaporates for this lane.
    agent = CodeAgent(
        tools=[],
        model=model,
        max_steps=8,
        additional_authorized_imports=["pathlib", "importlib", "sys", "subprocess"],
        verbosity_level=1,
    )

    start = time.monotonic()
    result = agent.run(TASK_TEMPLATE.format(workdir=workdir))
    wall = time.monotonic() - start

    fib_path = workdir / "fib.py"
    tasks_after = (workdir / "tasks.md").read_text(encoding="utf-8")
    fib_ok = False
    if fib_path.exists():
        ns: dict = {}
        exec(fib_path.read_text(encoding="utf-8"), ns)  # pilot validation
        fib_ok = ns["fib"](10) == 55

    return {
        "final_answer": str(result),
        "wall_seconds": round(wall, 1),
        "llm_calls": model.calls,
        "fib_py_written": fib_path.exists(),
        "fib_correct": fib_ok,
        "checkbox_marked": "- [X] T001" in tasks_after or "- [x] T001" in tasks_after,
        "workdir": str(workdir),
    }


if __name__ == "__main__":
    outcome = run_pilot()
    print("\n=== PILOT OUTCOME ===")
    for key, value in outcome.items():
        print(f"{key}: {value}")
    ok = (
        outcome["fib_correct"]
        and outcome["checkbox_marked"]
        and "COMPLETE" in outcome["final_answer"].upper()
    )
    print(f"\nPILOT {'PASSED' if ok else 'FAILED'}")
    sys.exit(0 if ok else 1)
