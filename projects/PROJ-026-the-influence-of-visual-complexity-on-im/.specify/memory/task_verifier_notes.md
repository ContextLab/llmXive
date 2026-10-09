# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The amendment file exists and includes “Status: Ratified”, but the required project state file `state/projects/PROJ-026-the-influence-of-visual-complexity-on-im.yaml` is missing, so the version‑ing step was not completed.
- **T001** — The provided filesystem lacks the required `docs` directory and the `data/raw/stimuli`, `data/raw/responses`, and `data/processed` subfolders, and the `code/` tree contains many extra entries not specified in the plan, so the exact project structure is not present.
- **T004** — `code/config.py` defines `SEED` correctly, but `DATA_ROOT`, `CODE_ROOT`, and `RESULTS_ROOT` are `Path` objects derived from the project root rather than the exact string values `"data"`, `"code"`, and `"data/results"` required by the task. The variable types/values do not match the specification.
- **T005** — The only artifact present is a minimal top‑level `code/__init__.py` containing a docstring; there are no `data`, `stimuli`, `analysis`, or `viz` sub‑directories (or their `__init__.py` files) to constitute the required package structure. The task is therefore not fully implemented.
- **T017a-2** — declared artifact(s) missing/empty/invalid: data/processed/valid_images_list.txt, data/processed/complexity_metrics_raw.csv
- **T017a-3** — declared artifact(s) missing/empty/invalid: data/processed/complexity_metrics_raw.csv, data/results/pca_variance.json, data/processed/complexity_scores.csv
- **T027a-Map** — declared artifact(s) missing/empty/invalid: data/processed/complexity_scores.csv, data/processed/stimulus_set_mapping.csv
- **T027a** — declared artifact(s) missing/empty/invalid: data/raw/responses/participants.csv, data/processed/counterbalance_assignment.csv
- **T026b-1** — declared artifact(s) missing/empty/invalid: data/processed/filtered_trials.csv
- **T026b-2** — declared artifact(s) missing/empty/invalid: data/processed/filtered_trials.csv, data/processed/d_scores_raw.csv
- **T026b-3** — declared artifact(s) missing/empty/invalid: data/processed/d_scores_raw.csv, data/processed/counterbalance_assignment.csv, data/processed/complexity_scores.csv, data/processed/aggregated_d_scores.csv
- **T041a** — declared artifact(s) missing/empty/invalid: code/utils/profile_memory.py
- **T041b** — declared artifact(s) missing/empty/invalid: code/utils/profile_memory.py
