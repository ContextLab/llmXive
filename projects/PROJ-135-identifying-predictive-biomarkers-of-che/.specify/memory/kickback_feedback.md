# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T023d is too coarse. It combines 'Orchestrate LOO Loop', 'Call T023a', 'Call T023b', and 'Call T023d' (recursive reference) into one task. It should be split into: 1) 'Implement LOO Loop Controller', 2) 'Implement per-type DE execution', 3) 'Implement aggregation logic'.
- Task T034 is too coarse. It combines 'Pre-Check', 'Loop Logic', 'Re-train', 'Test', and 'Save' into one task. It should be split into: 1) 'Implement LOO Pre-check', 2) 'Implement LOO Re-training Logic', 3) 'Implement LOO Evaluation and Save'.
- Task T041 is too coarse. It combines 'Check existence', 'Read existing flags', 'Merge', and 'Write' into one task. It should be split into: 1) 'Implement summary.md merge logic', 2) 'Implement final summary generation'.
- Task T013 implements a hard 'halt with exit code 1' if valid GEO datasets < 2. Spec FR-002 requires downloading ≥2 datasets, but the Spec's 'Edge Cases' section explicitly states: 'The pipeline must skip that dataset and log a warning; at least 2 datasets... must be available'. The task's hard halt logic ignores the 'skip and warn' instruction for individual datasets, potentially causing total pipeline failure on a single bad dataset when the Spec intended graceful degradation. This is a semantic weakening of the Spec's error handling requirements.
