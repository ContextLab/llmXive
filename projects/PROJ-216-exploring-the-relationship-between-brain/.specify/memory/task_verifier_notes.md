# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015c** — The required `data/processed/sample_info.json` file does not exist, so the explicit sample size declaration is not present. Consequently the verification command (`python -c "import json; d=json.load(open('data/processed/sample_info.json')); assert 'subjects_used' in d"`) would fail. The implementation must create this JSON file with the specified schema during dataset download.
- **T017c** — No NIfTI file, code, or notebook was provided; there is no evidence that a `float32` 4‑D array with a valid header (including `pixdim` and `sform`) was actually created using nibabel. The required mock NIfTI artifact is missing.
- **T017d** — declared artifact(s) missing/empty/invalid: data/processed/preprocessing_stats.json
- **T018a** — No code, script, log file, or documentation was provided that implements motion‑artifact detection (e.g., computing framewise displacement and flagging subjects with FD > 0.5 mm). Without any artifact to inspect, the requirement cannot be verified as met.
- **T018b** — declared artifact(s) missing/empty/invalid: data/processed/excluded_subjects.log
- **T019a** — declared artifact(s) missing/empty/invalid: data/processed/preprocessing_stats.json
- **T031c** — declared artifact(s) missing/empty/invalid: data/processed/graph_metrics.csv
- **T031d** — No code, script, or unit test evidence was provided showing that the pipeline now halts when zero valid Fluid Intelligence scores are present, nor any error‑message verification. The required implementation and its test are missing.
- **T031b** — No mock data, correlation script, or output results were provided; there is no evidence that the correlation logic was actually run on mock data to verify the pipeline flow. The required artifact (e.g., a script execution log, result CSV, or summary report) is missing.
