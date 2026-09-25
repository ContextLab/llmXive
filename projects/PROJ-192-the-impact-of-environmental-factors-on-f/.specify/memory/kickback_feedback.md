# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013d` (rejected 1x): The required output file `data/metadata/harmonized_matrix.csv` does not exist, and the provided `src/pipelines/ingest.py` snippet shows only ontology‑mapping utilities without any logic that merges, validates, cleans metadata, or writes the harmonized matrix CSV. Consequently the task’s core requirement is unmet.
- `T015` (rejected 1x): The `src/pipelines/preprocess.py` file contains no import or usage of `miceforest`, nor any logic for MICE imputation, convergence checking, or row dropping. Additionally, the required `data/cleaned_metadata.csv` file is absent. Both the implementation and the verification artifact are missing.
- `T018` (rejected 1x): The repository lacks the required `results/permanova_summary.csv` file, and the provided `src/pipelines/analysis.py` does not contain any implementation of PERMANOVA (adonis2) with the specified permutation logic or Benjamini‑Hochberg correction. The task’s core output and functionality are therefore missing.
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: src/pipelines/report.py
- `T022` (rejected 1x): declared artifact(s) missing/empty/invalid: results/permanova_summary.csv, results/db_rda_variance.csv
- `T026` (rejected 1x): The provided `analysis.py` does not show any logic that checks stratum sample counts and skips PERMANOVA/varpart, nor does it write to `results/skipped_strata.log`. Moreover, the required log file is absent from the repository. The power‑check implementation and the verification log entry for biome “FR-005” are missing.
- `T028` (rejected 1x): No `results/db_rda_biome_<NAME>.csv` files are present; the claim provides only a description of the expected output without any actual CSV artifacts, so the required per‑biome R² results are missing. The next implementer must generate and commit the CSV files for each biome as specified.
- `T029` (rejected 1x): declared artifact(s) missing/empty/invalid: results/biome_ranking_summary.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

