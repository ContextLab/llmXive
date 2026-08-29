# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree or file list showing `projects/PROJ-484-the-impact-of-visual-attention-on-recall/` with the required subfolders (`data/raw`, `data/processed`, `artifacts/figures`, `artifacts/logs`, `code`, `tests`) was provided. The evidence needed to confirm the directories exist is missing.
- **T001b** — No `.gitignore` or `README.md` files from `projects/PROJ-484-the-impact-of-visual-attention-on-recall/` were presented, nor any content showing they contain the required exclusions or minimal README text. The required root files are missing from the evidence.
- **T002** — The required file `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/requirements.txt` does not exist (nor a top‑level `requirements.txt`). A `code/requirements.txt` is present, but it is in the wrong location and includes an extra package, so the task’s specified artifact is missing.
- **T002b** — declared artifact(s) missing/empty/invalid: code/venv/pyvenv.cfg
- **T004** — No evidence of the required directories (`data/raw/`, `data/processed/`, `artifacts/figures/`, `artifacts/logs/`) was presented; the claim lacks any artifact listing, screenshots, or file‑system output confirming that the structure exists. The implementer must provide concrete proof that these folders have been created and are non‑empty.
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006a** — No `specs/001-visual-attention-recall/data-model.md` file or its contents were provided; thus the required schema document for Participant, Stimulus, and Trial entities is missing. The implementer must create and supply this markdown artifact.
- **T006b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T040** — No `artifacts/logs/data_verification_report.json` file was presented, and no contents were shown that contain the required `success`, `variable_presence`, and `geometry_status` fields. The task’s primary deliverable is therefore missing.
- **T017** — The required output file `data/processed/analysis.csv` does not exist, and the schema file `schema.yaml` is also missing. The provided `preprocess.py` script is incomplete (truncated) and contains no logic that writes an analysis‑ready CSV or validates it against a schema. Consequently, the task’s core requirement is not satisfied.
