# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`code/`, `data/raw/`, `data/processed/`, `data/survey/`, `tests/`) is presented; the implementer’s claim is unsupported by any listed artifacts. The task therefore remains unfinished.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or corresponding CI scripts) were presented. Without these artifacts, we cannot confirm that ruff and black have been configured as required. The implementer must add the appropriate configuration files and ensure they are non‑empty and correctly set up.
- **T008** — No artifact such as a configuration file, script, or documentation that sets up environment variable management for dataset paths and API keys is present. The evidence only contains a high‑level feature specification unrelated to environment variable handling, so the required setup is missing.
- **T023** — The required output file `data/survey/survey_sequences.json` does not exist, and the provided `code/survey_deploy.py` excerpt does not show the implementation of SessionState, Latin Square randomization, or the logic that writes the JSON file. Without the generated sequence file and clear evidence of the required constraints, the task is not fulfilled.
- **T024** — declared artifact(s) missing/empty/invalid: data/survey/pilot_responses_real.csv, data/synth/pilot_responses_synth.csv
- **T026a** — declared artifact(s) missing/empty/invalid: data/survey/pilot_responses_real.csv
- **T026b** — No code, configuration, or test artifacts were provided that create or check the `data/survey/` and `data/synth/` directories, enforce naming conventions, or raise a `DataHygieneError` for misplaced files. The required enforcement logic and verification are missing.
- **T021** — The required file `tests/unit/test_data_schema.py` does not exist, so no unit test for validating the data schema (participant_id, image_id, salience, rating) is present. The task’s core deliverable is missing.
- **T045** — declared artifact(s) missing/empty/invalid: data/survey/pilot_responses_real.csv, data/processed/cleaned_responses.csv
