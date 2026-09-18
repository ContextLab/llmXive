# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T022 (US2) depends on T008-impl-cache. T008-impl-cache depends on T008-exec-axpo. The 'Critical Dependency Chains' section correctly lists T008-exec-axpo -> T008-impl-cache. However, T008-impl-cache is listed in Phase 2 with a [P] tag. Since it consumes the output of T008-exec-axpo (also in Phase 2), it cannot be parallel with T008-exec-axpo. The [P] tag on T008-impl-cache is incorrect and creates a false parallel opportunity.
- T015 is marked [P] but explicitly states 'Depends on T014'. T014 is in the same phase (Phase 3). Tasks within the same phase marked [P] must be parallel-safe. T015 cannot run in parallel with T014. The [P] tag on T015 is incorrect.
- T004-ext requires raising 'TimeoutExceededError' or 'MemoryLimitExceededError'. The task does not define the module path for these exceptions or instruct the implementer to create them. An implementer cannot execute this without knowing where to import or define these custom error classes.
