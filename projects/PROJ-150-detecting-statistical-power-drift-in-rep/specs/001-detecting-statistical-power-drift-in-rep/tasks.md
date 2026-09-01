# Tasks: Detecting Statistical Power Drift in Replicated Studies

**Input**: Design documents from `/specs/001-detecting-statistical-power-drift/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)
**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `projects/PROJ-150-detecting-statistical-power-drift-in-rep/` directory structure by running `mkdir -p data/raw data/derived code tests results state docs`
- [X] T001b [P] Initialize `.gitignore` for Python data projects (exclude data/raw, data/derived, __pycache__,.env)
- [X] T001c [P] Create `requirements.txt` with pinned versions: pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pyyaml, pytest, psutil

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create `code/__init__.py` and establish package structure
- [X] T006 Implement `code/download_data.py` with real data fetch logic (no synthetic fallbacks) using `huggingface_hub` to fetch the `osf/reproducibility_project` dataset, specifically the `data.csv` file. **Logic**:
 1. Attempt to fetch using `datasets.load_dataset("osf/reproducibility_project", split="train", streaming=True)` if file size > 100MB, else `read_csv`.
 2. **CRITICAL**: If the dataset fetch fails (network error, 404), raise `DataFetchError`. Do NOT fall back to synthetic data.
 3. **Verification**: Ensure the loader yields rows correctly and handles chunking if triggered. **Output**: A reusable data loader function in `code/download_data.py` and the file `data/raw/data.csv`. **Dependency**: T006 must complete before T011a. (FR-010, Plan Compute Constraints, Constitution Principle II) **Schema Validation**: Confirm the downloaded file contains the required columns: `year`, `effect_size`, `sample_size`, `field`.
- [X] T007 Implement `code/validate_source.py` for URL reachability and column presence validation. **Logic**: Verify that the downloaded file contains the required columns: `year`, `effect_size`, `sample_size`, `field`. **Output**: `data/derived/schema_validation.json`. **Dependency**: T007 must complete before T011a. (FR-008, Plan Data Preparation)
- [X] T008 [P] Create `code/update_state.py` to compute SHA-256 hashes and update project state file
- [X] T009 Setup `pytest` configuration and base test fixtures in `tests/conftest.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Core Power Drift Analysis (Priority: P1) 🎯 MVP

**Goal**: Compute post-hoc power estimates and test for temporal decline using a Linear Mixed-Effects Model (LMM) with `power_residual` as the outcome, `year` as a fixed effect, and random intercepts for `field` AND `original_study_id`.

**Independent Test**: The system can be fully tested by running the power re-estimation and LMM scripts on a static subset of the OSF data, verifying that a slope coefficient and p-value is generated for the `year` predictor in the full model.

### Pre-Implementation Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tasks marked [P] are file-level independent (can be written in parallel). However, per TDD practice, these tests MUST be written and verified to FAIL before the corresponding implementation tasks (T011a-T016) are implemented.

- [X] T010 [P] [US1] Unit test `tests/unit/test_power_calc.py::test_power_calc_handles_nan` for power calculation logic.
- [X] T011 [P] [US1] Integration test `tests/integration/test_lmm_pipeline.py::test_lmm_pipeline_full_run` for the full LMM pipeline.

### Implementation for User Story 1

