# Research: Assessing the Validity of Statistical Power in Publicly Available Pre-Registered Studies

## 1. Research Question & Hypothesis

**Primary Question**: Is there a systematic discrepancy (Power Gap) between the statistical power planned in pre-registered studies and the sensitivity power achieved given the actual sample sizes?

**Reframed Hypothesis**:
1. **Execution Fidelity**: Planned sample sizes are systematically larger than actual sample sizes, leading to a positive "Power Gap" (Planned Power > Sensitivity Power). This measures adherence to the plan.
2. **Planning Accuracy (Secondary)**: Assumed effect sizes in pre-registrations are systematically larger than observed effect sizes (subject to Winner's Curse bias). This measures the realism of assumptions.

**Note**: The primary analysis focuses on **Execution Fidelity** (did they recruit as planned?). The secondary analysis addresses **Planning Accuracy** (was their guess right?), with explicit caveats about bias.

## 2. Dataset Strategy

The study relies on public data from the **Open Science Framework (OSF)**. The OSF API provides access to pre-registration documents and metadata.

**Dataset Source**: Open Science Framework (OSF)
**Access Method**: OSF Public API (`)
**Data Retrieval Strategy**:
1. **Cohort Selection**: Retrieve a batch of pre-registered studies using OSF query parameters for "pre-registration" and specific disciplinary tags (e.g., "psychology", "economics").
2. **Hybrid Extraction**:
 * **Pre-registration**: Parse document text for `planned_power`, `target_n`, `effect_size_assumption`, and `test_type`.
 * **Results**: Parse linked data repositories (OSF Files, Zenodo, GitHub) or PDF result sections for `actual_sample_size` and `observed_effect_size`.
3. **Validation**: If structured data is unavailable for results, the study is flagged as `manual_review_required` and excluded from automated regression.

**Verified Datasets**:
*Note: The OSF API does not provide structured fields for `actual_sample_size` or `observed_effect_size`. These must be extracted from unstructured text in linked documents. The VIF file mentioned in previous iterations is noted as a potential test artifact but not the primary study dataset.*

**Data Limitations & Mitigation**:
- **Missing Data**: If a study lacks `planned_power` or `actual_sample_size`, it is flagged and excluded from the Power Gap calculation but retained in the audit log (US-1, US-2).
- **API Rate Limits**: Implementation includes exponential backoff (start with an initial delay, max 60s) and resume capability.
- **Unstructured Text**: NLP parsing (keyword matching) will be supplemented with regex patterns for specific numeric formats (e.g., "power = 0.8").
- **Manual Review**: Studies where results cannot be programmatically extracted are flagged for manual review and excluded from the primary regression analysis.

## 3. Methodology

### 3.1 Data Extraction (FR-001, FR-002)
- **Input**: OSF Study IDs.
- **Process**:
 1. Fetch metadata and document content via OSF API.
 2. Apply NLP keyword search for "power", "sample size", "effect size", "test type".
 3. Apply Regex fallback for patterns like `power\s*[:=]\s*[\d.]+`.
 4. Extract `page_number` or `json_path` as source citation.
 5. **Crucial**: Extract `test_type` (e.g., "t-test", "ANOVA") to ensure correct power calculation method.
- **Output**: `StudyRecord` JSON object.

### 3.2 Sensitivity Power Calculation (FR-003, FR-004)
- **Metric**: Sensitivity Power (Power to detect the *assumed* effect size given the *actual* sample size).
- **Formula**: $Power = f(N_{actual}, \alpha=0.05, \delta_{assumed}, \text{test\_type})$.
- **Tool**: `statsmodels.stats.power` (TTestIndPower, FTestAnovaPower, etc., selected by `test_type`).
- **Power Gap**: $Gap = Planned\_Power - Sensitivity\_Power$.
- **Handling Errors**: Values clamped to [0.0, 1.0]; warnings logged for out-of-bounds.
- **Explicit Exclusion**: The `observed_effect_size` extracted in 3.1 is **strictly excluded** from the sensitivity power calculation. It is used ONLY for the secondary "Assumption Realism" analysis.

### 3.3 Regression Modeling (FR-005, FR-006, FR-007)
- **Model**: Multiple Linear Regression.
- **Outcome**: `power_gap` (measures Execution Fidelity).
- **Predictors**:
 - `field_of_study` (Categorical: Social, Natural, etc.)
 - `effect_size_domain` (Categorical)
 - **Excluded**: `sample_size_category` is **excluded** to prevent mathematical coupling with `power_gap` (which is derived from `N_actual`).
- **Diagnostics**:
 - **VIF (Variance Inflation Factor)**: Calculated for all predictors. If VIF > 5, independent effects are suppressed; joint relationship reported descriptively.
 - **Residual Analysis**: Normality check (Shapiro-Wilk) and homoscedasticity plot.
- **Inference**: All findings framed as **associational**. No causal claims.

### 3.4 Success Metrics & Testing (SC-001 to SC-005)
- **SC-001**: One-sample t-test (or Wilcoxon) on `power_gap` against 0.
- **SC-002**: R-squared comparison (Full Model vs. Intercept-only).
- **SC-003**: VIF threshold check (5.0).
- **SC-004**: Sample size check (N ≥ 30 for regression degrees of freedom).
- **SC-005**: Verification against `statsmodels` documentation for power calculation logic.

## 4. Compute Feasibility & Constraints

- **Environment**: GitHub Actions Free Tier (multiple CPUs, ample RAM).
- **Strategy**:
 - **No GPU**: `statsmodels` and `pandas` are CPU-optimized.
 - **Memory**: Data processed in batches; no full dataset loaded into memory if > 10k rows (unlikely for this scope).
 - **Runtime**: Target < 6 hours. Extraction is the bottleneck; rate limiting and caching are critical.
- **Approximation**: If the full OSF corpus is too large, a random sample of studies will be selected to ensure statistical power for the regression while fitting time limits.

## 5. Risks & Mitigation

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **OSF API Unreliability** | Data extraction fails. | Implement robust retry logic; cache raw JSON locally to resume on failure. |
| **Unstructured Text Parsing** | High missing data rate. | Manual review of a subset to refine regex/NLP heuristics; exclude unparseable studies with audit trail. |
| **Low Sample Size (N < 30)** | Regression underpowered. | Expand cohort search criteria; report limitation explicitly if N < 30. |
| **High Collinearity** | Invalid regression coefficients. | VIF check triggers descriptive reporting instead of coefficient interpretation. |
| **Mathematical Coupling** | Spurious regression results. | **Explicitly exclude `sample_size_category` from predictors.** |

