# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — The required script `code/src/pipeline/run_end_to_end.py` does not exist, and the only execution evidence is from a different script (`scripts/run_minimal.sh`) which merely reports generation of CSV files and does not show the required 50‑row printed summary with all three descriptor columns. Consequently the task’s core deliverable is missing.
- **T007** — The script `code/src/pipeline/compute_complexity.py` correctly generates `data/processed/task_complexity.csv` and `data/processed/correlation.txt`, but the required accompanying schema file `complexity.schema.yaml` is missing, violating the task’s specification that the CSV be provided with its schema.
- **T005** — Requested task execution failed; rerun successfully: src/pipeline/grid_search_labels.py exit=1
