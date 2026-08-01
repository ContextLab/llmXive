# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — The provided `code/data_loader.py` contains only checksum and S3‑download utilities; there is no implementation of motion‑scrubbing, FD‑based filtering, subject exclusion logic, or NaN‑counting, nor any logging to the required log files. Moreover, the three log files (`missing_data.log`, `motion_exclusions.log`, `parcel_quality.log`) do not exist. The task’s core requirements are therefore unmet.
- **T007b** — declared artifact(s) missing/empty/invalid: data/processed/valid_subjects.csv
- **T008** — declared artifact(s) missing/empty/invalid: conftest.py
- **T015b** — The provided `code/entropy.py` excerpt only defines `compute_sample_entropy` and shows no logic that counts NaN parcels, checks the >10 % threshold, or writes to `data/logs/invalid_parcels.log`. Moreover, the required log file `data/logs/invalid_parcels.log` does not exist on disk. The task’s core requirement—flagging subjects with >10 % invalid parcels and logging them—is therefore not satisfied.
- **T017** — The required output file `data/processed/entropy_metrics.csv` is absent, and the provided `code/entropy.py` excerpt only shows a helper function without any orchestration logic, chunking handling, or CSV writing. The task’s core deliverable is therefore not present.
- **T017b** — The `code/entropy.py` file does not contain any logic that records peak RAM usage to `data/logs/ram_usage.log` (the file is absent), and the provided snippet shows only the entropy computation function without any psutil‑based instrumentation or file writing. The required log artifact is missing, so the task is not fulfilled.
- **T043** — declared artifact(s) missing/empty/invalid: data/processed/surrogate_results.csv