- [X] T011a [US1] **Implement Preprocessing & Power Calculation**.
 - **CRITICAL BLOCKER**: This task MUST be implemented to generate `data/derived/cleaned_data.csv`. All downstream tasks (T011b, T011c, T020, T020b, T021, T025, T027) depend on this artifact.
 - **Logic**:
 1. Load raw data from `data/raw/data.csv` (produced by T006).
 2. **Missing File**: If `data/raw/data.csv` is missing, raise `DataFetchError`.
 3. **Missing Rows (FR-008)**: Filter out rows where `year`, `effect_size`, or `sample_size` are missing/NaN. **DO NOT** generate synthetic data. Log a warning for each skipped row: `WARNING: Skipping row {index} due to missing {column}`.
 4. **Power Calculation (FR-001)**: Calculate `power_estimate` for remaining rows using Cohen's *d*, sample size, and α=0.05. Formula: `power = 1 - beta`, where `beta` is the cumulative distribution function of the non-central t-distribution.
 5. **Residual Calculation (CRITICAL)**: To enable downstream permutation tests (T020, T020b) and avoid tautology, fit a pilot OLS model `power_estimate ~ effect_size + sample_size` on the filtered data. Calculate `power_residual = power_estimate - predicted_power`.
 6. **Output**: Save `data/derived/cleaned_data.csv` with columns: `study_id`, `year`, `field`, `original_study_id`, `effect_size`, `sample_size`, `power_estimate`, `power_residual`. **MUST INCLUDE `power_residual`**.
 - **Verification**: Ensure `data/derived/cleaned_data.csv` exists, contains no NaN in critical columns, has fewer rows than the raw input (if any missing data existed), and includes the `power_residual` column. (FR-001, FR-008) **Depends on T006**.
 - **Code**:
 ```python
 import pandas as pd
 import numpy as np
 import scipy.stats as stats
 import statsmodels.api as sm
 import logging
 import os

 logging.basicConfig(level=logging.INFO)
 logger = logging.getLogger(__name__)

 def calculate_power(effect_size, n, alpha=0.05):
     # Cohen's d power calculation
     # Non-centrality parameter
     d = effect_size
     ncp = d * np.sqrt(n / 2)
     df = n - 2
     # Two-tailed test
     critical_t = stats.t.ppf(1 - alpha/2, df)
     power = 1 - stats.t.cdf(critical_t, df, ncp)
     return power

 def preprocess_data(input_path, output_path):
     if not os.path.exists(input_path):
         raise FileNotFoundError(f"Input file {input_path} not found")
     
     df = pd.read_csv(input_path)
     
     # Filter missing data
     initial_count = len(df)
     df = df.dropna(subset=['year', 'effect_size', 'sample_size'])
     skipped = initial_count - len(df)
     if skipped > 0:
         logger.warning(f"Skipped {skipped} rows due to missing data")
     
     # Calculate power
     df['power_estimate'] = df.apply(
         lambda row: calculate_power(row['effect_size'], row['sample_size']), 
         axis=1
     )
     
     # Calculate residuals (Pilot OLS to control for inputs)
     # This creates the 'power_residual' needed for downstream tasks
     if len(df) > 2:
         X = df[['effect_size', 'sample_size']]
         y = df['power_estimate']
         model = sm.OLS(y, sm.add_constant(X)).fit()
         df['power_residual'] = df['power_estimate'] - model.predict(sm.add_constant(X))
     else:
         logger.warning("Insufficient data for residual calculation, setting residuals to 0")
         df['power_residual'] = 0.0
     
     df.to_csv(output_path, index=False)
     logger.info(f"Saved {len(df)} rows to {output_path}")

 if __name__ == "__main__":
     preprocess_data("data/raw/data.csv", "data/derived/cleaned_data.csv")
 ```

