# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T011 hardcodes the 12 trust scale items in the task description. This violates the 'Single Source of Truth' principle if the citation validation in T000 determines the scale items are different. The task should specify reading the items from a source file (e.g., 'docs/trust_scale_items.md' created by a prior step or a canonical config) rather than hardcoding them, or explicitly state that T000's validation result is the source of truth for these hardcoded values.
