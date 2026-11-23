# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — Requested task execution failed; rerun successfully: code/utils/write_amendment.py exit=1
- **T001** — The provided filesystem lacks the required `docs` directory and the `data/raw/stimuli`, `data/raw/responses`, and `data/processed` subfolders, and the `code/` tree contains many extra entries not specified in the plan, so the exact project structure is not present.
- **T002** — The file `code/requirements.txt` exists and contains a reasonable dependency list, but the task explicitly required the file to have the exact content shown in the task specification (the spec-excerpt header block with project ID, FR-001 through FR-005, data models, analysis pipeline, and references). The actual file contains only package requirements with no part of that required content. The implementer must rewrite `code/requirements.txt` with the exact specified content.
- **T004** — `code/config.py` defines `SEED` correctly, but `DATA_ROOT`, `CODE_ROOT`, and `RESULTS_ROOT` are `Path` objects derived from the project root rather than the exact string values `"data"`, `"code"`, and `"data/results"` required by the task. The variable types/values do not match the specification.
- **T005** — The only artifact present is a minimal top‑level `code/__init__.py` containing a docstring; there are no `data`, `stimuli`, `analysis`, or `viz` sub‑directories (or their `__init__.py` files) to constitute the required package structure. The task is therefore not fully implemented.
- **T016** — The script `code/stimuli/validate.py` exists and looks functional, but the task's verification requirement was not met: `data/raw/stimuli/` is MISSING (no mix of valid/corrupt images to run on) and there is no `logs/validation.log` artifact, so there is no evidence the script was ever executed or that it produces correct valid/invalid entries. The implementer must create the test images (valid + corrupt), run `validate_batch` on them, and produce `logs/validation.log` with correct VALID/INVALID entries.
- **T017a-2** — declared artifact(s) missing/empty/invalid: data/processed/valid_images_list.txt, data/processed/complexity_metrics_raw.csv
- **T017a-3** — declared artifact(s) missing/empty/invalid: data/processed/complexity_metrics_raw.csv, data/results/pca_variance.json, data/processed/complexity_scores.csv
- **T027a-Map** — declared artifact(s) missing/empty/invalid: data/processed/complexity_scores.csv, data/processed/stimulus_set_mapping.csv
- **T027a** — declared artifact(s) missing/empty/invalid: data/raw/responses/participants.csv, data/processed/counterbalance_assignment.csv
- **T026b-1** — declared artifact(s) missing/empty/invalid: data/processed/filtered_trials.csv
- **T026b-2** — declared artifact(s) missing/empty/invalid: data/processed/filtered_trials.csv, data/processed/d_scores_raw.csv
- **T026b-3** — declared artifact(s) missing/empty/invalid: data/processed/d_scores_raw.csv, data/processed/counterbalance_assignment.csv, data/processed/complexity_scores.csv, data/processed/aggregated_d_scores.csv
- **T041a** — declared artifact(s) missing/empty/invalid: code/utils/profile_memory.py
- **T041b** — declared artifact(s) missing/empty/invalid: code/utils/profile_memory.py
- **T043a** — the task writes platform-owned path(s) inside the project: `.github/workflows/analysis.yml` (shadows `.github/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
