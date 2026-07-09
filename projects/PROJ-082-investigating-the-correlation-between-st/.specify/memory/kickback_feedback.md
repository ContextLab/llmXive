# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T013 requires parsing 'qualitative descriptors' but provides no logic for how to extract them from raw text (e.g., regex, NLP, or specific column mapping). The spec (FR-001) mandates this extraction, but the task description is too vague for deterministic implementation without guessing the input format.
- T022 implements 'Bonferroni correction' but the Plan explicitly rejects Bonferroni for non-independent data in favor of RVE. The task description does not resolve this contradiction or specify which logic to implement, leaving the implementer unable to execute deterministically.
- T019 requires verifying I² precision to a 'standard level of decimal places' but does not specify the exact number (e.g., 2). The spec (SC-002) mandates 'at least two decimal places', but the task fails to encode this specific threshold, making the test non-deterministic.
- T021 requires outputting `egger_skipped_reason` but does not mandate the exact string format. The spec (US-2) requires the specific message 'Skipped: Insufficient studies (N < 10) for Egger's regression.' The task must explicitly enforce this string to ensure the skip logic is verifiable.
- T031 checks memory usage during rendering but does not include a task to verify the *output file size* of the generated PNGs. The spec (SC-003) requires plots to be 'optimized for efficient storage' with a 5MB limit mentioned in the test section, but no task explicitly validates the final artifact size.
