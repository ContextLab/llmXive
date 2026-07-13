# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011b** — The provided `code/models/jacotext_cpu.py` stops after defining a sample prompt and contains only comments and configuration; it never loads the model, checks its file size, runs a CPU inference, measures performance, or writes the required JSON report. Consequently the deliverable (model‑size verification, CPU inference test, and performance metrics) is missing.
- **T012** — The required file `code/models/starcoder_cpu.py` is missing, and there is no evidence that the StarCoder model size was checked to be ≤1 GB or that a CPU‑only inference wrapper was implemented. The task’s core deliverables are absent.
