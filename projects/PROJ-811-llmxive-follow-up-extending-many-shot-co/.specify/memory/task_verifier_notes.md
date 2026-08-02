# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — declared artifact(s) missing/empty/invalid: data/processed/gold_standard_annotations.json
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/validation_report.json
- **T017** — The required artifact `data/processed/dag_manifest.json` is missing, so no filtering or exclusion logic can be verified. Without the manifest file, the task of removing invalid traces and preventing their inclusion downstream is not demonstrated. The implementer must create the manifest file with the appropriate filtered content.
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/dag_manifest.json
- **T026** — No batch‑runner script or generated prompt files are present in `data/processed/prompts/`; the claim provides no code, configuration, or output artifacts to demonstrate that prompts for multiple seeds and three strategies were actually created. The required files must be added and verified.
- **T027** — The claim provides only a high‑level description of the feature and no concrete artifact (e.g., source code changes, unit tests, or documentation) that implements or verifies the “no duplicate orderings within a strategy group across seeds” validation. Without any code, test suite, or evidence of the validation logic, the requirement is not satisfied. The next implementer must add the actual validation implementation (e.g., in the ordering generation module) and include tests demonstrating that duplicate orderings are detected and prevented across different random seeds.
- **T028** — declared artifact(s) missing/empty/invalid: data/processed/prompt_manifest.json
