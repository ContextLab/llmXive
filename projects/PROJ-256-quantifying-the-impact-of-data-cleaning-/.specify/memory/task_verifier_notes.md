# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The repository contains no `tests/integration/test_baseline.py` file, nor any evidence that running the baseline analysis script creates a `baseline_metrics.json` with p‑values in (0, 1) and finite confidence intervals. Without these artifacts, the integration test requirement is not satisfied.
- **T012** — The repository contains a partially shown `code/analysis.py` that defines column‑identification helpers and a t‑test routine, but it does not include a linear‑regression implementation, nor any logic that validates p‑values or checks that confidence‑interval bounds are finite. Moreover, the required output file `data/processed/baseline_metrics.json` is absent. The task’s core deliverables are therefore missing.
