# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The project root contains `code/`, `tests/`, `docs/`, and `config/`, but the required `data/` directory (with its `raw/` and `processed/` subfolders) and the `state/` directory are missing. These absent subdirectories mean the directory structure was not fully initialized as specified.
- **T004** — The required directories `data/raw/`, `data/processed/`, and `state/` are reported as missing in the project root, so the data directory structure was not created.
- **T005** — The required file `code/utils/logger.py` does not exist (only a different `code/logger.py` is present), and the existing logger lacks the mandated JSON keys (`task_id`, `vif_score`, `collinearity_status`). No `state/` YAML files are present, and `code/main.py` does not implement a `--verify-reproducible` flag nor update artifact hashes in state files. These missing artifacts and functionality must be added to satisfy T005.
- **T009a** — The workflow file exists but does not meet the specification: it only defines a `workflow_dispatch` trigger, with the required `on: push` and `on: schedule` triggers commented out. Moreover, the job runs `python code/main.py --verify-reproducible`, but `code/main.py` defines a `--verify` flag (not `--verify-reproducible`), so the command would fail. The implementer must add the push and schedule triggers and align the CLI argument with the script’s actual interface (or add the expected flag).
- **T061** — declared artifact(s) missing/empty/invalid: config/verified_sources.yaml
- **T063** — declared artifact(s) missing/empty/invalid: data/processed/sampling_report.json
- **T067** — declared artifact(s) missing/empty/invalid: config/verified_sources.yaml
- **T033** — declared artifact(s) missing/empty/invalid: data/processed/results.json, docs/report.md
