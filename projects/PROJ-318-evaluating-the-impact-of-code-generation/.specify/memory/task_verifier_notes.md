# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `plan.md` does include the required line `MAX_METHODS = 1000`, but it still contains a “CPU full‑precision” note (and mentions “no GPU fallback”), which violates the task’s requirement to remove any full‑precision or fallback‑to‑8‑bit notes. The `code/config.py` correctly defines `MAX_METHODS = 1000`. Remove the full‑precision reference from `plan.md` to satisfy the task.
