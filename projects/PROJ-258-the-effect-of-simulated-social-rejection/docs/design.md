# Design Decisions: Social Rejection and Reward Analysis

## 1. Design Type Determination

### Problem
The project must support both Within-Subjects (single-cohort) and Between-Subjects (composite) designs, but the available datasets may not always align.

### Decision
Implement a two-stage verification process in `code/ingest.py`:
1. **Single-Cohort Check**: Verify if a single dataset contains both Cyberball and Reward tasks with consistent participant IDs.
2. **Composite Fallback**: If single-cohort fails, attempt to match participant IDs across ds000208 (rejection) and ds003392 (reward).

### Rationale
- Preserves statistical power when possible (Within-Subjects is more powerful).
- Maintains feasibility when single-cohort data is unavailable.
- Explicitly flags Between-Subjects results as "associational" to avoid causal overreach.

### Implementation Details
- `verify_single_cohort(df)`: Checks for both tasks and ID consistency.
- `validate_composite_datasets(df_rejection, df_reward)`: Matches IDs across datasets.
- `log_design_switch()`: Records the transition in execution logs for traceability.

## 2. Memory Safety

### Problem
Large neuroimaging or behavioral datasets can exceed available RAM, causing crashes.

### Decision
Implement runtime memory monitoring using `psutil` with a hard threshold (default: 7 GB).

### Rationale
- Prevents silent failures or partial results.
- Ensures reproducibility across different hardware environments.
- Aligns with FR-001 (Plan Clarification) distinguishing runtime RAM from disk size.

### Implementation Details
- `get_process_memory_check()`: Returns a function that checks RAM usage.
- `log_memory_snapshot()`: Logs memory usage at key pipeline stages.
- Execution halts with exit code 1 if the threshold is exceeded.

## 3. Statistical Rigor

### Problem
Multiple comparisons in ANOVA and sensitivity analyses increase Type I error risk.

### Decision
Apply Benjamini-Hochberg FDR correction to all p-values and perform sensitivity sweeps across alpha thresholds.

### Rationale
- Controls false discovery rate while maintaining statistical power.
- Demonstrates robustness of findings across different significance levels.
- Aligns with FR-004 (FDR) and FR-006 (Sensitivity Analysis).

### Implementation Details
- `apply_fdr(p_values)`: Uses `statsmodels.stats.multitest.multipletests`.
- `sensitivity_sweep(df, alpha_set)`: Runs analyses at α ∈ {0.01, 0.05, 0.1}.
- Results include both raw and FDR-corrected p-values.

## 4. Phrasing and Causal Claims

### Problem
Between-Subjects designs cannot support causal claims about "modulation" of reward by rejection.

### Decision
Enforce "associational" phrasing in the final report when `design_type == "Between-Subjects"`.

### Rationale
- Prevents scientific overreach.
- Maintains integrity of the analysis pipeline.
- Aligns with FR-003 (Associational Framing) and FR-008 (Design Type Recording).

### Implementation Details
- `generate_report_logic(results, design_type)`: Selects phrasing based on design type.
- `verify_report_constraints()`: Unit test asserts "associational" is present and "causal" is absent in Limitations.
- Explicitly drops "modulation" claims for Between-Subjects results.

## 5. Data Integrity

### Problem
Raw data must be preserved with integrity checks to ensure reproducibility.

### Decision
Generate SHA-256 checksums immediately after download, before any validation or processing.

### Rationale
- Adheres to Constitution Principle III (Data Integrity).
- Allows verification of data corruption or tampering.
- Provides a clear audit trail.

### Implementation Details
- `calculate_file_hash(filepath)`: Computes SHA-256 hash.
- `save_checksums(checksums_dict, output_path)`: Writes to `data/raw/checksums.json`.
- Executed as the first step in the ingestion pipeline.

## 6. Convergence and Small N

### Problem
Small sample sizes (N < 30) may lead to unstable estimates and wide confidence intervals.

### Decision
Issue convergence warnings and report effect size confidence intervals for all analyses.

### Rationale
- Alerts users to potential limitations in statistical power.
- Provides transparent reporting of uncertainty.
- Aligns with FR-005 (Small N Handling).

### Implementation Details
- `calculate_effect_size_ci(results)`: Computes confidence intervals for effect sizes.
- `run_analysis_pipeline()`: Checks N and issues warnings if N < 30.
- Warnings are included in the final report.

## 7. Outlier Handling

### Problem
Reaction times and behavioral data often contain extreme values that skew results.

### Decision
Use IQR-based outlier detection per Condition group, with capping rather than removal.

### Rationale
- Preserves sample size while reducing outlier influence.
- Group-specific thresholds account for condition-specific variability.
- Aligns with FR-002 (Outlier Handling).

### Implementation Details
- `detect_outliers_iqr(df, group_col='Condition')`: Flags outliers using 1.5×IQR rule.
- Outliers are capped at the IQR bounds, not removed.
- Flagged outliers are recorded in the preprocessed data.

## 8. Pipeline Modularity

### Problem
The pipeline must support independent testing and incremental development of user stories.

### Decision
Structure the codebase into discrete, testable modules: `ingest.py`, `preprocess.py`, `analysis.py`, `report.py`.

### Rationale
- Enables parallel development of user stories.
- Facilitates unit and integration testing.
- Allows independent validation of each pipeline stage.

### Implementation Details
- Each module has a `run_*_pipeline()` function for end-to-end execution.
- Tests in `tests/` correspond to each user story.
- `config.py` centralizes paths and parameters for easy modification.
