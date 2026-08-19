# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — declared artifact(s) missing/empty/invalid: src/utils/validators.py
- **T013** — declared artifact(s) missing/empty/invalid: src/data/preprocess.py
- **T014** — declared artifact(s) missing/empty/invalid: src/models/train.py
- **T019** — declared artifact(s) missing/empty/invalid: src/models/evaluate.py
- **T020** — declared artifact(s) missing/empty/invalid: src/models/evaluate.py
- **T015** — declared artifact(s) missing/empty/invalid: src/models/evaluate.py
- **T016** — declared artifact(s) missing/empty/invalid: src/models/interpret.py, data/reports/feature_importance.csv
- **T017** — No `run_pipeline.sh` script (or any other files) is present in `src/cli/`, and none of the required output files (`model.pkl`, `feature_importance.csv`, `significant_features.tsv`, `prediction.csv`, `pipeline.log`) are provided. Consequently, the claimed CLI entry point and its orchestration logic cannot be verified. The implementer must add the actual script and ensure it generates the specified outputs.
- **T018** — declared artifact(s) missing/empty/invalid: src/data/preprocess.py
- **T021** — declared artifact(s) missing/empty/invalid: src/models/evaluate.py
- **T023** — No script, data files, or output artifacts (e.g., an updated `run_pipeline.sh`, logs showing CI limit enforcement, generated model files, or reports) were provided for inspection; therefore the claim cannot be verified as fulfilled. The implementer must supply the actual `run_pipeline.sh` with full dataset processing integrated and evidence that the CI limit is respected (e.g., execution logs, test run outputs).
- **T026** — No `src/cli/predict_host_range.sh` script is present, nor any evidence (code, tests, or output files) showing it loads `model.pkl`, processes a FASTA via T025, and writes probability predictions. The required artifact is missing, so the task is not satisfied.
- **T027** — No code, script, function, or output file implementing the probability calculation for all unique hosts in the reference matrix (FR‑017) was provided. The claim lacks any tangible artifact (e.g., a Python module, CLI tool, or generated CSV) that could be inspected to confirm the required functionality. The implementer must supply the actual implementation and evidence of its execution.
- **T028** — The required artifact `src/cli/predict_host_range.sh` does not exist in the repository, so there is no evidence of runtime or memory compliance. The missing script must be added and validated against the ≤30 s and ≤4 GB constraints.
- **T029** — No artifact such as code handling the “Zero‑Feature Pathogen” case, test logs, or output files was provided; the claim contains only a textual description without any concrete implementation or evidence that a baseline prevalence probability is assigned. The required edge‑case handling is therefore not demonstrated.
