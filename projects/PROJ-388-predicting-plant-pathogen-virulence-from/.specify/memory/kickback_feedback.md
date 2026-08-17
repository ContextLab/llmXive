# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T026` (rejected 1x): The provided `phylogeny.py` never extracts genes from `data/raw/*.fna`; it merely expects a pre‑existing `data/processed/housekeeping_genes.fasta` and raises an error if it is absent. That output file is missing, so the core requirement (extract rpoB, gyrB, 16S and write them to the specified FASTA) is not fulfilled.
- `T020c` (rejected 1x): The `src/data/merge.py` file is truncated (e.g., an unfinished `detect_aggregation_need` definition) and does not contain the logic to merge `species_aggregates.parquet` or write `data/processed/merged_dataset.parquet`. Moreover, the required output file `data/processed/merged_dataset.parquet` is absent. The task’s core requirement is therefore unmet.
- `T027` (rejected 1x): The required output files `data/processed/tree.newick` and `data/processed/phylo_covariance_matrix.npy` are absent, and the provided `src/analysis/phylogeny.py` is incomplete (truncated) with no implementation of Maximum Likelihood tree construction or writing of the specified artifacts. The task’s core requirements are therefore not met.
- `T028b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/analysis/correlation.py, data/processed/merged_dataset.parquet, data/processed/tree.newick, data/processed/raw_correlations.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

