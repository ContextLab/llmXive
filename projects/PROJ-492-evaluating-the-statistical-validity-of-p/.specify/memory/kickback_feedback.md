# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 6 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T077 still marked [P] but depends on T076's checksums output. Reviser claimed [P] removed but marker remains. Cannot run in parallel with T076.
- T047 still marked [P] but depends on T046's resource_monitor module. Reviser claimed [P] removed but marker remains. Cannot run in parallel with T046.
- T042 still marked [P] but depends on T040's manifest.json creation. Reviser claimed [P] removed but marker remains. Cannot run in parallel with T040.
- Contract tests still marked [P] despite dependency notes. [P] implies no dependencies; if they run AFTER implementation, [P] is misleading. Consider removing [P] or clarifying they're parallel within their own group only.
- Contract tests still marked [P] despite dependency notes. Same issue as US1 - [P] tag contradicts explicit 'run AFTER' dependencies.
- Contract tests still marked [P] despite dependency notes. Same issue as above - [P] tag is inconsistent with stated dependencies.
