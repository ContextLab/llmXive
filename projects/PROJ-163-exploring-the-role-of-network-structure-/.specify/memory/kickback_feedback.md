# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 9 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The planned sample size (≈10‑20 devices) is very small for the multiple‑testing regime (≈6 graph metrics × 4 performance metrics). Even with MDES calculation, the analysis may be under‑powered; the plan proceeds to report “significant” correlations without a clear fallback if MDES > 0.5, risking false positives.
- Bootstrap confidence intervals with 1 000 BCa resamples are unreliable when N < 20, as the resampling distribution is poorly estimated. A permutation test or exact Spearman p‑value should be used, or the limitation explicitly acknowledged.
- Confound control includes chip_generation, qubit_count, device_age_days, and readout_architecture, but omits calibration timestamp / environmental conditions that may co‑vary with performance and could bias the associational analysis.
- The choice of spectral gap as a topological descriptor is not justified in relation to superconducting qubit performance; without a theoretical or empirical rationale, construct validity of this metric is questionable.
- The 'Visualization' phase is listed without any associated functional requirement (FR) or success criterion (SC). The specification does not request a dedicated visualization deliverable, so this element appears to be over‑reach.
- The 'Hygiene & Versioning' phase is listed without any linked FR or SC. While useful, the specification does not mandate a separate hygiene phase, making this an unbacked plan element.
- The plan references `correlation_results.csv` and `power_analysis.csv` with explicit contract names, but it never mentions the contracts for `graph_metrics.csv` (`contracts/graph_metrics.schema.yaml`) nor for `performance_metrics.csv` (`contracts/performance_metrics.schema.yaml`). This breaks the Plan ↔ contracts consistency check.
- The plan describes generating a `performance_window_metrics.csv` for the 30‑day robustness window, yet the data model (`data-model.md`) defines only a `PerformanceMetric` entity with a `source_window` field limited to "current". There is no entity or schema for the window‑averaged metrics, causing a Plan ↔ data‑model mismatch.
- The plan’s Graph Construction step mentions computing several graph metrics, but the corresponding `GraphMetric` entity in the data model includes fields `is_finite` and `component_size` that are not referenced anywhere in the plan. This omission makes it unclear whether those fields will be populated, violating the Plan ↔ data‑model alignment.
