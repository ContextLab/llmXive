# Tasks: The Impact of Incidental Music on Autobiographical Memory Retrieval

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/`
**Research Question**: Does exposure to music during adolescence produce uniquely vivid and emotionally salient autobiographical memories compared to music exposure during other developmental periods?

## Phase 1: Setup and first end-to-end analysis

**Goal**: Establish the pipeline skeleton and run a thin, end-to-end analysis on a small simulated sample to verify the statistical flow.

- [ ] T000 Initialize `state.yaml` with the required structure (`artifact_hashes`, `updated_at`, `config`) as a blocking prerequisite for all subsequent data tasks and checksumming. <!-- FAILED-IN-EXECUTION: code/init_state.py exit=1 -->
- [ ] T001 Establish the project layout (`code/`, `data/raw/`, `data/processed/`, `data/final/`, `tests/`), `requirements.txt` (including `statsmodels`, `pyarrow`, `levenshtein`), and `code/config.py` containing thresholds (Levenshtein $\le 4$, `MATCH_RATE_THRESHOLD=0.8`) and seeds. Document the execution command in `quickstart.md`.
- [ ] T002 Implement the data contracts in `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` to define the User-Track Pair analysis dataset and the regression/permutation outputs.
    - Verification: The contract files must pass `jsonschema` validation and match the requirements in `spec.md`.
- [ ] T003 Implement a "thin" end-to-end pipeline in `code/main.py` using a small mock dataset to produce the first real result rows. This must exercise the basic flow: `simulate_amt.py` $\rightarrow$ `ingest.py` $\rightarrow$ `aggregate.py` $\rightarrow$ `model.py`.
    - Output: `data/processed/ingested_cohort.parquet`, `data/processed/user_track_pairs.parquet`, and `data/final/regression_summary.csv`.
    - Verification: The `regression_summary.csv` must contain the required columns (`term`, `estimate`, `std_error`, `t_value`, `p_value`, `vif`) as per the output contract.

**Checkpoint**: The documented command executes and produces numerically valid result rows in `data/final/`.

## Phase 2: Complete the study and validate its evidence

**Goal**: Implement the full-scale data processing, robust handling of edge cases, and the complete statistical suite.

- [ ] T004 [US1] Implement full data ingestion and exposure scoring in `code/data/ingest.py` and `code/data/aggregate.py`. <!-- FAILED-IN-EXECUTION: code/data_ingestion.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
    - **MSD Schema Validation**: Before ingestion, verify the MSD source contains `track_id`, `release_date`, and `popularity`; fail with a clear error if missing.
    - Implement the **Global Exposure Fallback** (FR-008) as a population-level proxy for missing individual data to be used as a predictor; ensure the fallback check for missing birth years ($>50\%$) occurs **before** any listen-count filtering (EC-001).
    - Implement the **Minimum Listen Threshold** (FR-009: `total_listens >= 3`) and the raw `adolescent_exposure_ratio` calculation (FR-001).
    - Output: `data/processed/ingested_cohort.parquet`.
    - Verification: Unit tests in `tests/unit/test_ingestion.py` must verify that the fallback trigger correctly identifies missing birth year proportions and that the listen threshold is applied last.
- [ ] T005 [US2] Implement the cue matching and aggregation logic in `code/data/match.py` and `code/data/aggregate.py`.
    - Implement Levenshtein distance matching ($\le 4$) and the **Match Rate Verification** (SC-004: log warning if rate $< 80\%$ but proceed).
    - Implement the **User-Track Pair aggregation** (FR-004) and filter out **Zero Variance Tracks** (EC-002: `n_cues == 0`).
    - Output: `data/processed/user_track_pairs.parquet`.
    - Verification: `data/logs/match_rate_stats.json` must record the actual match rate; `user_track_pairs.parquet` must strictly adhere to `contracts/user_track_pair.schema.yaml`.
- [ ] T006 [US3] Implement the primary statistical analysis in `code/analysis/model.py`.
    - Fit the Linear Mixed-Effects Model (LMM) (FR-005): `mean_vividness ~ adolescent_exposure_ratio + popularity + (1|user_id)`. **Note**: Use the raw ratio per spec; ignore the logit transformation suggested in `plan.md`.
    - Implement the **Multicollinearity Check** (EC-003): calculate VIF for predictors and log a warning if $\text{VIF} > 5$.
    - Output: `data/final/regression_summary.csv` and diagnostic plots in `data/final/plots/` (residuals, QQ plot).
    - Verification: VIF values must be present in the regression summary; diagnostic plots must be non-empty.
- [ ] T007 [US3] Implement the **Sensitivity Analysis** loop (FR-006) in `code/analysis/sensitivity.py`.
    - For each Levenshtein threshold in $[1, 2, 3, 4, 5]$, re-run the matching and aggregation process and re-fit the LMM.
    - Output: `data/final/sensitivity_analysis.csv`.
    - Verification: The output CSV must contain one row per threshold with the corresponding coefficient and p-value.
- [ ] T008 [US3] Implement the **Block-Permutation Test** (FR-007) in `code/analysis/permutation.py`.
    - Shuffle `mean_vividness` within each `user_id` block for 5,000 iterations (seed 42) while keeping predictors fixed.
    - Compare the observed coefficient against the null distribution to calculate the final p-value.
    - Output: `data/final/permutation_results.csv`.
    - Verification: Unit tests must verify that `user_id` blocks are preserved during shuffling (no leakage across users).

**Checkpoint**: All required runs complete; artifacts match the actual computations and adhere to the defined schemas.

## Phase 3: Reproducible results and paper handoff

**Goal**: Ensure full reproducibility and prepare the final evidence package.

- [ ] T009 Verify all final artifacts. Recompute SHA-256 checksums for `data/processed/*.parquet` and `data/final/*.csv`, comparing them against `state.yaml`. Run a final contract test in `tests/contract/test_data_flow.py` to ensure the final results strictly match `contracts/output.schema.yaml`.
- [ ] T010 Generate the final research account in `report.md`. This must link to the actual output cells in `data/final/`, describe the observed effect of adolescent exposure on vividness, and honestly document any failures (e.g., match rate warnings or VIF issues).
- [ ] T011 Document the paper-stage handoff. Re-run the entire documented workflow from `quickstart.md` to confirm it completes within the 6-hour budget and maintains memory usage $< 5\text{GB}$ via streaming.

## Dependencies and requirement coverage

| Requirement | Task | Verification |
| :--- | :--- | :--- |
| FR-001: Raw Exposure Ratio | T004 | `tests/unit/test_ingestion.py` |
| FR-004: User-Track Pair Unit | T005 | `contracts/user_track_pair.schema.yaml` |
| FR-005: LMM Model | T006 | `data/final/regression_summary.csv` |
| FR-006: Sensitivity Analysis | T007 | `data/final/sensitivity_analysis.csv` |
| FR-007: Block-Permutation | T008 | `data/final/permutation_results.csv` |
| FR-008: Global Fallback | T004 | `tests/unit/test_ingestion.py` |
| FR-009: Min Listen Threshold | T004 | `user_track_pairs.parquet` (min 3) |
| SC-004: Match Rate Warning | T005 | `data/logs/match_rate_stats.json` |
| EC-001: Fallback Order | T004 | `tests/unit/test_ingestion.py` |
| EC-002: Zero Var Filtering | T005 | `user_track_pairs.parquet` (n_cues $\ge 1$) |
| EC-003: VIF Warning | T006 | `data/final/regression_summary.csv` |

**Execution Order**: T000 $\rightarrow$ T001 $\rightarrow$ T002 $\rightarrow$ T003 $\rightarrow$ T004 $\rightarrow$ T005 $\rightarrow$ T006 $\rightarrow$ T007 $\rightarrow$ T008 $\rightarrow$ T009 $\rightarrow$ T010 $\rightarrow$ T011.