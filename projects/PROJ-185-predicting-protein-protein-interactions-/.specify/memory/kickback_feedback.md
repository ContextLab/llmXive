# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Functional Requirement FR-012 (global random seed flag for reproducibility) is not referenced in any User Story traceability matrix, making it an orphaned requirement.
- SC-004 requires reproducible results (identical output files) when re‑run with the same input data and random seed, but the specification does not provide any mechanism to set or control the random seed used by stochastic steps (e.g., random‑graph baseline generation). Add a functional requirement (e.g., FR-012) that mandates a configurable random seed flag and ensures all stochastic processes respect it, making SC-004 measurable.
- [template_placeholder] unfilled [NNN-...] branch-name template placeholder in 'projects/PROJ-185-predicting-protein-protein-interactions-/specs/001-predicting-protein-protein-interactions/spec.md': '[###-predict-ppi-coexpression]'. A converged spec must not carry this; the reviser must resolve it before the spec advances.
