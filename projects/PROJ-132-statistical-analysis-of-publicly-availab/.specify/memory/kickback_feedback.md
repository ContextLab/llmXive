# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'science'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan states it will download the *full* eBird Basic Dataset (≈ 10 GB) and PRISM climate layers, storing them under `data/raw/`. The GitHub Actions free‑tier runner provides only ~14 GB of disk space, which must also accommodate intermediate files, provenance logs, and output artifacts. This exceeds the available storage and will cause the pipeline to fail before any analysis runs. Either down‑sample the eBird data to a size that fits within the runner’s disk quota or redesign the workflow to stream directly from the source without persisting the full raw files.
- FABRICATED-RESULT signal — projects/PROJ-132-statistical-analysis-of-publicly-availab/specs/001-statistical-analysis-of-publicly-availab/plan.md: self-declared fabricated metric — “…l observations; no fabricated placeholder values are used.**  ## Technical Co…”. Research results must be REAL measurements, never simulated / placeholder / hardcoded / drawn from random.*. The reviser must replace this with a genuine computation before the stage advances.
- FABRICATED-RESULT signal — projects/PROJ-132-statistical-analysis-of-publicly-availab/specs/001-statistical-analysis-of-publicly-availab/research.md: self-declared fabricated metric — “…ctly from observed data; **no placeholder values are introduced**.  ### 3.2 A…”. Research results must be REAL measurements, never simulated / placeholder / hardcoded / drawn from random.*. The reviser must replace this with a genuine computation before the stage advances.
