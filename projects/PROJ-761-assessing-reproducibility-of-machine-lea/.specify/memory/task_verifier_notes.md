# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directory tree (e.g., `data/raw`, `code`, `artifacts/logs`, etc.) is provided; the implementer did not supply any file‑system listing, script output, or screenshot confirming that the `mkdir -p …` command was run. The task therefore lacks the mandatory artifact.
- **T003b** — No linting/formatting configuration files or command‑line output are present, and there is no evidence that `ruff check .` and `black --check .` were executed with a zero exit code. The required artifacts to prove the task’s success are missing.
- **T006a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T003** — The required schema file `contracts/PaperManifest.schema.yaml` is absent, and the provided `code/ingest.py` snippet does not show any actual validation against a schema (the code is truncated and only warns if `jsonschema` is missing). Without the schema and a working validator, the manifest cannot be validated as the task demands.
- **T018** — The repository contains `code/main.py`, but the script does not include code that writes the aggregated list to `artifacts/reports/repro_results.json`, nor does it ensure the required fields (e.g., `max_metric_std`) are present. Moreover, the expected output file `reports/repro_results.json` is absent. The task’s core deliverable—producing the aggregated JSON report—is therefore missing.
- **T030b** — No `artifacts/logs/failure_log.json` file was presented, and there is no evidence that such a JSON file exists or contains objects with the required keys (`paper_doi`, `failure_mode`, `details`). The implementer must create the file at the specified path and populate it with the correctly‑structured data.
- **T031** — declared artifact(s) missing/empty/invalid: reports/stat_summary.json
