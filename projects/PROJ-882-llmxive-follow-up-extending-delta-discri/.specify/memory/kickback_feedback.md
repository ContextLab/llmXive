# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T013 states: 'FAIL if fewer than 200 valid examples remain.' This contradicts the Spec (FR-002) and Plan (Phase 1.1) which mandate a minimum of 10 examples. An implementer cannot deterministically execute a task that hardcodes a failure condition (200) that violates the project's defined minimum threshold (10), leading to a pipeline crash on valid data subsets.
- Tasks T028 and T028a implement a SHAP-based threshold derivation and classification logic. However, the Spec (FR-008, Edge Cases) explicitly mandates using 'Permutation Importance scores (threshold < 0.01)' to distinguish 'signal is emergent' vs 'features are poor proxies'. The task description does not provide the logic for the Spec-mandated Permutation Importance check, leaving the implementer with a conflict between the task instructions and the functional requirements.
- Task T026b describes generating a 'uniform weight vector scaled to match the variance of the true coefficients'. The Spec (FR-005, SC-001) defines the baseline as 'uniform weights from N(0,1)' (random) and a 'uniform-weight baseline' (constant). The task's description of scaling to match variance alters the definition of the baseline specified in the requirements, making the statistical comparison non-deterministic against the Spec's intended metric.
