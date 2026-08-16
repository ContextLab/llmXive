# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T012a (Entropy Extraction) references 'AST normalization' and 'AST hash' but does not specify the library or function to use (e.g., `ast.unparse` or a specific hashing library). Without this, the clustering logic is non-deterministic across different implementers.
- Tasks T003a and T003b are too fine-grained (creating config files with specific strings). These should be atomized or merged into a single 'Project Configuration' task, as they represent a single logical unit of work (setting up linting/formatting) rather than distinct executable steps.
- Tasks T004b-raw and T004b-processed are split by file type (raw vs processed) but represent the same logical operation (checksumming). While not fatal, this granularity is slightly too fine. However, since they operate on different file sets, they are acceptable but could be merged into a single 'Checksum Datasets' task with parameters.
