# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory structure (root with `src/`, `tests/`, `data/`, `results/`, `contracts/`) is shown or described in the provided evidence; the implementer did not supply any file‑system listing, screenshots, or other proof that these folders exist. The task therefore remains unfulfilled.
- **T003** — declared artifact(s) missing/empty/invalid: ruff.toml
- **T004** — declared artifact(s) missing/empty/invalid: github/workflows/ci.yml
- **T005** — No `README.md` file was provided in the evidence, and thus there is no top‑level README containing quick‑start instructions as required. The implementer must add a non‑empty `README.md` at the project root.
- **T036a** — The required test file `tests/contract/test_reproduction_md.py` does not exist in the repository, so the verification of `REPRODUCTION.md` cannot be performed. The task’s primary artifact is missing.
- **T041** — declared artifact(s) missing/empty/invalid: data/checksums.txt
- **T064b** — The required test file `tests/contract/test_config_hyperparams.py` does not exist, so no contract test verifies that the hyper‑parameter keys are defined and within the expected ranges. The `src/config.py` file is present, but without the accompanying test the task is not fulfilled.
- **T071** — declared artifact(s) missing/empty/invalid: src/model/mask.py
- **T071a** — declared artifact(s) missing/empty/invalid: tests/contract/test_mask_schema.py
- **T015** — declared artifact(s) missing/empty/invalid: src/train/opd_baseline.py
