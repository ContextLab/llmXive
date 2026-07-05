# Research: Predicting Coating Adhesion Strength from Composition and Surface Features

## Dataset Strategy

### Verified Datasets & Sources

**CRITICAL CONSTRAINT**: The plan MUST use ONLY the verified dataset URLs provided in the project's `# Verified datasets` block.
- **NIST (jsonl)**: ` (Note: **INVALID**. This URL contains medical conversation data, not surface metrology. The spec requires NIST Surface Metrology Repository data, but NO verified source for the *correct* NIST Surface data is provided in the block.)
- **Materials Project**: **NO VERIFIED URL PROVIDED**.
- **Open-access Literature (Adhesion)**: **NO VERIFIED URL PROVIDED**.

**Gap Analysis**:
The specification explicitly requires data from:
1. **Materials Project API** (for compositional data)
2. **NIST Surface Metrology Repository** (for surface roughness/metrology)
3. **Open-access literature sources** (for adhesion strength measurements)

However, the `# Verified datasets` block provided in the user message **contains NO verified URLs** for any of these required sources. The listed URLs are for medical conversations, LLM benchmarks, and medical RMSE/MAE data, which are **completely irrelevant** to coating adhesion strength prediction.

**Action**:
- **DO NOT** fabricate URLs.
- **DO NOT** proceed with the plan assuming these datasets exist at the listed URLs.
- **State explicitly**: The project cannot proceed to Phase 1 (data ingestion) until verified sources for the Materials Project API, NIST Surface Metrology, and relevant literature are provided.
- **Recommendation**: The spec's assumption that these sources are "accessible" is invalid without verified URLs. The plan must flag this as a **blocking gap**.

### Blocking Gap Statement

**CURRENT STATUS: PROJECT HALTED**.
The modeling pipeline cannot be constructed or executed because:
1. No verified URL exists for the NIST Surface Metrology Repository (current URL is for medical data).
2. No verified URL exists for the Materials Project API.
3. No verified URL exists for open-access literature sources containing adhesion strength measurements.
4. Without unique identifiers or verified cross-references between these sources, the required data alignment is impossible without introducing fatal scientific errors (spurious correlations).

**Next Step**: Obtain and verify correct dataset URLs. Until then, the project remains in "Data Gap Analysis" mode.

### Hypothetical Data Structure (For Planning Only)

*If* the correct datasets were available, the structure would be:

| Source | Expected Columns | Role in Model |
|--------|------------------|---------------|
| **Materials Project API** | `material_id`, `elemental_composition`, `band_gap`, `formation_energy` | Compositional features (predictors) |
| **NIST Surface Metrology** | `sample_id`, `Ra`, `Rq`, `Rsk`, `Rku`, `bearing_area` | Surface features (predictors) |
| **Literature (Adhesion)** | `coating_id`, `substrate_id`, `adhesion_strength`, `test_method`, `publication_date` | Target variable + alignment keys |

### Mapping Protocol (FR-007) - REJECTED

**Status**: The proposed 'heuristic mapping' (matching by chemical formula and substrate name) is **REJECTED** due to high risk of misalignment and spurious correlations.

**New Protocol**:
1. **Unique Identifier Requirement**: Records from bulk databases (Materials Project) and specific coating formulations (Literature) MUST be linked via a unique, verified identifier (e.g., a specific sample ID or DOI).
2. **Rejection of Unmappable Records**: Any record pair that cannot be linked via a unique identifier will be **REJECTED** and logged.
3. **No Heuristic Matching**: Heuristic matching by chemical formula or substrate name is prohibited due to variability in coating formulations (e.g., stoichiometry, dopants, processing history).

**Risk**: This strict protocol may result in a small final dataset. However, it is necessary to ensure scientific validity. If the final dataset is too small (<1,000 rows), the project will halt (see Power Analysis).

## Modeling Strategy

### Algorithms

1. **Gradient Boosting Regressor (GBR)**:
 - Library: `scikit-learn` (`GradientBoostingRegressor`)
 - Rationale: Handles non-linear relationships, robust to outliers, provides feature importance.
 - Constraints: CPU-only, limited depth (max_depth=3-5) to prevent overfitting and ensure runtime.

2. **Random Forest Regressor (RFR)**:
 - Library: `scikit-learn` (`RandomForestRegressor`)
 - Rationale: Ensemble method, robust to noise, provides feature importance.
 - Constraints: CPU-only, limited trees (n_estimators=100) to ensure runtime.

3. **Baselines**:
 - **Composition-only**: Same models trained on compositional features only.
 - **Surface-only**: Same models trained on surface features only.

### Validation Strategy

- **Nested 5-Fold Cross-Validation**:
 - Outer loop: 5 folds for performance estimation.
 - Inner loop: 5 folds for hyperparameter tuning (e.g., `n_estimators`, `max_depth`).
 - **Purpose**: Prevent data leakage and provide unbiased performance estimates (FR-003).

- **Metrics**:
 - Primary: R², RMSE, MAE.
 - Secondary: Feature importance stability (Spearman correlation between SHAP and permutation importance).

### Feature Engineering

