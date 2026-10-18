# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: src/data_loader.py exit=1
- **T002** — The provided `src/extraction.py` never writes per‑document raw score tensors to `data/interim/raw_scores/` and its `DynamicHiLSWrapper` does not actually load a HiLS checkpoint or enforce CUDA‑only execution. `src/aggregation.py` expects `.pt` files that do not exist, and its output JSON lacks the required `checksum` field. Moreover, `tests/test_extraction.py` fails during import because the `datasets` dependency cannot be loaded (pyarrow version mismatch), so the end‑to‑end extraction test never runs. The essential artifacts and behaviors required by the task are missing.
- **T003** — Requested task execution failed; rerun successfully: code/run_static_inference.py exit=1
