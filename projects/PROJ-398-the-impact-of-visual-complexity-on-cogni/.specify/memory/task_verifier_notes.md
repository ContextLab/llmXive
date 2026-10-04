# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`src/lib/`, `src/metrics/`, `src/experiment/`, `src/analysis/`, `tests/`) is present; the artifact list is empty, so the claimed code structure has not been provided.
- **T001b** — No directory structure (`data/stimuli/`, `data/processed/`, `data/measurements/`, `data/raw/`) is presented or referenced in the provided artifacts; without visible evidence of these folders, the requirement cannot be confirmed as satisfied.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or corresponding CI scripts) are present, nor any documentation showing that ruff and black have been set up for the project. The required artifacts to prove the tools are configured are missing.
- **T014d** — No JSON side‑car files were presented under `data/stimuli/metadata/`, nor any listing of their contents showing the required `entropy`, `color_variance`, and `object_count` fields. Without these files, the claim that per‑stimulus metadata has been recorded cannot be verified. The implementer must provide the actual JSON files (or a directory listing with sample content) for each image ID.
- **T011** — The provided `src/experiment/pilot_interface.py` lacks any Streamlit UI code, does not implement a mock server, and is truncated (e.g., `append_rating` is unfinished). Moreover, the required `data/measurements/cohort.json` file is missing entirely. These missing components mean the task’s specifications are not satisfied.
- **T010a** — declared artifact(s) missing/empty/invalid: data/measurements/human_ratings.csv
- **T012** — declared artifact(s) missing/empty/invalid: data/measurements/human_ratings.csv
- **T013** — declared artifact(s) missing/empty/invalid: data/derived/pilot_validation_report.md
