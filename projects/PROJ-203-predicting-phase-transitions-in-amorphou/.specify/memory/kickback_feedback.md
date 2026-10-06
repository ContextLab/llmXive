# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/sensitivity_report.json
- `T020#1` (rejected 1x): declared artifact(s) missing/empty/invalid: data/logs/simulation_times.json, docs/reports/pipeline_timing.json
- `T025` (rejected 1x): No files or figures were found in `docs/reports/shap_plots/`; the implementer did not provide the required SHAP summary plots or ranked feature‑importance lists for each chemical family, so the task is not satisfied.
- `T026` (rejected 1x): No partial dependence plot files (e.g., PNG/JPEG/HTML) or generated code/report are present; the claim provides only a textual description without any actual artifact demonstrating the plots for top predictors per chemical family. The required visualizations are missing, so the task is not satisfied.
- `T028` (rejected 1x): declared artifact(s) missing/empty/invalid: docs/reports/interpretability_report.md
- `T029` (rejected 1x): The claim provides only the task description and no actual artifact (e.g., a statistical analysis report, p‑values, confidence‑interval tables, or plots) demonstrating significance testing of family differences for the top descriptors. Consequently, the required evidence is missing.
- `T030` (rejected 1x): No `docs/quickstart.md` (or any updated documentation) was presented; the evidence contains no files or content to verify that the required documentation updates exist. The implementer must add the documentation files with instructions for running the pipeline.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

