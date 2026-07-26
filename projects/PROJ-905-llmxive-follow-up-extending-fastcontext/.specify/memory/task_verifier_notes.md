# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listing or other evidence was provided showing that `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/` contains the required subfolders (`data/raw`, `data/processed`, `data/results`, `code`, `tests/unit`, `tests/integration`, `specs/contracts`, `state`). Without this concrete artifact, the task requirement is not verified.
- **T002** — The required file `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/requirements.txt` does not exist, and the existing `code/requirements.txt` does not contain the specification excerpt required by the task. The task’s core requirement is therefore unmet.
- **T003a** — declared artifact(s) missing/empty/invalid: ruff.toml
- **T003b** — declared artifact(s) missing/empty/invalid: pyproject.toml
- **T007b** — The required output file `data/raw/ground_truth_annotations.csv` does not exist, and the provided `code/annotation_extractor.py` is truncated before completing the extraction logic and writing the CSV, so the implementation is incomplete.
- **T007c** — The required input file `data/processed/regularity_scores.csv` is absent, so the script cannot load the sample or compute any correlation. Moreover, the provided `pilot_validation.py` is truncated and does not show the correlation calculation or the flag‑ging logic. The missing CSV (and incomplete script) means the task’s core requirement is not met.
