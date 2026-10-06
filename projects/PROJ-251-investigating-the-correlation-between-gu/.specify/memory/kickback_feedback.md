# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): No ingestion script, output CSV, logs, or analysis results were provided; the claim lacks any tangible artifacts (code, data files, or result tables) that demonstrate the required data filtering, validation, correlation calculations, multiple‑testing correction, or predictive modeling. The implementer must supply the actual scripts and generated outputs to satisfy the user stories.
- `T001a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008a` (rejected 1x): No `.env` template file was provided; there is no evidence of a file containing placeholders for `SRA_TOKEN` and `DATA_SOURCE_URL`. The required artifact is missing.
- `T039` (rejected 1x): No evidence was provided that a ruff linting run or black formatting was executed on the `code/` directory, nor any logs, diff outputs, or updated files showing that reported issues were fixed. The required artifacts (lint/format reports and corrected code) are missing.
- `T011a` (rejected 1x): No code, script, or data files were provided that actually fetch the pre‑processed OTU table and serology metadata for the SRP accession series, so the required artifact is missing. The claim lacks any concrete implementation or output to verify.
- `T020b` (rejected 1x): No code, script, notebook, or data file implementing or demonstrating relative abundance normalization was provided; the only evidence is the high‑level feature specification, which does not contain the required artifact. The task therefore lacks the concrete output it demands.
- `T020c` (rejected 1x): No code, data files, or result outputs (e.g., a script that computes Shannon diversity, a CSV with per‑subject Shannon indices, or a report showing the calculations) were provided. Without any tangible artifact, we cannot verify that the Shannon diversity calculation was actually implemented or that it meets the specification. The next implementer must supply the implementation and its resulting output.
- `T021` (rejected 1x): No code, script, notebook, or data file was provided that demonstrates the titers have been log‑transformed and that limits of detection (LOD) are handled as required. Without any artifact to inspect, the claim cannot be verified. The next implementer must supply the actual implementation (e.g., a Python/R script) and/or resulting dataset showing the transformed titer values and LOD handling.
- `T032a` (rejected 1x): No ingestion script, validation logs, correlation analysis output, or predictive modeling code/results were provided. The required artifacts (e.g., a script that filters the OTU tables, a CSV of the cleaned dataset, correlation tables with CLR‑transformed data and Benjamini‑Hochberg adjusted p‑values, and a trained Random Forest model with nested cross‑validation metrics) are missing, so the task is not satisfied.
- `T025` (rejected 1x): No artifact (e.g., log file, report, or measurement output) was provided to demonstrate that SC-004’s outcome was measured and recorded; the only evidence is the task description itself. The required deliverable is missing.
- `T036a` (rejected 1x): No code, log file, notebook, or report containing the computed confusion matrix, precision, recall, or F1‑score for the high/low responder classification was provided. The claim lacks any concrete artifact demonstrating that these metrics were calculated and recorded.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

