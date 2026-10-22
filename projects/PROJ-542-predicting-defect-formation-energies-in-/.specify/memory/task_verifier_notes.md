# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The provided `code/tests/test_pipeline_entry.py` imports `src.pipeline.run` (not `code.pipeline.run`) and checks that `run()` returns `None`, whereas the task requires a test that imports `code.pipeline.run` and asserts `run()` returns a dict with keys `raw_path`, `features_path`, and `model_path`. Consequently the verification does not satisfy the stated requirement. The pipeline entry point needs to be adjusted and a correct unit test added.
- **T002** — Requested task execution failed; rerun successfully: src/data/download.py exit=1
- **T003** — The required `data/processed/featurize.log` file is missing, and `data/processed/features.csv` contains an extra `composition` column that is not allowed by `contracts/features.schema.yaml`, so the CSV does not validate against the schema. Both issues prevent the task from being fully satisfied.
- **T006** — Checked the repository for the required output artifacts. While `code/models/split.py` and its implementation `src/models/split.py` exist and contain the correct deterministic `GroupShuffleSplit` logic, the expected output files `data/processed/train.csv`, `data/processed/test.csv`, and the checksum files `data/checksums/train.sha256` and `data/checksums/test.sha256` are missing. Without these CSVs and their SHA‑256 files, the task’s output requirements are not satisfied.
- **T007** — Requested task execution failed; rerun successfully: src/models/train.py exit=1
- **T008** — Requested task execution failed; rerun successfully: code/models/evaluate.py exit=2
