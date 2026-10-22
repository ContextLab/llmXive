# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The required `code/utils/seed.py` file is missing (only a `utils/seed.py` exists elsewhere), violating the specified script location. Moreover, `tests/test_setup.py` fails the `test_datasets_importable` check because the local `datasets.py` masks the installed package, so the verification test does not pass.
- **T001** — The `download_pi_bench.py` script does not implement the required retry logic nor does it verify checksums against a bundled list (the `REFERENCE_CHECKSUMS` dict is empty). Moreover, when run it writes **0 JSON files**, so `tests/test_dataset_download.py` fails (“No JSON files found in data/raw”). The test suite must pass and the script must produce verified files for the task to be considered complete.
- **T002** — Checked `code/pipelines/parse_traces.py` (exists and implements parsing) and `tests/test_parse_traces.py` (tests the script on a temporary directory). The required output artifact `data/derived/normalized_traces.csv` is missing, so the script does not demonstrably produce the CSV at the specified location.
- **T003** — Requested task execution failed; rerun successfully: code/pipelines/infer_missing_intents.py exit=1
