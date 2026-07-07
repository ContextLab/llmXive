# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T034 requires generating `mbb_metrics.json` containing 'CI width and OLS coefficient ratio'. Task T051 requires calculating the 'bootstrap confidence interval width ratio' and verifying it is ≤20%. These are effectively the same calculation. T051 is redundant and creates ambiguity: should the implementer write the logic twice? The task list fails to distinguish between 'generating the metric' and 'verifying the threshold' as distinct, non-overlapping steps.
- Tasks T035 and T050 implement sensitivity analysis but fail to define the masking proportion. SC-006 requires masking '[deferred] to [deferred]' of data. The tasks lack a mechanism to configure, log, or verify this specific proportion, rendering the success criterion unmeasurable and violating the requirement to measure methodological validity against a defined threshold.
- Plan Phase 1 mandates a 'Johansen Cointegration Test' to decide between VAR and VECM paths. While T025 implements the test, there is no explicit task to generate the `model_spec.json` decision artifact *before* modeling begins, nor to log the cointegration result that triggers the VECM path. T029 generates the log but does not explicitly link the decision logic to the model selection, risking a silent drift from the required 'Time-Series Integrity' (Constitution Principle VI).
