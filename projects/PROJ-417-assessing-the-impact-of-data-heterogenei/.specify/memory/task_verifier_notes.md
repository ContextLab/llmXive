# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The CSV `data/processed/base_template.csv` exists and has the required 20 rows and columns, and the script `code/scripts/generate_base_template.py` is present, but there is no evidence that the script was actually executed (e.g., a recorded command run with exit status 0) and no artifact showing that a public Cochrane meta‑analysis CSV was downloaded as the task also requires.
- **T002** — Requested task execution failed; rerun successfully: code/main.py exit=2
- **T005** — Checked `code/main.py`, `data/results/sample_estimates.csv` (missing), and `data/results/simulation_raw.jsonl`. The CLI does not accept `--sweep-type` or `--out`, writes outputs to the wrong locations, produces only one “Synthetic” estimator (not the three required), generates 20 simulation records and 20 estimation records (instead of 10 + 30), and the required `sample_estimates.csv` with 30 rows and the specified columns is absent. The task’s end‑to‑end entry point and output specifications are therefore not met.
- **T004** — Requested task execution failed; rerun successfully: code/main.py exit=2
