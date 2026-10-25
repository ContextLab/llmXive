# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Phase 3 task T3‑01 proposes computing optical‑flow statistics for 1 s, 3 s, 5 s, 10 s windows using CPU‑only `torchvision`, and Phase 1 task T1‑03 runs a YOLOv8 hand detector on every frame. Processing up to 5 000 episodes (~10 h video) at 1 fps on the free‑tier GitHub Actions runner (2 CPU cores, ~7 GB RAM) is unlikely to complete within the claimed ≤ 5 h wall‑clock budget and may exceed the 6 GB RAM limit, making the pipeline infeasible under the free‑compute constraints.
- The plan asserts that `data/static_predictions.csv` conforms to a `RegressionPrediction` schema and that `data/temporal_features_{w}s.csv` and `results/vla_*.csv` conform to their respective schemas, yet only `contracts/static_features.schema.yaml` is present. Missing contract files for `RegressionPrediction`, `TemporalWindowFeatures`, `StaticResidual`, and `VLAExperimentResult` cause a plan‑to‑contract mismatch (Plan ↔ contracts).