1. **Compositional Features (FR-002)**:
 - **One-hot encoding**: Elemental composition (e.g., "Fe": 1, "O": 2, etc.).
 - **Derived descriptors**:
 - Atomic radius variance: Variance of atomic radii of constituent elements.
 - Electronegativity variance: Variance of electronegativities.
 - **Crosslinker density proxy**: Heuristic ratio based on C/H/O ratios (FR-008). **Must be validated** against theoretical models before use (Construct Validity Assessment).

2. **Surface Features (FR-002)**:
 - **Standardization**: Ra, Rq, Rsk, Rku normalized to [0, 1].
 - **Derived**: Bearing area curve parameters.

3. **Sensitivity Analysis (FR-008)**:
 - Test at least three definitions of "crosslinker density" (e.g., C/H ratio, C/O ratio, (C+H)/O).
 - Report variance in model performance (R²) across definitions.

## Statistical Rigor & Assumptions

### Multiple Comparison Correction (FR-005)

- **Tests**:
 1. Full vs. Composition-only.
 2. Full vs. Surface-only.
- **Correction**: Bonferroni correction applied to p-values (alpha = 0.05 / 2 = 0.025).
- **Method**: Nadeau & Bengio corrected t-test (accounts for dependence in CV folds).

### Causal Inference & Limitations

- **Observational Nature**: The study is observational; no randomization of coating/substrate pairs.
- **Claims**: All claims are **associational**, not causal. "Feature X is associated with higher adhesion" rather than "Feature X causes higher adhesion."
- **Collinearity**: Compositional and surface features may be correlated (e.g., certain coatings inherently have rougher surfaces).
 - **Handling**: Report collinearity (VIF) and acknowledge that independent effects cannot be disentangled.
 - **Descriptor**: If one feature is derived from another (e.g., crosslinker density from C/H/O), do NOT claim independent effects; report descriptively.

### Power & Sample Size

- **Assumption**: ≤5,000 records provide sufficient power to detect R² ≈ 0.6–0.7 (Spec Assumption).
- **Limitation**: If the actual dataset is smaller (<1,000 rows), power may be insufficient.
- **Mitigation**: If data is scarce, report power limitation explicitly and focus on effect sizes rather than p-values. **Halt** if N < 1,000.

### Measurement Validity

- **Adhesion Strength**: Only ASTM D pull-off test data included (FR-009).
- **Surface Metrics**: NIST metrology standards assumed valid.
- **Compositional Data**: Materials Project data assumed accurate for bulk properties.

## Compute Feasibility

- **Hardware**: GitHub Actions free-tier (limited CPU, limited RAM, no GPU).
- **Memory Management**:
 - Sample dataset to ≤5,000 rows (FR-006).
 - Use `pandas` chunking if raw data >7 GB.
 - Avoid large intermediate dataframes.
- **Runtime**:
 - Target: <4 hours (SC-004).
 - Models: GBR and RFR with limited depth/trees should complete in <1 hour for [deferred] rows.
 - SHAP: CPU-based SHAP (kernel SHAP or tree SHAP) may require a substantial amount of time.; optimize with `approximate=True` if needed.
- **Libraries**:
 - `scikit-learn` (CPU-only, well-optimized).
 - `shap` (CPU support, but may require sampling for large datasets).
 - `pandas`, `numpy` (standard, efficient).

## Risk Mitigation

1. **Dataset Mismatch**:
 - **Risk**: No verified URLs for required datasets.
 - **Mitigation**: **HALT** at Phase 0. Do not proceed with mock data.
2. **API Rate Limits**:
 - **Risk**: Materials Project API rate limiting.
 - **Mitigation**: Implement exponential backoff (3 retries) in `ingestion.py`.
3. **Memory Overflow**:
 - **Risk**: Raw data exceeds 7 GB.
 - **Mitigation**: Sample to [deferred] rows immediately after ingestion. Use chunked processing.
4. **Runtime Exceedance**:
 - **Risk**: SHAP or CV takes >6 hours.
 - **Mitigation**: Limit SHAP to a subset of the most influential features. Use fewer CV folds (if justified) or approximate SHAP.
5. **Data Alignment Failure**:
 - **Risk**: No unique identifiers between sources.
 - **Mitigation**: **REJECT** unmappable records. Do not use heuristic mapping. Report count of rejected records.

## Decision Rationale

- **Why Gradient Boosting & Random Forest?**
 - Robust, interpretable, and CPU-efficient.
 - Provide feature importance directly.
 - No deep learning required (avoids GPU dependency).

- **Why Nested CV?**
 - Prevents data leakage in hyperparameter tuning.
 - Provides unbiased performance estimates.

- **Why Strict Rejection of Heuristic Mapping?**
 - Unique identifiers are absent between bulk databases and specific formulations.
 - Heuristic matching introduces spurious correlations and invalidates scientific claims.

- **Why Bonferroni Correction?**
 - Multiple hypothesis tests (full vs. baselines) require correction to control family-wise error rate.

## References

- **Materials Project**: (No verified URL provided; must be sourced).
- **NIST Surface Metrology**: (No verified URL provided; must be sourced).
- **SHAP**: (No verified URL provided; library documentation assumed).
- **Nadeau & Bengio (2003)**: "Inference for the Generalization Error" (standard for CV comparisons).

**Note**: All dataset URLs in this document are placeholders. The actual implementation MUST use verified URLs from the project's `# Verified datasets` block. Currently, **no such URLs exist** for the required data sources, making this a blocking issue.