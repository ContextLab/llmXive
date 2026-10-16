# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-003 uses the placeholder **[deferred]** for the discard proportion ("System MUST discard the bottom **[deferred]** of videos ..."). The requirement also mentions a default `filter_discard_percent` of 40 % in the description, creating a contradiction: the discard rate is both undefined (placeholder) and defined (default 40 %). This makes the functional requirement unverifiable.
- SC-001 references a target retain/discard rate as **[deferred]** ("The percentage of videos retained after filtering is measured against the target retain rate of **[deferred]** (i.e., discard **[deferred]**)"), but the specification elsewhere (FR-003, Constitution Principle VI) states the intended discard proportion is 40 %. The placeholder leaves the success criterion unmeasurable and inconsistent with the stated design.
- FR-003 uses the placeholder **[deferred]** for the discard proportion ("System MUST discard the bottom **[deferred]** of videos ..."). The original idea explicitly requires discarding the bottom **40 %** of videos. Without a concrete numeric target the requirement is unverifiable.
- SC-001 references a target retain/discard rate as **[deferred]** ("The percentage of videos retained after filtering is measured against the target retain rate of **[deferred]** (i.e., discard **[deferred]**)"), providing no concrete numeric target. The success criterion cannot be measured against the idea’s required 60 % retain / 40 % discard rate.
