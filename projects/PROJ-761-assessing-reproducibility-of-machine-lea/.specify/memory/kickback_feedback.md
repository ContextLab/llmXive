# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T013 is marked '[ ]' (pending) but is listed as a dependency for T017 (Sensitivity Analysis) and T018 (Aggregation). The 'Re-plan' notes indicate T013 'could not be made to pass verification' and lacks model substitution logic. This creates a hard ordering block: T017 and T018 cannot proceed without T013's output, yet T013 is flagged as a known broken step. The task list presents a dependency chain that is currently non-functional.
- Task T034 relies on an unexpanded template placeholder '{{claim:c_81186764}}' for guideline citations. While not a strict ordering violation, this creates a semantic dependency on an external resolution step that is not defined in the task flow. The task assumes the placeholder will be resolved before execution, but no preceding task is listed to perform this resolution, potentially causing a runtime failure in the guideline generation flow.
- Tasks T020a and T020b are marked as '[ ]' (unchecked) in Phase 2, yet the Phase 2 'Checkpoint' states 'Foundation ready'. T021 and T022 (which depend on T020a/b for logic) are marked '[X]'. This creates a logical contradiction where the foundational phase is declared complete while critical extraction tasks remain unimplemented. These tasks must be either marked '[X]' with a note that they are trivial/no-ops, or the checkpoint must be moved to after their completion.
