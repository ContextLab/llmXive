# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-001 mandates "GPT-Neo 350M", which does not exist (GPT-Neo family: 125M/1.3B/2.7B/6B/20B; prior run's 401 confirms). The plan substitutes gpt2-medium (355M) and flags the gap, but the spec itself must be amended so FR-001 is satisfiable as written; otherwise the implementer cannot meet the FR verbatim.
- SC-006 asserts 12 runs give ≥90% power at d=0.5, α=0.05; actual power ≈50% (~85/group needed for 90%). The plan honestly reports achieved power and flags the infeasibility, but SC-006 as stated is untestable/false and must be corrected in the spec (e.g., restate as "achieved power is computed and reported").
- The WikiText-2 row's 'Source (verified)' column cites the wikitext-103-raw-v1 parquet URL (…/wikitext-103-raw-v1/test-00000-of-00001.parquet) while the loader uses 'wikitext-2-raw-v1'. The URL and the dataset name disagree; fix the citation to the wikitext-2 artifact or state explicitly which parquet is checksummed under data/raw/.
