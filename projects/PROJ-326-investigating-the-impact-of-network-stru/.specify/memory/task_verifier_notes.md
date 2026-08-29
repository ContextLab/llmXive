# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — `data/run_log.json` does not exist; the task required the file to be present as an empty JSON array `[]`. Without this file the verification step fails, even though `logging.py` implements the required functions. The missing log file must be created (or `init_logging` must be invoked to create it) to satisfy the task.
- **T018b** — The repository contains a `batch_runner.py` file, but it does not define a `main()` function that loads `config.yaml` and starts the generation pipeline. Moreover, the required `config.yaml` file is absent from the project. Both the essential entry‑point logic and the configuration file are missing, so the task is not satisfied.
- **T018c** — declared artifact(s) missing/empty/invalid: code/tests/contract/test_schemas.py, schema.yaml
- **T018e** — declared artifact(s) missing/empty/invalid: data/raw/global_batch_manifest.json
- **T018f** — The provided `batch_runner.py` only contains a partially shown `GlobalSuccessRateMonitor` class and does not demonstrate the full logic for per‑graph failed‑attempt tracking, global success‑rate enforcement, batch failure handling, or logging to `data/run_log.json`. Moreover, the required `data/run_log.json` and `config.yaml` files are absent, and no verification test is supplied. These missing artifacts and incomplete implementation mean the task requirements are not met.
