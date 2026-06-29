# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T043 mentions 'Ensure [deferred] line coverage for core logic' which is a nonsensical instruction. Line coverage is a metric, not a code artifact. The task should be split into: 'Run pytest --cov' and 'Verify coverage report exists'.
- Task T040 asks to 'Verify via unit test that plot objects have these attributes'. This is too fine-grained and mixes implementation with verification. The task should be: 'Implement plot functions with explicit labels' and a separate test task 'tests/unit/test_viz_labels.py'.
- Task T041 repeats the verification logic of T040 ('Verify file existence in unit tests'). This is a verification step, not an implementation task. It should be merged into the test tasks (T036/T037) or removed as redundant.
- Task T015 implements ortholog mapping but does not include a check to ensure the mapped orthologs are actually present in the normalized counts matrix before calculating the ISG score. FR-015 requires the score to be computed; if the mapping fails or genes are missing, the task risks silent failure or empty PCA results, violating the acceptance criteria for US1.
- Task T016 calculates the first principal component (PCA) of ISG genes but does not verify that the ISG set is present in the normalized counts matrix (after T015 mapping) before running PCA. If the gene set is empty or missing, the task may fail silently or produce invalid scores, violating FR-002's requirement to compute the score.
