# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): No files or code were presented that create, serialize, or store graph objects under `data/processed/graphs/` in pickle or parquet format, nor any checksum generation/check verification. The required artifact is missing, so the task is not satisfied.
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/graphs/node_degree_stats.json
- `T023` (rejected 1x): No code, script, or JSON example showing the new convergence detection logic or the updated `ThermalSample` metadata with a `converged` field is provided. The required artifact (implementation that checks relative change < 1 % and writes `converged: false` on failure) is missing.
- `T024` (rejected 1x): No code, script, notebook, or other artifact implementing the required outlier detection (identifying configurations where >15 % of atoms have coordination <3 or >6) is present. The evidence consists only of the task description and project spec, without any concrete implementation or test output. The required functionality is therefore missing.
- `T025` (rejected 1x): No evidence of a `data/processed/conductivities/` directory containing saved `ThermalSample` objects (graph, conductivity, metadata) was provided, nor any indication that checksums are computed and stored. The required artifact is missing, so the task is not satisfied.
- `T032` (rejected 1x): No code, notebook, script, or output files implementing or demonstrating SHAP (or similar) feature‑importance extraction from a trained GNN are present. Without such artifacts, we cannot confirm that the required functionality was actually delivered. The implementer must provide the implementation (e.g., a Python module or notebook) and example results showing per‑sample importance scores.
- `T033a` (rejected 1x): No artifact (script, notebook, function, or result file) showing a Pearson correlation analysis between feature importance and global thermal conductivity was provided. Consequently, there is no evidence that the required analysis was implemented, nor any correlation coefficient or supporting output to verify it. The implementer must supply the actual code and/or results demonstrating the completed analysis.
- `T034` (rejected 1x): No code, script, notebook, or documentation implementing Pearson correlation significance testing with Bonferroni correction was provided; the evidence section contains no artifact paths or files to inspect. The required implementation is therefore missing.
- `T036` (rejected 1x): No files or directories were presented under `data/processed/model_outputs/`; thus the LMM coefficients, correlation results (r and p‑value), and their interpretation are not saved, nor is there any evidence that such outputs were generated. The required artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

