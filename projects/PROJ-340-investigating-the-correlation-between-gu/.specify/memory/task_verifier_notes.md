# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014b** — The repository lacks the required output artifacts – `data/processed/filtered_data.parquet` and `data/results/outlier_report.json` do not exist. Moreover, the provided `code/ingest.py` snippet is incomplete and shows no implementation of the outlier‑filtering step or the generation of the JSON report. The task’s core requirements are therefore not met.
- **T014c** — The required file `data/processed/filtered_data.parquet` does not exist, so no checksum could be computed, and the YAML file does not contain a checksum entry for that path (only a hash for `code/data_generator.py`). Consequently the task of registering the checksum is not fulfilled.
- **T016** — The required artifact `data/results/timing_evidence.json` does not exist, and the provided `code/main.py` excerpt shows no implementation of start/end time logging, the < 6‑hour assertion, or generation of the JSON evidence. The task’s timing‑check and evidence‑generation requirements are therefore unmet.
- **T016c** — declared artifact(s) missing/empty/invalid: data/results/stress_test_report.json
