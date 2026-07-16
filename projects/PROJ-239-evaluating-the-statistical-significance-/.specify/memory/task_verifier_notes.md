# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — The required `.github/workflows/ci.yml` file is missing; without this CI configuration the task deliverable is not satisfied. The existing `requirements.txt` alone does not meet the specification.
- **T035** — The repository contains the `code/synthetic_cluster_params.py` script, but the required output file `data/derived/synthetic_cluster_structure.csv` is absent, indicating the script either does not write the CSV or was never executed. Additionally, the provided code excerpt does not show the validation step that checks the ICC_RANGE constraint. The missing CSV (and likely missing validation) must be added to satisfy the task.
- **T014** — declared artifact(s) missing/empty/invalid: data/derived/baseline_results.csv
