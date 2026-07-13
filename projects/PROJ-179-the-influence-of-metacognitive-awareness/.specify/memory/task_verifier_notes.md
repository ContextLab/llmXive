# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — The required file `data/download.py` does not exist in the repository, so no implementation of dataset fetching or checksum validation is present. The task’s core artifact is missing, making the claim unsubstantiated.
- **T006** — The required file `data/validate_data.py` does not exist in the repository, so the validation functionality cannot be present. The task’s core deliverable—a script that checks for the `confidence_rating` and `source_label` fields—is missing.
- **T012** — The required file `data/preprocess.py` does not exist in the repository, so no code was provided to extract trial‑wise source labels and responses from the VALID dataset. Without this artifact, the task’s core requirement is unmet.
- **T016** — The required output file `data/results/primary_analysis.json` does not exist, so the implementation has not produced the expected JSON report containing the correlation statistics. The missing artifact must be created and populated with the correct data.
- **T022** — The required output file `data/results/regression_analysis.json` does not exist, so the implementation that should add regression details to this JSON cannot be verified. The missing artifact must be created and populated with the specified regression statistics and diagnostic flags.
- **T025** — No `tests/integration/test_modality_analysis.py` file or its contents are present; without the integration test artifact, the requirement for an integration test of modality‑specific correlation is not satisfied. The implementer must add the test file with appropriate assertions.
