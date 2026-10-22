# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required entry‑point script `code/pipeline/run.py` is missing, and the provided test `code/tests/test_pipeline_entry.py` imports `src.pipeline.run` (not `code.pipeline.run`) and expects `run()` to return `None` rather than a dict with `raw_path`, `features_path`, and `model_path`. Both the artifact and the verification behavior do not satisfy the task’s specification.
- **T002** — Requested task execution failed; rerun successfully: src/data/download.py exit=1
- **T003** — The required `data/processed/featurize.log` file is missing, and the existing `descriptor_gaps.log` reports a gap that does not exist in `features.csv`. Moreover, `features.csv` contains only 10 placeholder rows (all values set to 1.0) instead of the ≥500 realistic rows expected, so the featurization output does not meet the task’s specifications.
- **T006** — The evidence shows only `data/processed/split.log` exists; the required script `code/models/split.py`, the split CSV files `data/processed/train.csv` and `data/processed/test.csv`, and the checksum files `data/checksums/train.sha256` and `data/checksums/test.sha256` are all missing. Consequently the deterministic, composition‑aware split and checksum generation have not been delivered.
- **T007** — Requested task execution failed; rerun successfully: src/models/train.py exit=1
