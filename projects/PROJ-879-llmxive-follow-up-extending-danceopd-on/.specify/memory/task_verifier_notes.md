# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — The provided `code/utils/check_weights.py` ends abruptly (`def ` line truncated) and lacks the script’s entry‑point, error handling, and exit‑code logic required to abort on missing manifest, missing files, or checksum/size mismatches. Consequently it does not fully implement the pre‑flight checks described in the task.
- **T009** — No JSON schema files for `TeacherRoutingDataset`, `InferenceResult`, or `DecisionTreeMetadata` were presented in `specs/contracts/`; the required artifacts are missing, so the task is not satisfied.
- **T011** — declared artifact(s) missing/empty/invalid: tests/integration/test_data_generation.py
- **T012b** — The required parquet files `data/raw/imageNet_samples.parquet` and `data/raw/laion_samples.parquet` are missing, so the implementer cannot load any samples, perform the length assertions, or combine them as specified. The core artifact needed to satisfy the task does not exist.
- **T013a** — The provided `code/00_teacher_inference.py` contains only placeholder stubs (e.g., `load_teacher_model` returns `None`, no GPU detection, no actual inference, and no logic to write `teacher_ground_truth.parquet`). The required fallback file `data/raw/teacher_ground_truth.parquet` is missing, and the script does not abort with a clear error when neither GPU inference nor a verified fallback is available. Consequently, the task’s primary and fallback requirements are not met.
- **T013b** — No code, logs, or dataset modifications were presented that demonstrate detection of undefined routing paths, counting/logging of such occurrences, and exclusion of those samples from the final output. The required artifact (implementation and evidence of the exclusion behavior) is missing.
- **T014** — The `code/00_data_extraction.py` file is truncated and ends mid‑statement, showing no implementation for extracting the required fields or writing them to a Parquet file. Additionally, the expected output file `data/processed/teacher_routing_dataset.parquet` is missing entirely. Both the implementation and the required artifact are absent.
- **T018** — declared artifact(s) missing/empty/invalid: tests/unit/test_tree_training.py
- **T019** — declared artifact(s) missing/empty/invalid: tests/integration/test_tree_training.py
- **T023** — declared artifact(s) missing/empty/invalid: data/results/tree_accuracy.csv
- **T030** — declared artifact(s) missing/empty/invalid: data/results/fidelity_metrics.csv
- **T031** — declared artifact(s) missing/empty/invalid: data/results/statistical_tests.json
