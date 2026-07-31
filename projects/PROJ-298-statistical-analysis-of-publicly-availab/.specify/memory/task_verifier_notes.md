# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of a `projects/PROJ-298-statistical-analysis-of-publicly-availab/` directory (or any files within it) is provided; the response only contains a feature specification, not the required filesystem artifact. The required root directory is missing.
- **T007** — The `code/data/generate_taxonomies.py` file exists, but the required output files (`data/events/reference_calendar.json` and `data/taxonomy/survey_2023.json`) are missing, and the visible portion of the script does not show the full implementation of taxonomy generation or validation against the Survey 2023 source. The task is not fully satisfied.
- **T008** — declared artifact(s) missing/empty/invalid: data/events/reference_calendar.json, data/taxonomy/survey_2023.json
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/confidence_interval.json
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/trend_results.json
- **T025** — declared artifact(s) missing/empty/invalid: data/processed/decomposition_results.json
- **T030** — The `code/analysis/clustering.py` file does not contain any implementation of a Cluster Label Alignment Score using fuzzy (Levenshtein ≤ 2) matching, and it falls back to a dummy taxonomy when `data/taxonomy/survey_2023.json` is absent. Moreover, the required `data/taxonomy/survey_2023.json` file is missing entirely. Both the core logic and the necessary data file are absent.
- **T032** — declared artifact(s) missing/empty/invalid: data/processed/cluster_results.json
- **T033** — No `README.md` or `quickstart.md` files were found in the specified `projects/PROJ-298-statistical-analysis-of-publicly-availab/` directory, nor any content showing documentation updates or reproducibility instructions. Without these artifacts, the task requirement is unmet.
- **T034** — No code files, diff logs, or linting reports from the `code/analysis/` directory are present; the implementer provided no tangible evidence that any cleanup, refactoring, or lint checks were performed. Consequently, the required artifacts to verify completion are missing.
- **T035** — No code, notebooks, benchmark results, or any performance‑optimization artifacts are present; the only material shown is a specification for a statistical‑analysis feature that does not address the “streaming large data dumps to fit RAM constraint” requirement. Consequently the claimed work does not provide the required implementation, measurements, or reproducible notebook evidence.
