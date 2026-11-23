# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000-VERIFY-SPEC** — The required script `code/utils/verify_spec.py` is missing; without this file the spec cannot be programmatically checked for the presence of the string `"{1, 2, 3, 7, 14}"` in FR‑005.
- **T000-BOOTSTRAP** — The `research.md` does not contain the exact “Summary” text from `spec.md` (the spec has no explicit Summary section) nor the exact “Technical Context” text from `plan.md` (the file lacks a Technical Context section). Additionally, the state file uses `last_updated` instead of the required `updated_at` field, so the timestamp was not correctly updated. These missing/incorrect artifacts prevent the task from being considered complete.
- **T001** — The directory contains a `.project_init.json` file, but the provided evidence does not show its contents, so we cannot confirm it matches the required JSON (`{"project_id": "PROJ-487", "branch": "001-news-volume-anxiety", "created": "2026-06-27"}`). The task remains incomplete until the file’s exact content is verified.
- **T004a** — The project contains a hidden directory `.venv/` but no `venv/` directory created by `python -m venv venv`, nor any logs or scripts showing that exact command was run. The task specifically requires a `venv` folder at `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/`; this artifact is missing.
- **T013b** — declared artifact(s) missing/empty/invalid: code/data/pilot_validation.py
- **T015b-VALIDATE** — declared artifact(s) missing/empty/invalid: code/data/keyword_stability.py, data/raw/anxiety_trends.csv
- **T015-VALIDATE** — declared artifact(s) missing/empty/invalid: code/tests/test_data_validation.py, data/raw/gdelt_events_raw.csv, data/raw/google_trends.csv
- **T037** — Requested task execution failed; rerun successfully: code/utils/update_state.py exit=1
- **T029a** — declared artifact(s) missing/empty/invalid: data/reports/statistical_validity_report.json
- **T029c** — declared artifact(s) missing/empty/invalid: code/tests/test_statistical_report.py, data/reports/statistical_validity_report.json
- **T030-PLOTS** — declared artifact(s) missing/empty/invalid: data/reports/plots/
- **T012c** — declared artifact(s) missing/empty/invalid: code/constants.py
- **T030-TEXT** — declared artifact(s) missing/empty/invalid: code/constants.py
- **T031b** — declared artifact(s) missing/empty/invalid: code/utils/profile_runtime.py
