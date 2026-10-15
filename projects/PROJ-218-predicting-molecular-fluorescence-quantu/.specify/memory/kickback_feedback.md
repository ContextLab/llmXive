# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-002 still reads 'scaffold-based split with fixed ratios [deferred] train, [deferred] validation, [deferred] test'. The 80/10/10 ratio is a constitution-mandated constant (Principle VI: 'MUST enforce a scaffold-based data split (80% train, 10% validation, 10% test)'), not an empirical value to defer. Note FR-013 already asserts the 80/10/10 ratios, so FR-002 is also internally inconsistent. Restore explicit 80/10/10 in FR-002.
- FR-002 uses a '[deferred]' placeholder for the train/validation/test split ratios. The Constitution (Principle VI) mandates an explicit 80/10/10 split. Without concrete ratios the split cannot be measured, making the requirement untestable.
- Acceptance Scenario 3 references a molecule selected from the "top [deferred] experimental FQY of the test set". The placeholder prevents the scenario from being reproducibly instantiated, so the test cannot be executed. Replace the placeholder with a concrete selection rule (e.g., top‑5 % highest FQY values).
