# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-002 still reads 'scaffold-based split with [deferred] train, [deferred] validation, [deferred] test ratios'. The 80/10/10 ratio is a constitution-mandated constant (Principle VI), not an empirical value to defer, and FR-013 already asserts 80/10/10 — the placeholder makes the split ratios unmeasurable and the spec internally inconsistent. Restore explicit 80/10/10.
- Scenario 3 still says 'selected as one of the top-[deferred] highest FQY values of the test set'. The placeholder prevents reproducible instantiation of the test input. Replace with a concrete selection rule (e.g., top-5% highest FQY, or top-N with N fixed).
- FR-002 still reads 'scaffold-based split with [deferred] train, [deferred] validation, [deferred] test ratios'. The 80/10/10 ratio is a constitution-mandated constant (Principle VI), not an empirical value to defer, and FR-013 already asserts 80/10/10 — the spec is internally inconsistent. Restore explicit 80/10/10 in FR-002. This concern was raised previously and remains unresolved.
- Scenario 3 still says 'selected as one of the top-[deferred] highest FQY values of the test set'. The placeholder prevents the scenario from being reproducibly instantiated. Replace with a concrete selection rule (e.g., top-5% highest FQY values). Previously raised, unresolved.
