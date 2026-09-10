# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T023b** — The provided `experiment_runner.py` does not contain any code that reads `latency_violations.json`, checks the >10% >100 ms condition, adjusts parameters, or writes an abort entry to `data/results/sweep_abort_log.json`. Moreover, the required `sweep_abort_log.json` file is absent. The task’s mitigation logic and abort‑log artifact are therefore missing.
- **T026** — The integration test file exists, but the required output artifacts are not present: `data/results/final_report.md` is missing, and `data/results/deltas.json` contains only placeholder zero values rather than real comparative results. The task’s requirement to produce these files after running `main.py --compare` is therefore not met.
