# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- SC-003 (Performance) mandates training must complete within 6 hours. Task T024 logs duration, and T020 states 'do NOT enforce a hard threshold failure'. There is no task that explicitly implements a timeout mechanism or a build-fail condition if the 6-hour limit is exceeded, creating a gap in enforcing the non-functional performance constraint.
- T016 mandates reading `state/validated_n.json` to determine sample size, but T009 (the generator of this file) is marked as 'rejected' and missing in the critical path. The task assumes a prerequisite artifact that does not exist, making execution impossible without first fixing T009.
