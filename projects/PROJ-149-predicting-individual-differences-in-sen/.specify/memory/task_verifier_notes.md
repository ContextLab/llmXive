# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008a** — The required output `data/processed/feasibility_report.md` is absent, and the provided script does not demonstrably create this file (its content is truncated and does not show the join logic or report generation). The missing report means the task’s exit‑condition and reporting requirements are not satisfied.
- **T009** — No configuration or seed‑pinning artifacts were supplied (e.g., no `requirements.txt`, `environment.yml`, Dockerfile, or a script that sets NumPy/PyTorch/TensorFlow seeds). Consequently the claim does not meet the “setup environment configuration management and random seed pinning” requirement.
- **T013** — No code, script, or output file implementing the required behavioral parsing (median RT extraction, outlier removal, participant exclusion) was provided. Consequently, there is no artifact to verify that the task runs after T010b or meets the specified criteria. The implementer must supply the parsing implementation and any resulting data files.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/features_raw.csv, data/processed/features.csv
- **T016** — The required artifact `data/processed/features.csv` does not exist, so no schema validation (no‑null check, column verification, RT range check) could be performed. The task lacks the essential input file.
- **T017** — The `code/04_modeling.py` file is cut off mid‑string (`"a`) and does not contain a complete implementation (e.g., missing the rest of the results dict, CLI entry point, and any execution logic). Moreover, the required input `data/processed/features.csv` is absent from the repository. Both the script and its data dependency are missing, so the task is not genuinely fulfilled.
- **T020** — declared artifact(s) missing/empty/invalid: data/processed/features.csv
- **T022** — declared artifact(s) missing/empty/invalid: data/processed/split_indices.json
