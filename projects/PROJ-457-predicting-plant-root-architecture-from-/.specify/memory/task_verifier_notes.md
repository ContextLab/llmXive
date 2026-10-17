# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — Requested task execution failed; rerun successfully: code/run_lint.py exit=1
- **T004** — `code/config.py` and `code/models.py` exist with real, substantive implementations (config loader with defaults, `setup_logging()` creating `artifacts/logs/`, and the two required dataclasses). However, the required `config.yaml.template` is absent from the evidence (only `config.yaml` exists, which is a different artifact), and there is no execution evidence that `setup_logging()` actually ran and created a log file in `artifacts/logs/`. The implementer must add `config.yaml.template` and provide run evidence for the verification command.
- **T006** — Requested task execution failed; rerun successfully: code/ingestion.py exit=1
