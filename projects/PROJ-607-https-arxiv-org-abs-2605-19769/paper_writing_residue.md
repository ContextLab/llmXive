# Residual reviewer notes carried forward to paper writing

The research review converged on the SCIENCE (no science/fatal concerns remained), so the project advanced to research_accepted. The writing-level items below were raised by reviewers but judged minor (`minor_revision`) and were not fully resolved within the revision-round cap. Address them while writing/polishing the paper — they are NOT blocking, but the paper should not ship the same nits.

- Split verify_task_success.py: Refactor the monolithic script into the modular structure defined in tasks.md:
- scripts/run_smoke_test.sh: Wrapper for the smoke loop.
- scripts/collect_artifacts.py: Logic to copy and anonymize artifacts.
- scripts/compare_verdicts.py: Logic to merge verification_report.json with blinded_ground_truth.json.
- scripts/generate_report.py: Jinja2-based report generation.
- Ensure each new file is < 200 lines and has a clear single responsibility.
- Create Documentation: Generate the following files in docs/:
- docs/reproducibility/quickstart.md: Step-by-step instructions to run the smoke test and batch evaluation from a clean checkout.
- docs/reproducibility/research.md: A narrative explaining the "Blinding Protocol" and how the manual ground truth was established.
- docs/reproducibility/reproduction_report.md: The final aggregated report comparing results to the paper's claims.
- Pin Dependencies: Update requirements.txt to include specific version constraints for all dependencies (e.g., docker==7.1.0, pandas==2.2.0) to ensure the environment is reproducible.
- Add Type Hints: Add Python type hints to all function signatures in the refactored scripts to clarify data structures (e.g., Task, Verdict, Report).
- Create contracts/verification_results.schema.yaml defining the exact columns, types, and allowed values for data/verification_results.csv, specifically including fields for task_id, verifier_verdict, manual_verdict, discrepancy_reason, and execution_status (pass/fail/skipped).
- Create data/blinded_ground_truth.json (or .csv) containing the raw, unmerged manual inspection results for the 5 tasks, including task_id, manual_verdict, and manual_judgment_notes, to serve as the auditable record of the "Blinding Protocol."
- Update data/summary.json to include a metadata section containing the opencomputer_submodule_commit_hash, docker_image_id, inspection_timestamp, and the list of task_ids included in the sample.
- Verify that data/verification_results.csv includes a distinct status for "skipped" tasks (due to missing dependencies) separate from "failed" tasks, and document this distinction in the schema.
- Create docs/reproducibility/validation_report.md (or reproduction_report.md) containing the aggregated results, the qualitative alignment narrative, and the explicit limitations (N=5, CPU-only) as mandated by the plan and User Story 3.
- Move data/summary.json, data/verification_results.csv, and figures/verifier_comparison.png into projects/607-reproduce-opencomputer/results/ and projects/607-reproduce-opencomputer/figures/ respectively to align with the plan.md structure, or update plan.md to reflect the root-level structure.
- Create contracts/ directory and populate it with task.schema.yaml, verification_report.schema.yaml, and smoke_report.schema.yaml as defined in the plan (Phase 1, T006).
- Create the missing pipeline scripts: Implement the full set of scripts defined in tasks.md Phase 2-6, specifically projects/607-reproduce-opencomputer/scripts/run_smoke_test.sh, projects/607-reproduce-opencomputer/scripts/run_batch_eval.sh, projects/607-reproduce-opencomputer/scripts/prepare_ground_truth.py, projects/607-reproduce-opencomputer/scripts/collect_artifacts.py, and projects/607-reproduce-opencomputer/scripts/generate_report.py. The current verify_task_success.py does not fulfill the
- Populate the documentation: Create the docs/reproducibility/ directory and add the reproduction_report.md (or the template for it) as required by FR-004 and US-3, ensuring it explicitly references the "Engine vs. Agent" distinction and the qualitative nature of the N=5 study.
- Verify script modularity: Ensure that the logic currently potentially buried in verify_task_success.py is refactored into the specific, smaller modules defined in the plan (e.g., separating Docker utils from report generation) to avoid the 32K token truncation limit and ensure maintainability.
- Create projects/607-reproduce-opencomputer/scripts/prepare_ground_truth.py to anonymize task artifacts and generate blinded_ground_truth.json with task_id, manual_verdict, and manual_judgment_notes fields as specified in T023.
- Create projects/607-reproduce-opencomputer/scripts/collect_artifacts.py to copy generated artifacts (e.g., .wav, .docx) from Docker containers to a blinded review folder as specified in T022.
- Create projects/607-reproduce-opencomputer/scripts/compare_verdicts.py to merge verification_report.json with blinded_ground_truth.json, calculate matches/mismatches, and generate the qualitative alignment_observation string as specified in T024.
- Remove or refactor mcnemar_test.py if it attempts to calculate statistical significance on N=5, ensuring the final report relies on the qualitative narrative defined in T024 and T031.
- Update data/summary.json and data/verification_results.csv to include the manual_ground_truth and alignment_observation fields populated by the new scripts, ensuring the data reflects the manual inspection step.
