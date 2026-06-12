# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 7 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Phase 4 evaluation mentions F1/precision/recall but no power analysis for detecting 1-5% anomaly rates with stated sample sizes. Add sample size justification for statistical power at these injection rates.
- ADVI convergence for DPGMM mixture models has known challenges. Plan should explicitly address whether ADVI is expected to converge adequately for this use case, beyond generic ELBO monitoring.
- SC-002 states 'sufficient observations per dataset' but does not define the threshold. data-model.md specifies minItems: 1000, and plan.md references T173 for verification. The spec should explicitly state '≥1000 observations' to match the schema constraint and enable unambiguous verification.
- Spec states 'Total Files: 8 (6 schema tests + 2 service interface tests)' but plan.md lists 9 schema files including streaming_dpgmm.schema.yaml. The spec is missing a story for streaming_dpgmm schema which the plan correctly includes. Update spec to reflect 9 schema files or document streaming_dpgmm as an additional required contract.
- Plan notes 'time_series_dataset.schema.yaml which serves as the master dataset schema' but data-model.md defines Dataset entity with different field names (series_id vs id, values vs observations, timestamp vs timestamps). Contracts and data model are inconsistent.
- Quickstart references 'electricity_labels.csv' but data-model.md and research.md state labels come from synthetic anomaly injection, not external CSV. Quickstart should reference injected label generation, not external file.
- Dataset entity defines 'timestamp' (singular) but time_series_dataset.schema.yaml defines 'timestamps' (plural). Field naming should be unified across data model and contracts.
