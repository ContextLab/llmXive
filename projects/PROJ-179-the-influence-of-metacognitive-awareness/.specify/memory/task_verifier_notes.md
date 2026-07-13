# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — The required file `data/download.py` does not exist in the repository, so no implementation of dataset fetching or checksum validation is present. The task’s core artifact is missing, making the claim of completion invalid.
- **T006** — The required file `data/validate_data.py` does not exist in the repository, so no validation logic is present to check for the `confidence_rating` and `source_label` fields. The task’s core deliverable is missing.
- **T012** — The required file `data/preprocess.py` does not exist in the repository, so no code was provided to extract trial‑wise source labels and responses from the VALID dataset. Without this artifact, the task’s core requirement is unmet.
- **T016** — The required output file `data/results/primary_analysis.json` does not exist, so the correlation results are not rendered as specified. Without this artifact, the implementation cannot be considered complete.
- **T022** — The required output file `data/results/regression_analysis.json` does not exist, so the implementation that should add regression details to this JSON file is missing. Without the file, the task’s core requirement is not satisfied.
- **T025** — No `tests/integration/test_modality_analysis.py` file or any integration‑test code was found in the repository, and no evidence (e.g., test definitions, assertions, or execution logs) was provided. The required integration test for modality‑specific correlation is therefore missing.
