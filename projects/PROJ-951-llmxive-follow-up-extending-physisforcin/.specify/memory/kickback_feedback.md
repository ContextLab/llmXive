# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-003 uses the placeholder `[deferred]` for the discard proportion ("System MUST discard the bottom **[deferred]** of videos ..."). The required discard rate is undefined, making the requirement unverifiable.
- SC-001 references a target retain/discard rate as `[deferred]`, providing no concrete numeric target. This makes the success criterion unmeasurable.
- FR-003 states "System MUST discard the bottom **[deferred]** of videos based on the physics consistency score (raw score < 60, which equals normalized < 0.60)." The placeholder **[deferred]** leaves the discard proportion undefined, whereas the original idea explicitly requires discarding the bottom **40 %** of videos. This makes the requirement unverifiable.
- SC-001 describes "The percentage of videos retained after filtering is measured against the target retain rate of **[deferred]** (i.e., discard **[deferred]**)." The placeholder provides no concrete target, breaking the success‑criterion measurability that the idea mandates (retain 60 % / discard 40 %).
