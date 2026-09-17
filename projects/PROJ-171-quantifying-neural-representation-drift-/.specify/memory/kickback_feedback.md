# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T016 implements an Exponential decay model as primary and Linear as fallback. However, Spec FR-005 explicitly mandates a Linear model `drift(t) = a + b·t` as the primary requirement for the MVP. The task description claims 'Constitution VII overrides FR-005', but the task does not include a specific sub-task to implement the Linear model as the *primary* output or to explicitly handle the conflict resolution in code (e.g., a flag to switch modes). Without a task explicitly implementing the FR-005 Linear model as the default/primary path, the MVP deliverable fails the functional spec's core acceptance criteria.