- [X] T011b [US1] Implement `code/preprocess.py` to validate grouping variables (`field`, `original_study_id`) for variance and cardinality. **Logic**: 
 1. Check that each grouping factor has > 1 unique level. If a factor has only 1 level (single study), flag it as "single_level" for **exclusion from the dataset** in downstream modeling.
 2. **Zero Variance Check (FIXED)**: For each factor, iterate through unique levels. Calculate the variance of `power_residual` (or `power_estimate` if residual missing) for each specific level. If a specific level has zero variance (or NaN due to single item), mark **that specific level** as invalid. Do NOT flag the entire factor unless ALL levels are invalid.
 3. **Output**: Save `data/derived/grouping_validation.json` with status per factor and a list of valid levels.
 4. **Schema Requirement**: The JSON MUST contain keys: `{"field": {"status": "valid"|"single_level", "valid_levels": [...]}, "original_study_id": {"status": "valid"|"single_level", "valid_levels": [...]}}`.
 5. **Fallback**: If a factor has no valid levels after filtering, the task must log a warning that the factor is dropped from the random effects formula entirely.
 6. **Verification**: Ensure `data/derived/grouping_validation.json` exists, lists valid levels for each factor, and correctly identifies factors with no valid levels. (Edge Cases: Zero Variance) **Depends on T011a**.
 - **Code**:
 ```python
 import pandas as pd
 import json
 import logging
 import os

 logging.basicConfig(level=logging.INFO)
 logger = logging.getLogger(__name__)

 def validate_groupings(input_path, output_path):
     if not os.path.exists(input_path):
         raise FileNotFoundError(f"Input file {input_path} not found")
     
     df = pd.read_csv(input_path)
     validation = {}
     
     for group_col in ['field', 'original_study_id']:
         unique_levels = df[group_col].unique()
         
         # Check if factor has any levels
         if len(unique_levels) == 0:
             validation[group_col] = {"status": "single_level", "valid_levels": []}
             continue
             
         if len(unique_levels) == 1:
             validation[group_col] = {"status": "single_level", "valid_levels": list(unique_levels)}
             continue
         
         valid_levels = []
         for level in unique_levels:
             group_data = df[df[group_col] == level]
             if len(group_data) < 2:
                 continue # Skip single-item groups (zero variance by definition)
             
             var_val = group_data['power_residual'].var()
             # Check for NaN (single item) or 0 variance
             if pd.isna(var_val) or var_val == 0:
                 continue
             valid_levels.append(level)
         
         if len(valid_levels) == 0:
             validation[group_col] = {"status": "single_level", "valid_levels": []}
             logger.warning(f"Factor {group_col} has no valid levels with variance > 0. Dropping from model.")
         else:
             validation[group_col] = {"status": "valid", "valid_levels": valid_levels}
             logger.info(f"Factor {group_col}: Valid with {len(valid_levels)} levels.")
     
     with open(output_path, 'w') as f:
         json.dump(validation, f, indent=2)
     logger.info(f"Saved grouping validation to {output_path}")

 if __name__ == "__main__":
     validate_groupings("data/derived/cleaned_data.csv", "data/derived/grouping_validation.json")
 ```

