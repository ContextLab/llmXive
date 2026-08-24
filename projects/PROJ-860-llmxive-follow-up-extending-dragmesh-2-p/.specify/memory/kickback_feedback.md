# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T021a ('Implement data generation/sweep execution script') is too coarse. It asks to 'Execute a sweep of multiple randomized trials' but does not specify the number of trials, the specific friction range (other than 'non-negative'), or the output file format. An implementer cannot execute this deterministically without these parameters. It should be split into 'Implement sweep generator' and 'Execute sweep with N=100 trials, range=[0.0, 2.5], output=data/generated/sweep.csv'.
- Task T001c ('Generate checksums...') depends on T002 and T003. T002 and T003 create the files, but T001c is scheduled to run *after* them. However, T001b explicitly states 'Do NOT populate content yet'. If T001c runs immediately after T002/T003, it will hash the *newly created* content. The task description is ambiguous about whether it hashes the *skeleton* (empty) or the *populated* content. Given the dependency on T002/T003, it implies populated, but the phrasing 'skeleton files' in T001b creates confusion. The task must explicitly state: 'Compute SHA256 of the *populated* requirements.txt and pytest.ini created in T002/T003'.
- SC-001 requires >15% improvement on *high-friction* objects (0.8–1.2). T015d validates `improvement_pct_varying` (defined as 0.1–0.7 range). T015b records `improvement_pct_varying` but does not explicitly record a metric for the high-friction subset (0.8–1.2) required by SC-001. The verification logic in T015d does not match the specific success criterion in SC-001, creating a semantic gap in constraint preservation.
