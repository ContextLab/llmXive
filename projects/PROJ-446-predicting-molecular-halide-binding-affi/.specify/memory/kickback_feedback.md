# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Functional Requirement FR-003 ('System MUST filter the dataset to retain only host molecules with ≥3 different halide measurements') is not mapped to any implementation task in the plan. No T‑ID lists FR-003, leaving this requirement unaddressed.
- The ‘Verified Datasets’ block cites a SMILES parquet file, a WebBook CSV placeholder, a PubChem parquet file, and an RDKit descriptor parquet. None of these sources contain experimental halide‑binding constants, which are required by FR‑001 to attempt a real‑data scrape. Using these URLs therefore provides the wrong dataset for the primary research question; the plan cannot satisfy the requirement to obtain halide‑specific binding data from NIST or PubChem.
- The plan states that `report.md` is validated against `contracts/output.schema.yaml` (Task T008), but `output.schema.yaml` is a JSON Schema describing a JSON object, not a Markdown file. This creates a mismatch between the artifact type and its contract; either the report should be a JSON file or a separate validation step for the Markdown should be defined.
- Principle V requires that every artifact change updates `state.yaml` with a content hash. The plan mentions this in the Constitution Check table but does not include an explicit task that runs the Advancement‑Evaluator to record hashes after each script execution. Add a task (e.g., T012) that invokes the Advancement‑Evaluator after each artifact is written.
- Bootstrap confidence intervals for pairwise halide performance differences are computed from only 5 cross‑validation folds (GroupKFold). Resampling such a small set (10 000 bootstrap samples) can severely underestimate uncertainty and produce over‑confident CIs. Recommend augmenting the CV scheme (e.g., repeated GroupKFold or nested CV) to obtain a larger effective sample size before bootstrapping, or use a permutation test that respects the limited number of folds.
