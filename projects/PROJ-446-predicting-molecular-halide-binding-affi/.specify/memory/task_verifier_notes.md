# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required `projects/PROJ-446-predicting-molecular-halide-binding-affi/` directory (or any files within it) is provided; the response contains only the task description without any actual filesystem artifact. The implementer must create the directory and show its existence (e.g., a directory listing or file path) to satisfy the requirement.
- **T016** — The provided `code/01_data_ingestion.py` is truncated and does not show the required logic (mode calculation, RDKit descriptor computation, simulated log K generation, schema validation, file writing, and warning log). Moreover, the required `dataset.schema.yaml` is missing, so step 4 cannot be performed. The CSV and JSON files exist but there is no evidence they were produced by the implemented fallback logic. The task therefore remains unfinished.
- **T017** — The required output file `data/processed/halide_binding_data.csv` does not exist, so the task’s core deliverable (saving the processed dataset with schema validation) is missing. Consequently the implementation does not satisfy the stated requirement.
- **T022** — declared artifact(s) missing/empty/invalid: data/processed/model_runs.json
- **T026** — No artifact (e.g., CSV, markdown, or figure) containing a feature interpretation summary table was provided; the claim lacks any actual output linking features to chemical hypotheses, so the requirement is unmet.
- **T027** — declared artifact(s) missing/empty/invalid: data/processed/feature_analysis.json
