# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014b** — The provided `code/main.py` only shows argument parsing (including defaults for min‑n, max‑n, step‑n, effect sizes, hypotheses, and iterations) but the file content is truncated and contains no visible loop that iterates over the sample‑size range, effect‑size list, and hypothesis list, nor any logic that enforces a hard constraint on the number of iterations per condition. The required parameter‑loop implementation is therefore missing.
- **T016** — The required file `data/simulation/p_values_raw.csv` does not exist, so no output containing the specified columns (sample size, effect size, test type, raw p-values, hypothesis state) is present. The task’s core deliverable is missing.
- **T018** — The required file `data/simulation/error_rates_summary.csv` does not exist, so the aggregated error rates have not been saved as specified. The task’s core deliverable is missing.
- **T023** — The required file `data/simulation/thresholds.json` does not exist, so no threshold metrics (test type, effect size, identified n) are saved as specified. The task’s core output is missing.
