# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — Requested task execution failed; rerun successfully: code/main.py exit=1
- **T004** — Requested task execution failed; rerun successfully: code/data/align.py exit=1
- **T005** — The required output `data/processed/aligned_dataset.npz` is MISSING, and the recorded test run of `tests/test_preprocess.py` failed (exit 1) with all 3 tests erroring because `data/raw/qm9.parquet` does not exist — the pipeline never executed past data loading. The script `code/data/preprocess.py` itself looks substantively correct (grid, smoothing, normalization, unit conversion, filtering, NPZ schema), but no evidence shows it ever ran successfully or produced the NPZ with the required shapes/normalization.
- **T006** — Requested task execution failed; rerun successfully: code/data/bias_audit.py exit=1
