# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/scripts/generate_base_template.py exit=1
- **T001a** — The evidence does not include any script or CI configuration that checks the availability of the Cochrane CSV and raises a `FileNotFoundError` on failure. No file path, code snippet, or CI log showing the abort behavior is provided, so the required validation functionality is missing.
- **T002** — Requested task execution failed; rerun successfully: code/main.py exit=2
- **T005** — Checked `code/main.py`, `data/results/sample_estimates.csv` (missing), and `data/results/simulation_raw.jsonl`. The CLI does not accept `--sweep-type` or `--out`, writes outputs to the wrong locations, produces only one “Synthetic” estimator (not the three required), generates 20 simulation records and 20 estimation records (instead of 10 + 30), and the required `sample_estimates.csv` with 30 rows and the specified columns is absent. The task’s end‑to‑end entry point and output specifications are therefore not met.
- **T004** — Requested task execution failed; rerun successfully: code/main.py exit=2
