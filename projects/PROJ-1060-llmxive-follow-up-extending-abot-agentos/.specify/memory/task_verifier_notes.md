# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T023b** — The provided `experiment_runner.py` does not contain any code that reads `latency_violations.json`, checks the >10% >100 ms condition, adjusts parameters, or writes an abort entry to `data/results/sweep_abort_log.json`. Moreover, the required `sweep_abort_log.json` file is absent. The task’s mitigation logic and abort‑log artifact are therefore missing.
- **T026** — The required `data/results/final_report.md` file does not exist, and the existing `deltas.json` contains only placeholder zero values (e.g., `total_traces: 0`). Moreover, the test shown runs `experiment_runner.py` rather than `main.py --compare`, so the asserted behavior is not demonstrated. The integration test therefore does not verify the production of the required output artifacts.
