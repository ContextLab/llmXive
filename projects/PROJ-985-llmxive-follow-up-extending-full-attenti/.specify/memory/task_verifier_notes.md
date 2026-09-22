# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — declared artifact(s) missing/empty/invalid: data/logs/structure_verification.txt
- **T003** — The repository contains a correct `pyproject.toml` with a Black configuration, but the required `.ruff.toml` file is missing entirely, and no evidence is provided that `ruff check` and `black --check` were run successfully. The task’s deliverables are therefore not fully satisfied.
- **T005** — The repository contains a partially‑implemented `data_loader.py` (the `MemoryLimitedLoader.load_and_check` method is truncated and does not fully enforce the RAM limit), no unit‑test file asserting peak memory < 7 GB, and the required `data/logs/memory_profile.csv` does not exist. These missing pieces mean the task’s requirements are not satisfied.
- **T014** — declared artifact(s) missing/empty/invalid: data/intermediate/merged_dataset.csv
- **T019** — The repository contains `code/models/train_static.py`, but the file is truncated and does not show a training loop that iterates over the five seeds and saves model files to `data/intermediate/models/seeds/model_seed_{seed}.pkl`. Moreover, the required input `data/intermediate/merged_dataset.csv` is absent, so the script cannot be executed to produce the expected model artifacts. The missing dataset and incomplete script prevent the task from being genuinely fulfilled.
- **T019b** — The script `code/models/evaluate_static.py` exists, but the required output file `data/intermediate/static_eval_scores.json` is missing, indicating the evaluation was not actually executed or the script does not produce the specified JSON scores. The task is therefore not fully satisfied.
- **T019c** — declared artifact(s) missing/empty/invalid: data/results/static_aggregated.json
