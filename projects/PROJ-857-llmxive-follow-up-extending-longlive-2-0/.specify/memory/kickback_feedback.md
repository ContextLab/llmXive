# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T014 requires dynamic bit-width switching 'without code restart' but does not specify the mechanism (e.g., environment variable, config reload, factory re-instantiation). While this is an implementation detail, the lack of a defined mechanism in the task description makes the 'done' state subjective and difficult to verify against the 'no restart' constraint, potentially leading to incomplete coverage of the requirement.
- Task T005b requires verifying that the checksum recorded in T005a matches the derived file. However, T005a and T005b are marked as dependencies for T005b itself (circular or broken dependency chain in the text: 'Depends on: T006, T005a' while T005a is the source). More critically, if T005a is not completed, T005b cannot execute. The task graph shows a logical deadlock where the verification step (T005b) depends on an artifact (T005a) that is not guaranteed to be produced in the same phase without explicit sequencing, risking a failure to validate the data hygiene constraint (Constitution Principle III).
