# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000a** — The required log file `data/research/data_availability_log.txt` is missing, so there is no evidence that the dataset was verified or that the required subject count and session criteria were checked. The task’s core deliverable is absent.
- **T000b** — The required log file `data/research/coordinate_alignment_log.txt` does not exist in the project, so the verification and any planned resampling strategy have not been recorded as specified. The task’s core deliverable is missing.
- **T001a** — the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T001b** — Checked the project root for a `.gitignore` file; the artifact list shows only data directories and contract JSON files, with no `.gitignore` present. The required ignore patterns are therefore missing.
- **T001c** — The `README.md` file exists and has the correct title, but the Installation and Usage sections contain actual content (bullet points and placeholder steps) rather than being empty as the task requires. The sections need to be stripped to just headings (or placeholder comments) with no added items.
- **T001d** — declared artifact(s) missing/empty/invalid: data/contracts/csv_time_series.schema.yaml
- **T001e** — declared artifact(s) missing/empty/invalid: data/contracts/states.schema.yaml
- **T005** — the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/memory_profile.json
- **T020b** — declared artifact(s) missing/empty/invalid: data/synthetic/ground_truth_seed.csv
- **T021** — declared artifact(s) missing/empty/invalid: code/connectivity.py
- **T021b** — declared artifact(s) missing/empty/invalid: code/connectivity.py
- **T022** — declared artifact(s) missing/empty/invalid: code/connectivity.py
- **T023** — declared artifact(s) missing/empty/invalid: code/connectivity.py
- **T025** — declared artifact(s) missing/empty/invalid: code/connectivity.py, data/processed/excluded_zero_variance_subjects.csv, data/processed/ventral_striatum_activation.csv
- **T029** — declared artifact(s) missing/empty/invalid: code/analysis.py
- **T029b** — declared artifact(s) missing/empty/invalid: code/analysis.py, data/processed/sensitivity_analysis.csv
- **T030** — declared artifact(s) missing/empty/invalid: code/analysis.py
- **T032** — declared artifact(s) missing/empty/invalid: data/processed/correlation_plot.png
- **T033** — declared artifact(s) missing/empty/invalid: code/reporting.py, data/processed/sensitivity_analysis.csv, paper/results.md
- **T040** — the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T041** — Requested task execution failed; rerun successfully: code/main.py exit=1