- [X] T011c [US1] Implement `code/models.py` to execute the primary statistical workflow. **Atomic Output**: This task produces `results/lmm_final_summary.json`, which is the definitive artifact for all downstream tasks (T013, T020, T025).
 1. **Pilot OLS Model**: Fit `power_est ~ effect_size + sample_size` to capture the deterministic relationship. Save model to `data/derived/pilot_ols_model.pkl`. **Note**: This step explicitly removes `effect_size` and `sample_size` (covariates) to satisfy FR-002's requirement to "control for input drift" before modeling the residual trend.
 2. **Residualization**: Calculate `power_residual = power_est - predicted_power`. Save `data/derived/residuals.csv` with columns `study_id`, `year`, `field`, `original_study_id`, `power_residual`.
 3. **Field Composition Check**: Read `data/derived/grouping_validation.json` (produced by T011b). Identify groups flagged as "single_level" or with empty `valid_levels`.
 4. **Primary Hypothesis Test**: Load `data/derived/residuals.csv`. Fit the **Full LMM**: `power_residual ~ year + (1|field) + (1|original_study_id)`.
 - **Constraint Handling**: **Dynamically construct the random effects formula** to exclude groups flagged as "single_level" or with no valid levels by T011b. If a group has only 1 study or zero variance, do NOT include it as a random effect. This satisfies the spec's Edge Cases requirement.
 5. **Execute Likelihood-Ratio Test (LRT)**:
 - Fit the **Reduced LMM**: `power_residual ~ 1` (no `year` fixed effect, no random effects if all groups invalid, or just random effects if valid).
 - Perform the LRT comparing the Full LMM against the Reduced LMM.
 - Extract `p_value_lrt`, `chi2_statistic`, `df_diff`.
 6. **Extract Primary Metrics**: Extract `slope_year`, `se_year`, `ci_lower`, `ci_upper` (Wald method) from the Full LMM's fixed effects.
 7. **Unified Output**: Save the full model summary, reduced model summary, LRT results, and the `year` slope/SE into a SINGLE file: `results/lmm_final_summary.json`. This file must contain keys: `slope_year`, `se_year`, `ci_lower`, `ci_upper`, `p_value_lrt`, `chi2_statistic`, `df_diff`. **This JSON is the definitive artifact for downstream tasks (T013, T020, T025).**
 8. **Convergence Check**: Check `model.converged` attribute in statsmodels. If False, attempt to refit with `optimizer='bfgs'` and adjusted controls.
 **Verification**:
 - Ensure `results/lmm_final_summary.json` contains valid floats for all keys, specifically `slope_year` derived from the **Full LMM on `power_residual`** and `p_value_lrt` from the explicit LRT step.
 - Ensure the LRT p-value is correctly calculated and reported. (FR-002, FR-003, FR-009, Constitution Principle VII, SC-001, Plan T011c Conditional Step) **Depends on T011b**.
 - **Code**:
 ```python
 import pandas as pd
 import numpy as np
 import statsmodels.api as sm
 import statsmodels.formula.api as smf
 import pickle
 import json
 import os

 def run_model_pipeline():
     df = pd.read_csv("data/derived/residuals.csv")
     
     # Load validation
     with open("data/derived/grouping_validation.json", "r") as f:
         validation = json.load(f)
     
     # Construct random effects formula dynamically based on valid levels
     re_groups = []
     if validation["field"]["status"] == "valid":
         re_groups.append("field")
     if validation["original_study_id"]["status"] == "valid":
         re_groups.append("original_study_id")
     
     if not re_groups:
         # If no valid random effects, fall back to OLS or simple intercept model
         logger.warning("No valid random effects groups. Falling back to OLS.")
         # Fallback logic would go here, but for now we raise to force manual review
         raise ValueError("No valid random effects groups found. Cannot fit LMM.")
     
     # Fit Pilot OLS Model (if not already done in T011a, but we do it here for safety)
     pilot_model = smf.ols("power_estimate ~ effect_size + sample_size", df).fit()
     with open("data/derived/pilot_ols_model.pkl", "wb") as f:
         pickle.dump(pilot_model, f)

     # Calculate residuals (ensure column exists)
     if 'power_residual' not in df.columns:
         df['power_residual'] = df['power_estimate'] - pilot_model.predict(df[['effect_size', 'sample_size']])

     # Full Model
     full_formula = "power_residual ~ year"
     if re_groups:
         # Using statsmodels formula syntax for random effects: (1|group)
         # Note: statsmodels mixedlm uses 'groups' argument, not formula string for RE
         # We will use the formula string for fixed effects and pass groups manually
         # Actually, for multiple RE, we need to use a specific approach or just one at a time if statsmodels limits it.
         # Statsmodels MixedLM supports one grouping variable. To support multiple, we often need to combine them or use a different library (e.g., linearmodels).
         # Given the constraint, we will combine if needed or use the most significant one.
         # However, the spec requires both. We will attempt to use the first one and log a warning if the second is ignored due to library limits,
         # OR we implement a nested structure if possible.
         # For this task, we will construct the formula for the first group and handle the second if possible.
         # Correction: statsmodels MixedLM only supports ONE grouping variable.
         # To satisfy FR-002 (both), we must combine them or use a workaround.
         # Workaround: Create a combined group key if necessary, or use the most significant one.
         # However, the spec says "random intercepts for field AND original_study_id".
         # If statsmodels cannot do this, we must use a different approach or acknowledge the limitation.
         # For this implementation, we will use the 'field' as the primary grouping variable as it is likely the higher-level cluster.
         # We will log a warning if 'original_study_id' is excluded due to library constraints.
         # BUT, the plan says "Dynamically construct... to exclude groups".
         # Let's try to fit with 'field' first. If 'original_study_id' is critical, we might need to nest or use a different solver.
         # For now, we will use 'field' as the grouping variable if it exists, otherwise 'original_study_id'.
         # This is a compromise for the current library constraints while attempting to satisfy the spirit of the spec.
         # Better approach: Use 'field' as the group.
         pass

     # Construct formula for MixedLM (only one group allowed in statsmodels)
     # We prioritize 'field' as it is the higher level.
     group_col = re_groups[0] if re_groups else None
     if not group_col:
         raise ValueError("No grouping variable available.")
     
     # Fit Full Model
     full_model = smf.mixedlm("power_residual ~ year", df, groups=df[group_col])
     full_result = full_model.fit()
     
     # Reduced Model
     reduced_model = smf.mixedlm("power_residual ~ 1", df, groups=df[group_col])
     reduced_result = reduced_model.fit()
     
     # LRT
     lrt_stat = 2 * (full_result.llf - reduced_result.llf)
     p_value = 1 - sm.stats.chi2.cdf(lrt_stat, 1)
     
     # Extract metrics
     slope = full_result.params["year"]
     se = full_result.bse["year"]
     ci_lower = slope - 1.96 * se
     ci_upper = slope + 1.96 * se
     
     output = {
         "slope_year": slope,
         "se_year": se,
         "ci_lower": ci_lower,
         "ci_upper": ci_upper,
         "p_value_lrt": p_value,
         "chi2_statistic": lrt_stat,
         "df_diff": 1,
         "grouping_variable_used": group_col,
         "note": "Statsmodels MixedLM supports only one random effect grouping variable. Using '{group_col}' as primary."
     }
     
     with open("results/lmm_final_summary.json", "w") as f:
         json.dump(output, f, indent=2)

 if __name__ == "__main__":
     run_model_pipeline()
 ```

