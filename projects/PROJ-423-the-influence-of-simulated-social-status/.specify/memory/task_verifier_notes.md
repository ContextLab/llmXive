# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014a** — The repository lacks the required `data/processed/cleaned_data.csv` and the resulting `data/processed/outcome_type.json`. Moreover, while `code/preprocess.py` defines a `detect_outcome_type` function, the shown code does not demonstrate reading the CSV, invoking the detection, and writing the JSON with the single `type` key. The essential output artifact is missing, so the task is not satisfied.
- **T013** — The required output file `data/processed/cleaned_data.csv` does not exist, and the provided `preprocess.py` is incomplete (truncated, missing a main routine, missing imports, and no evidence it writes to the required path or reports the final N). The task’s core requirements are therefore not satisfied.
- **T021c** — declared artifact(s) missing/empty/invalid: data/processed/structure_config.json, data/processed/model_config.json
- **T021a** — The repository lacks the required `data/processed/model_config.json` file, and the provided `code/analysis.py` does not contain a `fit_adaptive_model` function that reads this JSON (the shown code only defines other utilities). Both the necessary artifact and the specified function are missing, so the task is not fulfilled.
