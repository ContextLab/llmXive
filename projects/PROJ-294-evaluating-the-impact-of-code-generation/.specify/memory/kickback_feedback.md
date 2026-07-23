# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T005b installs 'reference-validator' package. The Plan and Constitution mention a 'Reference-Validator Agent' but do not specify the package name. While T005b is a valid implementation step, the task description assumes a specific package name not authorized in the Plan. This is a minor ordering risk if the package doesn't exist or differs from the Plan's intent, but primarily a specification alignment issue. Consider clarifying the source of this package name in the task description.
- Task T005b mandates installing 'reference-validator' (or equivalent) but does not name the specific package or CLI entry point. The implementer cannot deterministically execute 'add to requirements.txt' without knowing the exact package name (e.g., 'reference-validator-agent' vs 'ref-val'). This violates the 'Concrete deliverable' criterion.
- Task T006 requires invoking an external 'Reference-Validator Agent' via CLI, but the spec and plan do not define the agent's existence, location, or interface. The task assumes an artifact not authorized or described in the project scope, making execution impossible without external context.
