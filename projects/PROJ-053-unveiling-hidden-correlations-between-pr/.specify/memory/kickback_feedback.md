# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 9 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T031A-1 attempts to load `data/baseline_importance.json` OR `data/literature_baseline_importance.json`. The task does not specify the order of precedence (which file is checked first) or the behavior if both exist. This ambiguity leads to non-deterministic behavior.
- Tasks T016D-1, T016D-2, and T016D-3 are overly fine-grained. They split a single logical operation (filtering the dataset) into three separate tasks (load/drop, drop zero-var, save intermediate). This creates unnecessary dependency overhead. These should be merged into a single 'Filter and Save Intermediate Dataset' task.
- Tasks T029A-1, T029A-2, and T029A-3 are overly fine-grained. They split the calculation and saving of metrics into three steps. These should be merged into a single 'Calculate and Save Metrics' task to reduce dependency noise.
- Tasks T031A-1, T031A-2, and T031A-3 are overly fine-grained. They split the baseline loading, validation, and correlation logic into three steps. These should be merged into a single 'Load, Validate, and Correlate Baseline' task.
- Tasks T047A-1 and T047A-2 are overly fine-grained. They split memory profiling into 'profile' and 'write JSON'. These should be merged into a single 'Profile Memory and Save Report' task.
- Tasks T053-1 and T053-2 are overly fine-grained. They split the 'Fail Loud' logic into 'remove try/except' and 'raise error'. These should be merged into a single 'Implement Strict Data Loader' task.
- Tasks T054-1 and T054-2 are overly fine-grained. They split documentation generation into 'add keys' and 'ensure clarity'. These should be merged into a single 'Update Metrics Documentation' task.
- Tasks T057-1 and T057-2 are overly fine-grained. They split the Sparse GPR fallback into 'implement logic' and 'ensure import'. These should be merged into a single 'Implement Sparse GPR Fallback' task.
- Tasks T058-1 and T058-2 are overly fine-grained. They split the source independence check into 'add logic' and 'handle error'. These should be merged into a single 'Implement Source Independence Validation' task.
