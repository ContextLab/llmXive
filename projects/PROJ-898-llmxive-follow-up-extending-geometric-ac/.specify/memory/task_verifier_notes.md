# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — No evidence of the required `data/raw`, `data/generated`, `data/results` directories or accompanying `.gitkeep` files is present; the implementer’s claim lacks any tangible artifact confirming the directory structure was created.
- **T005** — The `code/utils.py` file exists and implements the requested utilities, but the required test file `tests/unit/test_utils.py` is missing, so the verification step cannot be performed. The task is incomplete until the test suite is provided.
- **T007a** — The provided `code/config.yaml` does not contain the required top‑level keys (`max_attempts`, `target_count`, `max_iterations`, `stiffness_range`, etc.) that the schema test expects, and the test `tests/unit/test_config_schema.py` would fail due to these missing entries. The configuration must expose all required fields at the root level with the correct names and types.
- **T007b** — The repository lacks the required `tests/unit/test_config_loader.py` test, and the provided `code/config.yaml` does not match the nested schema expected by `Config.from_dict` (it uses flat keys instead of `topology`, `solver`, `experiment` sections), so the loader cannot correctly parse the real config file into the typed object.
- **T005-baseline-fetch** — Requested task execution failed; rerun successfully: code/fetch_baseline.py exit=1
- **T008** — the task writes platform-owned path(s) inside the project: `.github/workflows/ci.yml` (shadows `.github/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T009a-fetch-stats** — Requested task execution failed; rerun successfully: code/statistical_reference.py exit=1
