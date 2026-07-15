# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — No code or file was presented that loads a `config.yaml` from `src/modeling/config.yaml`; the required artifact is missing, so the environment configuration management task is not satisfied.
- **T009** — No `src/main.py` file is present in the provided evidence, and thus there is no orchestration script calling `scripts/update_state.py` after major stages. The required artifact is missing.
- **T010** — No `tests/unit/test_ingestion.py` file or its contents were provided; without the actual unit test code we cannot confirm that it checks SMILES normalization and error logging as required. The required artifact is missing.
- **T011** — No evidence of a `tests/unit/test_templates.py` file containing a unit test for the reaction template matching logic was provided; without the actual test file we cannot confirm its existence, content, or correctness. The implementer must supply the test file (non‑empty) that verifies the matching logic as required.
- **T012** — The required file `src/data/ingestion.py` (or `data/ingestion.py`) is missing from the repository, so no implementation exists to download, parse, and filter the USPTO-MIT subset as specified. The task cannot be considered done until the script is present and implements the described functionality.
- **T013c** — No `src/modeling/config.yaml` file or its contents were presented, so we cannot verify that SMARTS patterns for SN1, SN2, and Diels‑Alder were added under `reaction_templates`. The required artifact is missing.
