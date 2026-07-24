# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004b** — The provided `code/src/data_loader.py` excerpt does not contain a `checksum_datasets()` function, and the required output file `data/checksums.txt` is absent from the repository. Both the implementation and the recorded checksums are missing, so the task is not fulfilled.
- **T004c** — The repository lacks a `stratify_data()` implementation in `code/src/data_loader.py` (the file is truncated before such a function appears) and the required `data/processed/strata_log.json` file does not exist. Both the core function and its output artifact are missing.
- **T005e** — The `capture_metrics()` function in `code/src/utils.py` is incomplete: it never computes or records the elapsed runtime, contains a syntax error (`e`), and does not write the metrics to `data/processed/resource_metrics.json`. Moreover, the required JSON file is missing from the repository.
