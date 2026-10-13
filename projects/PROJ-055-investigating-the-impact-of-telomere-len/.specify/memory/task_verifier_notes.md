# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The `code/requirements.txt` file exists and is non‑empty, but there is no evidence that `pip install -r code/requirements.txt` succeeds in a fresh virtual environment. The provided pytest log fails because it looks for the file in the wrong location, and no successful installation run is recorded. A fresh‑env install test (or corrected test path) is needed to satisfy the task.
- **T011** — Requested task execution failed; rerun successfully: code/R/verify_renv.py exit=1
- **T002** — Checked `code/config.yaml` (exists and is valid YAML) and the test log `code/.tasks/T002.tests_test_config.py.log`, which shows that importing `02_ingest_data.py` fails because `config.ConfigError: Missing or empty required configuration key: DRYAD_API_KEY`. The scripts cannot read the configuration without this key, violating the requirement that the config be used by the scripts with no hard‑coded values. Add the missing required key (or adjust the scripts) and ensure the import succeeds.
