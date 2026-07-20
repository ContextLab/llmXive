# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008b** — No `run.sh` script content was presented; the claim provides only the task description without any actual file or code. The required executable script that imports modules, runs T008a test, and exits with code 1 on failure is missing.
- **T009** — declared artifact(s) missing/empty/invalid: data/raw/human_eval_data.jsonl, state/projects/PROJ-727-assessing-energy-consumption-of-llm-infe.yaml
- **T013** — The repository contains a partially shown `code/inference.py`, but the required output file `data/processed/energy_inference_raw.csv` does not exist, so the inference logs for the three models are not present. Without this CSV (and its rows for GPT‑2, CodeBERT, and StarCoder‑1B), the task’s verification condition is unmet.
- **T014** — The required output file `data/processed/energy_results_raw.csv` does not exist, and the provided `code/evaluation.py` is incomplete (truncated) and does not contain the logic to join inference results with the HumanEval evaluation outcomes to produce that CSV. The task’s core deliverable is therefore missing.
- **T016** — The repository contains `code/main.py` with a partially shown `aggregate_results` function, but the required output files `data/processed/filtered_rows.csv` and `data/processed/energy_results_aggregated.csv` are absent. Without these files, the task’s verification condition (existence and correct filtering) is not met. The implementation must be completed and the aggregation script run to produce the two CSV files.
- **T028** — declared artifact(s) missing/empty/invalid: data/processed/energy_bar.png
