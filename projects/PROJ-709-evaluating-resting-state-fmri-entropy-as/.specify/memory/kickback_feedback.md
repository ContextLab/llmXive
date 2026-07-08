# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T023 references 'Plan Strategy' for the 50-component reduction. This tag points to a plan element that contradicts the spec (FR-008). The task should be updated to reflect the spec's 200-component requirement or the spec/plan must be aligned.
- Task T023 implements PCA reduction to 50 components, but FR-008 in spec.md explicitly requires reduction to 200 components. This violates the 'Producer before Consumer' dependency: the downstream modeling tasks (T024-T028) consume a feature set defined by the spec (200 dims), but the producer task (T023) emits a different dimensionality (50 dims), breaking the semantic contract required for the baseline comparison.
- Task T023 implements PCA reduction to 50 components, directly violating FR-008 which mandates reduction to 200 components. This is a semantic weakening of the spec's requirement for a valid baseline comparison dimension.
- Task T029 adds 'scrub_fraction' as a covariate to the feature set. FR-007 only mandates logging exclusions; FR-003 requires training 'Entropy-only' models. Adding a motion covariate to the feature set alters the definition of the 'Entropy-only' model without explicit spec authorization, risking a violation of the clean separation required to prove entropy's unique value.
