# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011c** — No `research.md` file containing the required Minimum Detectable Effect (MDE) estimation results is present in the provided evidence; the implementer did not supply the updated document or any excerpt thereof. The task therefore remains unfinished.
- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — No .env template file containing an HF_TOKEN placeholder was provided; the required configuration artifact is missing, so the environment setup task is not satisfied.
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — The `code/utils/schema_validator.py` file exists, but the required contract schema (`contracts/dataset.schema.yaml`) is missing, so the validator cannot actually validate against the intended schema. Additionally, the provided code is truncated and does not show full validation logic against that contract. The missing contract file must be added (and the validator confirmed to use it) for the task to be complete.
- **T015a** — No code, data files, scripts, or result outputs (e.g., downloaded datasets, politeness scores, CLMM model fits, CSV results, or robustness analyses) were supplied. Without any tangible artifacts, the claim that HCI_P2 validity has been verified cannot be confirmed. The implementer must provide the required scripts, processed data, and analysis outputs to satisfy the user stories.
- **T019** — No code, script, or documentation showing the implementation of filtering logic is provided; there is no artifact demonstrating exclusion of dialogues lacking `quality_rating` or chatbot utterances, nor any logs confirming such filtering. The task therefore remains unverified.
