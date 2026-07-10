# Feature Specification: Quantifying the Effect of Alloying Elements on the Glass-Forming Ability of Metallic Glasses

**Feature Branch**: `001-gene-regulation`
**Created**: 2023-10-27
**Status**: Draft
**Input**: User description: "Quantifying the Effect of Alloying Elements on the Glass-Forming Ability of Metallic Glasses"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Feature Engineering (Priority: P1)

The system MUST ingest raw composition data from Dataset (2014 Experimental GFA), parse elemental fractions, and compute physics-based descriptors (atomic radius, electronegativity, valence electron count) and interaction features (variance, weighted mean, pairwise size mismatch) using Pymatgen.

**Why this priority**: This is the foundational step; without a clean, feature-rich dataset, no model can be trained, and no scientific conclusions can be drawn. It delivers the primary input artifact for the entire research pipeline.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying that the output CSV contains the original composition columns plus the computed descriptor columns with no null values for known elements, and that the row count matches the sum of source datasets.

**Acceptance Scenarios**:

1. **Given** the raw CSV files from Dataset-001, **When** the data ingestion script is executed, **Then** the output file must contain a unified dataset where every row represents a unique alloy composition with all elemental fractions summing to 1.0 ± 0.01. If the sum is within this tolerance, the system MUST normalize the fractions to sum exactly to 1.0.
2. **Given** a composition containing known elements (e.g., Zr, Cu, Al), **When** the feature engineering module runs, **Then** the output must include calculated descriptors (e.g., atomic size mismatch, electronegativity variance, raw valence electron count per element, and pairwise size mismatch descriptors) derived from Pymatgen's element database without raising exceptions.
3. **Given** a composition with an element not found in the Pymatgen database, **When** the feature engineering module runs, **Then** the system must log a warning and exclude that row from the final training set rather than crashing.

---

### User Story 2 - Model Training and Validation (Priority: P2)

The system MUST train Random Forest and Gradient Boosting regression models on the engineered features to predict the logarithm of the critical cooling rate ($log_{10}(R_c)$), perform Leave-One-Cluster-Out (LOCO) cross-validation based on chemical families, and select the best model based on Mean Absolute Error (MAE). Additionally, the system MUST generate SHAP values for feature importance analysis.

**Why this priority**: This implements the core scientific hypothesis testing mechanism. It allows the user to quantify the relationship between composition and GFA, delivering the primary predictive capability.

**Independent Test**: Can be fully tested by running the training script and verifying that two distinct model artifacts are saved, cross-validation scores are printed, the selected model has an MAE lower than a baseline mean-predictor, and a SHAP feature importance report is generated. The split must be deterministic (same MAE scores on repeated runs).

**Acceptance Scenarios**:

1. **Given** the cleaned and feature-engineered dataset, **When** the training script is executed, **Then** the system must output the R² and MAE for both the Random Forest and Gradient Boosting models on the held-out test set.
2. **Given** a Leave-One-Cluster-Out (LOCO) cross-validation setup based on primary metallic element families (e.g., Zr-based, Cu-based), **When** the validation loop completes, **Then** the system must report the mean and standard deviation of the MAE across the folds.
3. **Given** the two trained models, **When** the selection logic runs, **Then** the system must save the model with the lowest cross-validated MAE as the "best_model.pkl" and log the selection reason.
4. **Given** the selected best model, **When** the SHAP analysis runs, **Then** the system must generate a `shap_feature_importance.json` file containing global SHAP values for all features.

---

### User Story 3 - Novel Composition Screening and Ranking (Priority: P3)

The system MUST generate all unique ternary combinations from the most abundant metallic elements, predict their GFA using the best model, calculate confidence intervals via bootstrapping, check for novelty against a known alloy list, and output a ranked list of top candidates.

**Why this priority**: This delivers the actionable scientific output (new material candidates) derived from the model. It validates the utility of the predictive model for discovery.

