# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree or file listings were provided; the required `projects/PROJ-181-predicting-species-distribution-shifts-u/` folder with all specified subdirectories is absent from the evidence. The implementer must create and show the full directory structure.
- **T003** — I could find no linting or formatting configuration files (e.g., .flake8, pyproject.toml with black settings, or a pre‑commit hook) in the provided repository snapshot, nor any documentation indicating that flake8 and black have been set up. Without these artifacts, the requirement to configure linting and formatting tools is not satisfied.
- **T005** — declared artifact(s) missing/empty/invalid: logs/preprocess_counts.yaml
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — The repository contains a `code/download.py` file, but it is truncated (ends mid‑loop) and does not include logic to write the fetched records to `data/raw/occurrence_1970_2000.csv`. Moreover, the required CSV output file is absent. Consequently the implementation does not fulfill the task’s requirement.
- **T010b** — declared artifact(s) missing/empty/invalid: data/raw/occurrence_1970_2000.csv
- **T011** — The required output file `data/raw/occurrence_2005_2020.csv` does not exist, and the provided `code/download.py` is incomplete (truncated) and contains no logic that writes fetched data to that specific CSV file. Consequently the task’s core requirement—fetching recent occurrence data and saving it to the designated file—is not satisfied.
- **T010c** — The required `data/raw/effort_data.csv` file is absent, and the provided `code/download.py` is incomplete (truncated) and only sketches a GBIF API fetch; it does not compute or save the all‑observer density bias proxy as specified. The task’s core output is therefore missing.
- **T013** — Both required artifacts are absent: `code/preprocess.py` does not exist, and the log file `logs/preprocess_counts.yaml` is missing, so the preprocessing functionality and logging are not implemented.
