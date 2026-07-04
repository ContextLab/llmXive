# Feature Specification: Machine Learning Prediction of Crack Propagation Rates in Metals

**Feature Branch**: `001-crack-propagation-ml`  
**Created**: 2026-07-04  
**Status**: Draft  
**Input**: User description: "Machine Learning Prediction of Crack Propagation Rates in Metals"

## User Scenarios & Testing

### User Story 1 - Baseline Validation and Dataset Preparation (Priority: P1)

The system MUST ingest public fatigue crack growth (FCG) datasets (NASA Fracture Control Database, NIST Materials Data Repository), filter for records with valid $da/dN$ and $\Delta K$, and impute missing heat-treatment values to establish a robust baseline model using only the stress intensity factor range ($\Delta K$) to predict crack propagation rates ($da/dN$).

**Why this priority**: This is the foundational step. Without a validated dataset and a confirmed baseline performance (Paris Law behavior), no comparison can be made to determine if engineering descriptors add value. It establishes the "control" condition for the entire study.

**Independent Test**: The pipeline runs successfully on a subset of data, outputs a linear regression model with an $R^2$ score, and generates a partial dependence plot showing the log-log linear relationship between $\Delta K$ and $da/dN$, confirming the Paris Law holds for the mid-range data.

**Acceptance Scenarios**:

1. **Given** a raw CSV from the NASA Fracture Control Database containing missing heat-treatment fields, **When** the pre-processing script executes, **Then** the system filters for records with valid $da/dN$ and $\Delta K$, and imputes missing heat-treatment values with "Unknown/Not Specified", ensuring no rows are dropped due to missing heat-treatment data.
2. **Given** a cleaned dataset with $\log(\Delta K)$ and $\log(da/dN)$, **When** the baseline linear regression model is trained, **Then** the system calculates and reports the $R^2$ score and verifies statistical significance (p < 0.05) against a null model, confirming the baseline is valid.
3. **Given** the trained baseline model, **When** the system generates a partial dependence plot, **Then** the plot displays a linear slope consistent with the Paris Law exponent in the mid-range, verifying the physics-based relationship is captured.

---

### User Story 2 - Augmented Model Training and Variance Explanation (Priority: P2)

The system MUST train tree-based ensemble models (Random Forest, XGBoost) incorporating material composition (wt%) and heat-treatment descriptors alongside $\Delta K$, and quantify the unique variance explained by these engineering descriptors compared to the baseline using a nested model F-test or permutation test.

**Why this priority**: This addresses the core research question: "To what extent do material composition and heat-treatment parameters explain variance... beyond... $\Delta K$". This is the primary scientific contribution.

**Independent Test**: The system trains the augmented model, performs 5-fold cross-validation, and outputs a $\Delta R^2$ metric (Augmented $R^2$ minus Baseline $R^2$) that is statistically significant ($p < 0.05$) via a nested model F-test or permutation test on the added features.

**Acceptance Scenarios**:

1. **Given** the training set with composition and heat-treatment features, **When** the XGBoost model is trained with hyperparameter tuning (Optuna), **Then** the model converges without GPU acceleration and completes within the GitHub Actions free-tier limit of 6 hours on a 2-core CPU.
2. **Given** the test set, **When** the augmented model and baseline model generate predictions, **Then** the nested model F-test or permutation test on the added features returns a p-value $\le 0.05$, confirming the augmented model significantly reduces error beyond the baseline functional form.
3. **Given** the feature importance output, **When** the system aggregates scores, **Then** at least 3 non-$\Delta K$ features (e.g., Carbon content, Solution Treatment) rank in the top 10 importance metrics, proving engineering descriptors contribute predictive power.

---

### User Story 3 - Regime Identification and Sensitivity Analysis (Priority: P3)

The system MUST identify specific $\Delta K$ regions where microstructural effects dominate using continuous interaction analysis, and perform a sensitivity analysis on the model's stability across these regions to ensure robustness.

**Why this priority**: The research goal is not just to improve accuracy, but to map *where* the Paris Law fails. This enables engineers to target specific maintenance intervals. Sensitivity analysis ensures the identified regimes are not artifacts of arbitrary binning choices.

**Independent Test**: The system generates a regime map showing $\Delta R^2$ across $\Delta K$ regions identified by continuous analysis, with a sensitivity report showing that the identified "dominance regions" remain stable when model parameters are varied.

**Acceptance Scenarios**:

1. **Given** the test set predictions, **When** the system performs continuous interaction analysis to identify regions of low, mid, and high $\log(\Delta K)$, **Then** the residual $\Delta R^2$ attributed to composition is highest in the low and high $\Delta K$ regions identified by the analysis.
2. **Given** the sensitivity analysis configuration, **When** the model parameters are swept over a small range (e.g., hyperparameters), **Then** the ranking of regions (Low/High > Mid) remains unchanged, confirming the finding is robust to parameter variation.
3. **Given** the final analysis, **When** the system generates the partial dependence plots for the top 3 features, **Then** the plots show non-linear interactions specifically in the low and high $\Delta K$ regions, visualizing the shift to microstructural dominance.

