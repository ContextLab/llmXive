# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The repository contains `quickstart.md`, `code/orchestrator/config.py`, and a contract‑test file, but the contract test suite never validates any schemas (it is skipped because no data files are present) and the schema names it would use do not match the keys defined in `contract_validator.py`. Moreover, there is no `code/orchestrator/cli.py` (or equivalent entry point) to run `python -m code.orchestrator.cli --help`, so the quick‑start command cannot be exercised. These missing/non‑functional pieces prevent the task’s verification criteria from being satisfied.