**Independent Test**: Can be fully tested by running the screening script and verifying that the output CSV contains up to 10 rows, sorted by predicted $log_{10}(R_c)$ (where candidates are filtered by the 10th percentile threshold), with all values below the threshold, and that the output includes confidence interval columns derived from the 10-model bootstrapped ensemble. Additionally, verify that `./output/verification_requests.json` is generated with `status` and `novelty_status` fields for each candidate.

**Acceptance Scenarios**:

1. **Given** the best trained model and the list of 30 abundant elements, **When** the screening script is executed, **Then** the system must generate a combinatorial list of all unique ternary alloys and predict their $log_{10}(R_c)$ values.
2. **Given** the set of predicted compositions, **When** the filtering logic runs, **Then** the system must retain only those with predicted $log_{10}(R_c)$ in the bottom 10th percentile of the dataset distribution (or < 4.0 if the dataset range is unknown, but default to percentile) and rank them by ascending $log_{10}(R_c)$.
3. **Given** the filtered and ranked list, **When** the final output is generated, **Then** the system must produce a CSV file containing the top 10 compositions (or fewer if threshold not met), their predicted cooling rates, and an estimated confidence interval derived from the variance of 10 bootstrapped Random Forest predictions.

### Edge Cases

- What happens if the HuggingFace dataset is missing or the download fails? The system must retry up to 3 times with a 5-second backoff, then fail gracefully with a clear error message indicating the missing data source.
- How does the system handle compositions with elements not in the Pymatgen database? The system must log the specific unknown elements, exclude those rows from training, and proceed with the remaining valid data without crashing.
- What if the generated ternary combinations result in zero candidates below the threshold? The system must output an empty CSV with a header and a log entry stating "No candidates found below threshold," rather than crashing or returning random data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse Dataset (2014 Experimental GFA, source: https://huggingface.co/datasets/GFA-D2/pilot_flags) into a unified dataset. The system MUST verify that the dataset schema contains a continuous `log10_Rc` column before proceeding; if not, it MUST fail with an explicit error (See US-1).
- **FR-002**: System MUST compute elemental descriptors for every composition using Pymatgen: (a) atomic radius, (b) electronegativity, (c) raw valence electron count per element (VEC_raw, using `element.valence_electrons`), and (d) interaction features (variance, weighted mean). The weighted mean of VEC_raw is defined as Valence Electron Concentration (VEC_avg) (See US-1).
- **FR-002b**: System MUST compute pairwise size mismatch descriptors for every unique pair of elements in ternary compositions to capture local atomic environments (See US-1).
- **FR-003**: System MUST train: (a) a RandomForestRegressor and (b) a GradientBoostingRegressor with hyperparameter grids limited to ≤30 combinations each. Additionally, the system MUST train a separate bootstrapped ensemble of 10 RandomForest models *only* for the purpose of confidence interval estimation (See US-2).
- **FR-004**: System MUST perform Leave-One-Cluster-Out (LOCO) cross-validation based on primary metallic element families (e.g., Zr-based, Cu-based, Fe-based) on StandardScaler-normalized features to ensure composition-aware splitting, and select the best model based on the lowest Mean Absolute Error (MAE) (See US-2).
- **FR-005**: System MUST generate all unique ternary combinations from the 30 most abundant metallic elements (Al, Ca, Fe, Mg, Ti, Na, K, Zn, Si, Zr, Cu, Ni, Cr, Mn, V, Sn, Pb, Ag, Au, Pd, Pt, Mo, W, Nb, Ta, Hf, Y, La, Ce, Sc) and predict their GFA using the selected best model (See US-3).
- **FR-006**: System MUST filter and rank the predicted compositions to output the top 10 candidates with predicted $log_{10}(R_c)$ in the bottom 10th percentile of the dataset distribution (See US-3).
- **FR-007**: System MUST calculate and include a confidence interval for each predicted candidate using the lower and upper percentiles (2.5% and 97.5%) of the bootstrapped Random Forest model predictions (See US-3).
- **FR-008**: System MUST generate a JSON file at `./output/verification_requests.json` containing the top-ranked candidates, each with a `status` field set to `"pending_verification"` and a `novelty_status` field (See US-3).
- **FR-009**: System MUST calculate the Domain of Applicability (DoA) for each candidate using the convex hull of the *training* feature space and a Mahalanobis distance threshold (Constitutional Principle VII: Prediction Uncertainty). Candidates outside the DoA MUST be flagged as "high extrapolation risk" and penalized in the final ranking score by adding a penalty term of +1.0 to their $log_{10}(R_c)$ value. This penalty is applied before ranking to ensure high-risk candidates are deprioritized (See US-3).
- **FR-010**: System MUST perform residual analysis; if the Breusch-Pagan test indicates heteroscedasticity (p < 0.05), the system MUST retrain the model using a weighted loss function. Weights MUST be derived by binning residuals from the initial fit by feature-space quantiles (multiple bins) and fitting a local variance estimator; weights are inversely proportional to the estimated local variance. The retrained model MUST be saved as `best_model_weighted.pkl` (See US-2).
- **FR-011**: System MUST generate SHAP values for the best model to provide global feature importance rankings (See US-2).
- **FR-012**: System MUST output a `shap_feature_importance.json` file containing the global SHAP values for all features (See US-2).
- **FR-013**: System MUST perform a novelty check for each candidate by querying a "Known Alloys List" (derived from Materials Project and literature databases) to verify if the composition has been previously reported. The `novelty_status` in `verification_requests.json` MUST be set to `"novel"` if not found, or `"known"` if found (See US-3).

### Key Entities

- **AlloyComposition**: Represents a unique metallic glass formulation, characterized by elemental fractions, computed physical descriptors, and the target variable ($log_{10}(R_c)$).
- **PredictiveModel**: A trained regression model (Random Forest or Gradient Boosting) capable of mapping composition descriptors to critical cooling rate predictions.
- **CandidateList**: A ranked collection of novel ternary compositions predicted to have high glass-forming ability (low critical cooling rate).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model predictive performance (R² and MAE) is measured against the held-out test set of experimental GFA values (See US-2).
- **SC-002**: Feature importance rankings are measured against the SHAP global importance values derived from the best model (FR-011, FR-012) to identify the top governing elements (See US-2).
- **SC-003**: Novelty of discovered candidates is measured against the existing literature (via FR-013), AND the system MUST generate a `verification_requests.json` artifact for the top 10 candidates (See US-3, FR-008, FR-013).
- **SC-004**: Computational feasibility is measured against the GitHub Actions runner constraints (≤6 hours, CPU-only, ≤7GB RAM) to ensure the full pipeline completes without resource exhaustion (See US-1, US-2, US-3).

## Assumptions

- **Data Availability**: Dataset-001 (2014 Experimental GFA) is accessible via the verified HuggingFace URL `https://huggingface.co/datasets/GFA-D2/pilot_flags`. The dataset schema MUST contain a continuous `log10_Rc` column; if not, the pipeline fails (See FR-001). Dataset-002 (Materials Project) is excluded due to lack of verified access; the system relies solely on the verified HuggingFace source.
- **Physics-Based Descriptors**: Pymatgen's element database contains accurate and complete physical properties (atomic radius, electronegativity, valence electrons) for all elements present in the metallic glass datasets.
- **Linearity of Log-Transformation**: Transforming the critical cooling rate ($R_c$) to its logarithm ($log_{10}(R_c)$) sufficiently normalizes the target distribution for standard regression models, subject to heteroscedasticity checks (FR-010).
- **Combinatorial Feasibility**: Generating and predicting GFA for all unique ternary combinations of the 30 most abundant metallic elements fits within the memory and time constraints of the free-tier GitHub Actions runner.
- **Model Generalizability**: The Random Forest and Gradient Boosting models trained on existing data can extrapolate reasonably well to novel, unreported ternary compositions within the chemical space of the 30 abundant elements, provided extrapolation risk is flagged via Conformal Prediction (FR-009).
- **No GPU Requirement**: The selected ML algorithms (scikit-learn Random Forest/Gradient Boosting) and the dataset size are small enough to run efficiently on a CPU-only environment without requiring CUDA or GPU acceleration.