---

### Edge Cases

- **What happens when the dataset contains alloys with identical composition but different heat treatments?** The system MUST handle this by treating heat treatment as a categorical feature, ensuring the model can distinguish between them without collinearity errors.
- **How does the system handle missing values in heat-treatment descriptors (e.g., "unknown" or null)?** The system MUST impute missing categorical values with a "Unknown/Not Specified" category rather than dropping rows, to preserve sample size while flagging the uncertainty.
- **What happens if the test set contains an unseen alloy family (e.g., Titanium) not present in the training set?** The system MUST evaluate the model on this distinct subset to verify generalizability, and if performance drops significantly, log a warning that the model is not robust to unseen alloy families.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest and parse data from NASA Fracture Control Database and NIST Materials Data Repository, filtering for records with valid $da/dN$ and $\Delta K$, and imputing missing heat-treatment values (See US-1).
- **FR-002**: System MUST implement a baseline linear regression model using only $\log(\Delta K)$ to establish the Paris Law reference performance (See US-1).
- **FR-003**: System MUST train Random Forest and XGBoost regressors using $\log(\Delta K)$ plus composition (wt%) and heat-treatment descriptors (See US-2).
- **FR-004**: System MUST perform 5-fold cross-validation stratified by known alloy family to tune hyperparameters ($n\_estimators$, $max\_depth$, $learning\_rate$) using Optuna (See US-2).
- **FR-005**: System MUST calculate $\Delta R^2$ and perform a nested model F-test or permutation test on the added features between the baseline and augmented models to confirm statistical significance ($\alpha = 0.05$) (See US-2).
- **FR-006**: System MUST perform continuous interaction analysis (e.g., varying coefficient models) to identify regions where microstructural effects dominate and compute local $R^2$ and feature importance within these regions (See US-3).
- **FR-007**: System MUST execute continuous interaction analysis to identify regions of microstructural dominance and report the stability of these regions under parameter variation (See US-3).
- **FR-008**: System MUST generate partial dependence plots for the top 3 non-$\Delta K$ features to visualize non-linear interactions (See US-3).

### Key Entities

- **FatigueRecord**: Represents a single experimental data point containing $da/dN$, $\Delta K$, alloy composition (dictionary of elements in wt%), and heat treatment (categorical string).
- **ModelPerformance**: Represents the evaluation metrics for a specific model configuration, including $R^2$, RMSE, and feature importance scores.
- **RegimeAnalysis**: Represents the aggregated results for a specific $\Delta K$ region, containing local $R^2$, dominant features, and stability metrics from sensitivity analysis.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The unique variance explained by engineering descriptors ($\Delta R^2$) is measured against the baseline $R^2$; the specific improvement threshold is [deferred] to the research phase (See US-2).
- **SC-002**: The statistical significance of the error reduction is measured against the null hypothesis ($p \le 0.05$) via nested model F-test or permutation test (See US-2).
- **SC-003**: The stability of identified dominance regions is measured against parameter variations, requiring the region ranking to remain unchanged (See US-3).
- **SC-004**: The generalizability of the model is measured against a held-out test set containing distinct alloy families; the specific performance drop tolerance is [deferred] to the research phase (See US-3).
- **SC-005**: The computational feasibility is measured against the GitHub Actions free-tier constraint (2 CPU cores, 7 GB RAM, 6 hours), requiring the full pipeline to complete within these limits (See US-2).

## Assumptions

- The NASA Fracture Control Database and NIST Materials Data Repository contain the necessary variables (composition, heat treatment, $\Delta K$, $da/dN$) for the selected metallic alloys; if specific variables like "post-task anxiety" equivalents (e.g., specific microstructural grain size) are missing, the analysis will rely solely on available engineering descriptors.
- The Paris Law relationship is strictly linear in log-log space for the mid-range $\Delta K$ regime, allowing for a valid linear baseline model.
- Heat-treatment descriptors can be effectively encoded using one-hot encoding without introducing excessive dimensionality that would cause overfitting on the available dataset size.
- The dataset size is sufficient to support 5-fold cross-validation and a [deferred] held-out test set while maintaining statistical power for the t-test.
- The analysis will be performed using Python libraries (scikit-learn, xgboost, pandas) that are compatible with CPU-only execution and fit within the 7 GB RAM limit.
- The "dominance regions" identified are primarily driven by the interaction between composition and $\Delta K$, rather than unmeasured environmental factors (e.g., temperature, humidity) which are assumed to be controlled or negligible in the source data.