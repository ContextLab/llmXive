# Residual reviewer notes carried forward to paper writing

The research review converged on the SCIENCE (no science/fatal concerns remained), so the project advanced to research_accepted. The writing-level items below were raised by reviewers but judged minor (`minor_revision`) and were not fully resolved within the revision-round cap. Address them while writing/polishing the paper — they are NOT blocking, but the paper should not ship the same nits.

- Split citevqa_cpu_adaptation.py into a modular package structure:
- Create data/validate_dataset.py to handle dataset integrity checks and logging (US3).
- Create infer/run.py and infer/model_loader.py to handle CPU-only model loading and inference (US1).
- Create eval/run.py and eval/saa_scoring.py to handle metric calculation and report generation (US2).
- Refactor the code to generate the required artifacts: outputs/infer_results.jsonl (containing question, answer, bbox) and outputs/evaluation_report.json (containing saa_score, attribution_hallucination_rate).
- Implement the data streaming logic in data/validate_dataset.py to ensure memory efficiency (<7 GB RAM) as per FR-006, rather than loading the full dataset into memory in a single script.
- Add type hints and docstrings to all new modules to improve readability and maintainability, adhering to the research-stage code quality bar.
- Create/Update outputs/evaluation_report.json: Generate the machine-readable JSON report as specified in FR-004. It must contain the saa_score, total_samples, skipped_count, and a breakdown of error types (e.g., answer_only_correct, region_only_correct, both_correct).
- Create/Update outputs/infer_results.jsonl: Ensure the raw prediction artifacts are generated and saved in JSONL format, containing question, predicted_answer, and predicted_bbox for every processed record, as required by FR-001.
- Update data/results.csv or replace with outputs/validation_log.json: If data/results.csv is intended to be the validation log, it must be renamed to outputs/validation_log.json and populated with the list of skipped record IDs and the specific reasons (e.g., "missing_bbox", "missing_image") as required by FR-005 and SC-005.
- Verify Schema Compliance: Ensure all generated data artifacts (CSV/JSON) include the mandatory columns/fields: question, answer, ground_truth_bbox, predicted_bbox, and image_path (or image_id) to allow for independent verification of the SAA calculation.
- Create the docs/reproducibility/ directory and add data_quality_report.md detailing the dataset validation process, including the count of skipped records and reasons, as required by spec.md (FR-005) and plan.md.
- Create the outputs/ directory and ensure the pipeline generates outputs/infer_results.jsonl, outputs/evaluation_report.json, and outputs/validation_log.json instead of placing them in data/.
- Reorganize the source code to match plan.md: move citevqa_cpu_adaptation.py logic into infer/run.py and eval/run.py (or create these files), create data/validate_dataset.py, and establish the external/CiteVQA/ submodule structure.
- Update README.md to reflect the new directory structure, including instructions for initializing the external/CiteVQA submodule and running the pipeline from the root.
- Verify and Document Pipeline Alignment: In docs/reproducibility/pipeline_validation.md (create if missing), explicitly map the current citevqa_cpu_adaptation.py implementation to the spec's infer/run.py and eval/run.py requirements. Detail how the script handles CPU-only loading, memory constraints, and the specific SAA calculation logic (including IoU thresholding and attribution error tagging). If the current script deviates from the spec's modular design, update the code to match the spec or
- Confirm SAA Metric Implementation: In citevqa_cpu_adaptation.py (or the relevant evaluation module), add explicit logging or a debug output section that prints the breakdown of "Answer Correct/Region Wrong" vs. "Answer Wrong" cases for the processed samples. This is necessary to verify that the "WYSIATI" bias mitigation (distinguishing attribution hallucinations) is functionally present, as required by the spec's User Story 2 and Phase 6.
- Validate Dataset Integrity Check: Ensure citevqa_cpu_adaptation.py (or a dedicated validation script) includes and logs the results of the dataset integrity check (FR-005) for question, answer, ground_truth_bbox, and image_path fields. If this check is missing, implement it and record the count of skipped records in data/summary.csv or a new validation_log.json to satisfy SC-005.
- Create the directory structure infer/, eval/, data/, and tests/ as defined in plan.md.
- Implement infer/run.py to serve as the entry point for the inference pipeline, ensuring it generates outputs/infer_results.jsonl as specified in FR-001.
- Implement eval/run.py to consume the inference results and generate outputs/evaluation_report.json containing the SAA metric, as specified in FR-003 and FR-004.
- Create data/validate_dataset.py to perform the dataset integrity checks (FR-005) and generate outputs/validation_log.json.
- Implement the test suite in tests/ (including contract/ and integration/ subdirectories) to verify the schemas and pipeline execution as per T010-T026.
- Move or refactor the logic currently in citevqa_cpu_adaptation.py into the appropriate modular files (infer/, eval/, data/) to ensure the codebase matches the planned architecture.
- Generate the required documentation files in docs/ and docs/reproducibility/ as outlined in T036.
- Update the output generation logic to produce the JSON/JSONL artifacts specified in the spec, or update the spec to explicitly accept the CSV format if the scope has changed (but the latter requires a spec revision, not just a code change).
- Refactor citevqa_cpu_adaptation.py into the modular structure defined in plan.md: create infer/run.py for inference, eval/run.py for scoring, and data/validate_dataset.py for pre-checks.
- Replace data/results.csv and data/summary.csv with outputs/infer_results.jsonl (containing question, predicted_answer, predicted_bbox) and outputs/evaluation_report.json (containing saa_score, attribution_hallucination_rate, skipped_count).
- Implement the dataset validation logic in data/validate_dataset.py to explicitly check for ground_truth_bbox and image_path fields, logging skipped records to outputs/validation_log.json as per FR-005 and SC-005.
- Ensure eval/run.py calculates and reports the attribution_hallucination_rate (correct answer + wrong region) to satisfy the Phase 6 bias mitigation requirements.
