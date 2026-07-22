# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`src/`, `data/`, `tests/`, `state/`) is provided; the implementer did not supply any artifact showing the project structure exists.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black/Ruff settings, `.flake8`, or CI workflow steps) were presented, nor any evidence that these tools have been set up and run. The required artifacts to prove the task are missing.
- **T004** — declared artifact(s) missing/empty/invalid: src/utils/seeds.py
- **T007** — declared artifact(s) missing/empty/invalid: src/utils/validators.py
- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — declared artifact(s) missing/empty/invalid: src/cli/main.py
- **T013** — declared artifact(s) missing/empty/invalid: src/data/ingestion.py
- **T013b** — declared artifact(s) missing/empty/invalid: src/data/ingestion.py
- **T018** — declared artifact(s) missing/empty/invalid: src/data/loaders.py
- **T019** — No evidence of a `data/` directory with the required `raw/`, `processed/`, and `artifacts/` subfolders is shown, nor any code or log demonstrating checksum logging in a `state/` location. The implementer’s claim lacks the necessary artifacts to verify that the directory structure was created and that checksum logging was implemented.
- **T020** — declared artifact(s) missing/empty/invalid: data/artifacts/leakage_report.json
- **T020d** — No artifact was presented – there is no file in `data/artifacts/` containing a “Confounding Prevention Report”, nor any log or statistical check showing that the encoded reaction conditions from T015 were used as features in the split logic (T017). The required report is missing, so the task is not satisfied.
- **T020c** — No file named “Pivot & Limitation Report” exists in `data/artifacts/`, and no content is provided that documents the experimental‑to‑DFT pivot, the FR‑010 limitation, or a code‑level verification of downstream tasks (T014, T015, T018, T023‑T025, T031‑T035). The required artifact is missing, so the task is not satisfied.
- **T021** — The required artifact `tests/unit/test_attention_net.py` does not exist, so there is no unit test verifying the model architecture construction. The implementer must add a non‑empty test file at that location that actually tests the construction of the attention‑based model.
- **T022** — declared artifact(s) missing/empty/invalid: tests/unit/test_trainer.py
