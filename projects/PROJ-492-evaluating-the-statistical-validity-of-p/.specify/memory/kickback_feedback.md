# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 12 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- User Story 3 (Reproducibility Package Export) is not anchored to any functional requirement or success criterion; no FR explicitly mandates the export of a reproducible package and no SC measures its correctness.
- User Story 4 (Efficient CI Execution) lacks an explicit anchor to a functional requirement or success criterion; FR‑009 describes CPU‑only execution but the story does not reference it.
- Functional Requirement FR‑001 (accept list of URLs) is not linked to any user story; no story cites FR‑001.
- Functional Requirement FR‑002 (automatic extraction) is orphaned; no user story references FR‑002.
- Functional Requirement FR‑003 (reconstruct p‑value) is orphaned; no user story cites FR‑003.
- Functional Requirement FR‑006 (export reproducible research package) is not anchored to any user story; US 3 describes reproducibility but does not reference FR‑006.
- Functional Requirement FR‑009 (CPU‑only execution constraints) is orphaned; no user story explicitly references FR‑009.
- Success Criterion SC‑002 (inconsistency‑detection precision ≥ 90 %) is not tied to any user story; it only cites FR‑004.
- Success Criterion SC‑003 (statistical tests must be computed with SciPy) lacks a story anchor; no user story references SC‑003.
- FR-004 criterion 1 references a confidence‑interval level as `[deferred]`. Without a concrete confidence level (e.g., 95 %), the rule “reported p‑value lies outside the confidence interval derived from the reconstructed test (at [deferred] level)” is ambiguous and cannot be operationalised or measured.
- FR-005 states that a Wilson `[deferred]` confidence interval must be computed, but the confidence level (e.g., 95 %) is omitted. The missing level makes the CI width undefined, preventing verification that the correct interval is produced.
- FR-005 adds several statistical analyses not mentioned in the idea (chi‑squared goodness‑of‑fit test, Cochran‑Armitage trend test, Bonferroni‑adjusted subgroup tests). These constitute scope over‑reach unless explicitly justified as necessary extensions.
