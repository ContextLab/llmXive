# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The primary research question – whether brain‑network dynamics relate to musical improvisation skill – cannot be tested because the verified OpenNeuro parquet shard contains **no skill‑proxy columns** (expert rating, task condition, years of training). The plan merely logs a “no skill proxy” message and proceeds, meaning the association analysis will *always* be skipped for this dataset. This makes the central hypothesis unanswerable with the chosen data, a fundamental methodological flaw.
- The primary dataset (`clane9/openneuro-fslr64k`) does not contain any of the required skill‑proxy columns (expert_rating, task_condition, years_of_training, etc.) mandated by FR‑004/FR‑009. Consequently the core association analysis cannot be performed, and the study’s main scientific question becomes unanswerable with this dataset.
- The plan deviates from Constitution Principle VI by omitting FSL/AFNI preprocessing and by using a deterministic vertex‑block parcellation instead of a verified AAL or Schaefer atlas. These deviations are noted as “contingent” but the constitution amendment has not been ratified, leaving the pipeline non‑compliant with a core methodological requirement.
