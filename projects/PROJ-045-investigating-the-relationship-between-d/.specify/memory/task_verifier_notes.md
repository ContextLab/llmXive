# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020** — The repository contains a `code/validate.py` file, but it does not include any code that writes validation violations to `data/processed/validation_log.txt`, and the required `validation_log.txt` file is absent. Consequently the task’s core output (a JSON‑lines log with the specified schema) is missing.
- **T033** — The repository lacks the required `data/processed/defect_density_metrics.json` file, and the provided `code/dft_runner.py` does not contain any logic that computes defect density, logs it, or writes the specified JSON output. Consequently, the task’s core requirement is not satisfied.
