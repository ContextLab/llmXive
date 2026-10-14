# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/benchmark.py exit=2
- **T002** — The required files `data/raw/wikitext2.parquet` and `data/raw/README.md` are missing; no evidence of a successful download or checksum recording is provided, so the task’s core requirement is not met.
- **T003** — The `data/configs/` directory contains JSON files, but they were written without actually quantizing the models (auto‑gptq was unavailable) and many have `load_success: false` with placeholder checkpoint paths. No INT8/4‑bit checkpoint files were produced, and there is no `logs/model_load.log` showing OOM attempts for 7 B models. The schema file lives under `specs/.../contracts/` instead of the required top‑level `contracts/config.schema.yaml`, causing the contract test to fail, and the expected `gptneo-125M_fp16.json` file is missing. These omissions mean the task’s core requirements are not
