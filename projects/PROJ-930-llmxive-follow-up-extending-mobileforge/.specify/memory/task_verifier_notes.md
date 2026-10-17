# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — The script at `code/data/raw/download_mobileforge.py` exists and writes checksums, but it does **not** fetch the required dataset `mobileforge/logs` via `datasets.load_dataset` as specified; it instead downloads `OSTShushack/ExtractionDataset` using `huggingface_hub.snapshot_download`. This deviates from the task’s core requirement, so the implementation is not considered complete.
- **T009** — Requested task execution failed; rerun successfully: code/data/raw/validate_extraction_dataset.py exit=1
