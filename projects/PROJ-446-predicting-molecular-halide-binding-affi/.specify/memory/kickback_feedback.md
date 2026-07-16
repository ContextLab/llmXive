# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-011 mandates that if data is insufficient, the system must 'Switch to single-halide prediction mode'. Task T016 only generates the simulated dataset and sets a flag, but lacks a specific task to implement the logic for training a model on a single halide (the fallback behavior). Without a task to implement this specific model training path, the FR-011 requirement to 'switch' modes is unimplemented.
