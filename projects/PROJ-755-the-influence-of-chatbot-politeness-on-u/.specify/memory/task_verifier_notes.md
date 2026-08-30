# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — No .env template file (or any other configuration artifact) was provided; the claim contains only a textual description of the task, not the required file containing an HF_TOKEN placeholder. The required environment configuration artifact is missing.
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — The provided `schema_validator.py` is truncated (ends mid‑function) and thus does not contain a complete implementation, and the required `contracts/dataset.schema.yaml` file is missing entirely. Both the validator code and the schema it should validate against are absent/incomplete.
- **T015b** — No script, code, or downloaded dataset files are present to demonstrate that the Persona‑Chat dataset has been retrieved and stored as required. The evidence needed—a download implementation and resulting local data—are missing.
- **T015c** — No download script, code, or dataset files for EmpatheticDialogues are present; the claim cannot be verified because the required artifact (a working implementation that retrieves and stores the dataset) is missing.
- **T019** — No code, script, or documentation showing a filtering implementation was provided; there is no artifact demonstrating that dialogues lacking `quality_rating` or chatbot utterances are excluded or logged. The required filtering logic is therefore missing.
- **T011c** — No `research.md` file (or updated version) containing the required Minimum Detectable Effect (MDE) estimation results is present in the provided evidence. The task explicitly demands that this markdown document be updated, which cannot be verified from the given artifacts.
- **T012** — No code, data files, or result outputs were provided to demonstrate that the datasets were downloaded, politeness scores computed, the CLMM fitted, or the robustness/subgroup analyses performed. The claim lacks any tangible artifact (scripts, CSVs, logs, or figures) required by the user stories.
