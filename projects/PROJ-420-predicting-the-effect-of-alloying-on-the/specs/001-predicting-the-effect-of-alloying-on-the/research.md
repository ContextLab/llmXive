# Research: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Executive Summary

This research plan outlines the strategy to predict the Poisson's ratio of monolithic aluminum alloys using compositional data (Cu, Mg, Si, Zn, Mn) as predictors. The study relies on extracting data from public materials repositories, applying compositional data analysis (CoDA) techniques to handle the unit-sum constraint, and training a Random Forest regressor. All findings will be explicitly framed as associational due to the observational nature of the data.

## Dataset Strategy

The project requires datasets containing:
1.  **Composition**: Atomic fractions of Cu, Mg, Si, Zn, Mn (and Al balance).
2.  **Properties**: Poisson's ratio (independent measurement) and Young's modulus.
3.  **Metadata**: Alloy type (must be monolithic, non-composite), and measurement method.

### Verified Datasets

Per the project constraints, we will attempt to access the following sources. Note: The "Verified datasets" block provided in the prompt does **not** contain a verified URL for Materials Project or NIST Materials Data Repository specifically for aluminum alloy Poisson's ratio data. The provided URLs are for LLM reasoning, medical conversations, and CUDA benchmarks.

**Critical Gap Identification**:
The spec assumes the existence of accessible public APIs for Materials Project and NIST containing the specific required fields (Poisson's ratio + specific elemental fractions). The provided "Verified datasets" list does **not** include these sources.
*   **Action**: The implementation script (`data_extraction.py`) will attempt to query the standard public endpoints for Materials Project (via `pymatgen` or REST) and NIST. However, if these are not in the "Verified datasets" block, the plan must acknowledge that the *specific* dataset URL is not pre-verified in this context.
*   **Fallback**: If the specific MP/NIST endpoints for *this specific subset* (Al alloys with Poisson's ratio) are not reachable or do not return the required fields, the pipeline will halt with a clear error (as per Edge Cases).
*   **Constraint**: We cannot invent a URL. If the "Verified datasets" block is the only allowed source, and it lacks MP/NIST, the project may be blocked unless the "Verified datasets" block is updated or the assumption in the spec is revised to use a different, verified source.

*Assumption for Plan Execution*: We proceed assuming the standard public APIs for Materials Project and NIST are accessible as per the "Assumptions" section of the spec, but we flag that the specific URL verification step must pass before data ingestion.

**Dataset Table**:

| Dataset Name | Source/Loader | Verified URL (from block) | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Materials Project (Al Alloys) | `pymatgen` / REST | *Not in Verified Block* | **Pending Verification** | Spec assumes accessibility. Must verify presence of Poisson's ratio and specific elements. |
| NIST Materials Data | `requests` / REST | *Not in Verified Block* | **Pending Verification** | Spec assumes accessibility. Must verify presence of Poisson's ratio and specific elements. |

*Note: If the "Verified datasets" block is strictly enforced as the ONLY allowed sources, and it lacks MP/NIST, the project cannot proceed without a gap resolution. For the purpose of this plan, we assume the "Assumptions" section of the spec (that APIs are accessible) holds, but the implementation must handle the failure case gracefully.*

## Methodology

### 1. Data Extraction and Filtering (FR-001, FR-002, FR-003, FR-009)
- **Source**: Materials Project and NIST.
- **Filter**: Monolithic Al alloys only.
- **Completeness**: Must have Poisson's ratio, Young's modulus, and fractions for Cu, Mg, Si, Zn, Mn.
- **Independence Check (FR-009)**: 
  - **Rule**: Retain ONLY entries where `measurement_method` is explicitly "ultrasonic" or "experimental".
  - **Fallback**: If `measurement_method` is missing or indicates "DFT", "calculated", or "derived", **exclude the entry**. Do not attempt to infer independence.
- **Unit Normalization**: Elastic constants to GPa. Composition to atomic fractions summing to 1.0.
- **Exclusion Rule**: If sum of major elements < 0.95, exclude entry (log warning).

### 2. Feature Engineering (FR-004)
- **Compositional Constraint**: Atomic fractions sum to unity, causing perfect multicollinearity in raw space.
- **Transformation**: Apply **Isometric Log-Ratio (ILR)** transformation to the 5-element composition (Cu, Mg, Si, Zn, Mn).
  - **Implementation**: Use the `compositional` Python package (specifically `compositional.transforms.ilr`) to ensure reproducibility.
  - ILR maps the simplex to real Euclidean space, removing the unit-sum constraint.
  - This allows standard regression algorithms (Random Forest) to function correctly.
- **Feature Importance Strategy (FR-006)**:
  - **Method**: Do **NOT** back-transform ILR splits.
  - **Execution**: Train Random Forest on ILR coordinates.
  - **Sensitivity Analysis**: Run Permutation Importance on the **ILR features** to get baseline importance.
  - **Aggregation**: To attribute importance to original elements (Cu, Mg, etc.), perform a **Perturbation-Based Sensitivity Analysis**:
    1. For each original element (e.g., Cu), generate a perturbed dataset by adding small Gaussian noise to the Cu fraction in the raw space.
    2. Re-transform the perturbed raw data to ILR coordinates.
    3. Predict with the trained model and measure the change in loss (MAE).
    4. The magnitude of the loss change represents the element's contribution.
  - This approach is valid and avoids the mathematical impossibility of inverting tree splits.

### 3. Modeling (FR-004, FR-005)
- **Algorithm**: Random Forest Regressor (CPU-tractable, handles non-linearity).
- **Validation**: 5-fold Cross-Validation.
- **Split**: [deferred] Train / [deferred] Test.
- **Metric**: Mean Absolute Error (MAE).
- **Computational Feasibility**: Random Forest on <1000 samples is well within 2 CPU / 7 GB RAM limits. No GPU required.

#### Statistical Power & Uncertainty
- **Sample Size Limitation**: The plan assumes ≥50 entries (per spec assumptions). If the actual dataset is smaller (e.g., N < 50), the variance of the 5-fold CV MAE estimate will be high.
- **Uncertainty Quantification**: To address this, the `modeling.py` script will perform **Bootstrap Resampling** (1000 iterations) on the CV error. For each iteration, it will resample the dataset with replacement, perform 5-fold CV, and record the MAE.
- **Output**: The final report will include the median MAE and the 95% confidence interval derived from the bootstrap distribution. This quantifies the uncertainty of the predictive accuracy claim (SC-002).

### 4. Diagnostics and Interpretation (FR-006, FR-007, FR-008)
- **Feature Importance**: Extract via the perturbation method described in Step 2.
- **Collinearity (FR-007, SC-004)**:
  - Compute Variance Inflation Factors (VIF) on the **raw** (untransformed) composition.
  - **Method**: Drop one component (Al) to avoid infinite VIF due to the sum-to-one constraint.
  - **Output**: Write VIF scores to `diagnostics.json`.
  - **Clarification**: VIF > 5 is an **expected** outcome in raw compositional space due to the unit-sum constraint. This diagnostic confirms that the ILR transformation was necessary. It does **NOT** indicate a model failure or halt the pipeline. The "flag" is redefined as a diagnostic confirmation rather than a pass/fail metric.
  - **SC-004 Compliance**: These VIF scores from `diagnostics.json` will be explicitly included in the final report to satisfy the measurement requirement.
- **Associational Framing (FR-008, SC-005)**:
  - **Mechanism**: The `analysis.py` script will programmatically inject the phrase "associational (not causal)" into the final report template for every result statement.
  - **Verification**: A unit test (`tests/unit/test_framing.py`) will verify the presence of this phrase in the generated report before the file is written. If the phrase is missing, the script will raise an error.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Not applicable. The study focuses on a single outcome (Poisson's ratio) and a single model.
- **Sample Size**: The plan assumes ≥50 entries (per spec assumptions). If the actual dataset is smaller, the 5-fold CV may have high variance. This will be reported as a limitation, and bootstrap confidence intervals will be used to quantify uncertainty.
- **Causal Inference**: The dataset is observational. The plan explicitly avoids causal language. The "effect" in the title refers to the predictive association, not a causal mechanism.
- **Measurement Validity**: The plan relies on the assumption that the source databases contain valid, independent measurements of Poisson's ratio (FR-009). If the data is derived, it will be excluded.

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
- **Method**: Random Forest (scikit-learn) is CPU-efficient. Bootstrap resampling (1000 iterations) is computationally intensive but feasible for N < 1000 on 2 cores within 6 hours.
- **Data Size**: Expected < 1000 rows.
- **Runtime**: Estimated < 3 hours for full pipeline including bootstrap.
- **GPU**: Not required. No CUDA dependencies.

## Conclusion

This research plan addresses the user's question by establishing a rigorous, reproducible pipeline for predicting Poisson's ratio from composition. It adheres to the compositional data analysis principles (ILR) and maintains scientific integrity by framing results as associational. The primary risk is the availability of the specific dataset fields in the public repositories, which will be handled by the robust error handling defined in the edge cases.