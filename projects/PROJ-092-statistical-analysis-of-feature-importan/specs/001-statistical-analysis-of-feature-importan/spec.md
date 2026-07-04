# Feature Specification: Statistical Analysis of Feature Importance Drift

## User Stories

### US1: Baseline Model Training and Windowed Importance Calculation
**As a** data scientist,
**I want** to train a Random Forest model on sequential 30-day windows and compute feature importance,
**so that** I can establish a baseline for drift detection.

**Acceptance Criteria**:
- Data is split into non-overlapping 30-day windows
- Model achieves R² > 0.8 on each window (or is skipped)
- Permutation importance is calculated for all features
- `outputs/importance_profiles.csv` is generated with valid scores

### US2: Drift Quantification via Rank Correlation
**As a** data scientist,
**I want** to calculate Spearman rank correlation between consecutive windows,
**so that** I can quantify the magnitude of feature importance drift.

**Acceptance Criteria**:
- Spearman rho is calculated for all adjacent window pairs
- p-values are included from null baseline comparison
- `outputs/drift_metrics.csv` contains rho, p-value, and window IDs
- Null model baseline is generated via window shuffling

### US3: Statistical Significance Testing and Trend Detection
**As a** data scientist,
**I want** to apply Mann-Kendall trend test and block permutation tests,
**so that** I can validate whether observed drift is statistically significant.

**Acceptance Criteria**:
- Mann-Kendall test returns Kendall's Tau and trend direction
- Block permutation test returns p-value for correlation sequence
- Small sample sizes (n < 10) are handled via permutation
- Final report includes mean_rho, trend_direction, p-value, stable_window_count

## Functional Requirements
- **FR-001**: Download UCI dataset programmatically
- **FR-002**: Handle missing values via median imputation
- **FR-003**: Train RandomForestRegressor with specified hyperparameters
- **FR-003b**: Skip windows with R² < 0.8
- **FR-004**: Calculate Spearman rank correlation between consecutive windows
- **FR-004b**: Flag high drift only if block permutation p-value < 0.05
- **FR-005**: Implement Mann-Kendall trend test
- **FR-006**: Generate `drift_metrics.csv` and `global_stats.json`
- **FR-007**: Generate null baseline via window shuffling
- **FR-008**: Implement block permutation significance test

## Non-Functional Requirements
- **SC-003**: Report stability metrics (count of successful windows, average R²)
- **SC-004**: Null baseline must use multiple shuffled runs

## Edge Cases
- Missing data in raw dataset
- Zero-variance features per window
- Model failure (R² < 0.8)
- Small sample sizes for trend tests
