# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directory tree (`code/data`, `code/training`, `code/analysis`, `code/models`, `tests/unit`, `tests/integration`, `data/raw`, `data/partitions`, `results`, `artifacts`) inside `projects/PROJ-044-evaluating-the-effectiveness-of-differen/` is provided; the implementer’s claim is unsubstantiated. The missing folder structure must be created and shown (e.g., via a directory listing).
- **T003** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T011** — The repository lacks the required `data/raw/femnist.parquet` and its corresponding `femnist.sha256` checksum files, and the provided `code/data/download.py` is truncated and does not contain a concrete FEMNIST download implementation that writes those files. Consequently the task’s core deliverables are missing.
- **T011b** — The required `data/raw/shakespeare.parquet` and its `.sha256` checksum are absent, and the provided `code/data/download.py` is truncated and does not contain a concrete implementation that downloads the `leaf/shakespeare` dataset and writes those files. The task’s core deliverables are therefore missing.
- **T028** — The required `results/summary.csv` file does not exist, so the specified columns and data are missing. While a `validation_report.md` is present, the overall task is incomplete without the summary CSV.
- **T029** — No updated `README.md` or files under `docs/` were provided or referenced; the evidence contains only the feature specification and no documentation artifacts, so the required documentation updates are missing.