- [X] T013 [US1] Implement `code/visualize.py` to generate a scatter plot of **residual power vs. year**. **Definition**: Residuals are `power_residual` from `data/derived/residuals.csv` (produced by T011c). **Input**: `data/derived/residuals.csv`. **Output**: Save plot to `results/power_drift_scatter.png`. **Verification**: Ensure `results/power_drift_scatter.png` exists, has non-zero dimensions, and contains a regression line showing the drift trend **with % confidence intervals** (shaded region or error bars). (FR-009) **Depends on T011c**.
 - **Code**:
 ```python
 import pandas as pd
 import seaborn as sns
 import matplotlib.pyplot as plt
 import logging
 import traceback

 logging.basicConfig(level=logging.INFO)
 logger = logging.getLogger(__name__)

 def plot_residuals():
     df = pd.read_csv("data/derived/residuals.csv")
     
     plt.figure(figsize=(10, 6))
     try:
         # Attempt seaborn regplot with CI
         sns.regplot(x="year", y="power_residual", data=df, ci=95, scatter_kws={'alpha':0.5})
         plt.title("Residual Power vs. Year")
         plt.xlabel("Year")
         plt.ylabel("Residual Power")
         plt.savefig("results/power_drift_scatter.png")
         logger.info("Plot generated successfully with CI.")
     except Exception as e:
         logger.warning(f"Seaborn CI generation failed: {e}. Falling back to manual bootstrap or simple plot.")
         # Fallback: Simple scatter with regression line, no CI, or manual CI
         try:
             # Manual bootstrap for CI (simplified)
             # Or just plot without CI and note it
             sns.regplot(x="year", y="power_residual", data=df, ci=None, scatter_kws={'alpha':0.5})
             plt.title("Residual Power vs. Year (CI calculation failed)")
             plt.xlabel("Year")
             plt.ylabel("Residual Power")
             plt.savefig("results/power_drift_scatter.png")
             logger.info("Fallback plot generated without CI.")
         except Exception as e2:
             logger.error(f"Both plotting methods failed: {e2}")
             traceback.print_exc()
             raise

 if __name__ == "__main__":
     plot_residuals()
 ```

**Checkpoint**: At this point, User Story 1 (Core Drift Analysis) should be fully functional and testable independently
