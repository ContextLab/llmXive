# Feature Specification: Predicting Material Stability using Machine Learning and DFT Calculations

**Feature Branch**: `001-material-stability`  
**Created**: 2026-07-05  
**Status**: Draft  
**Input**: User description: "Predicting Material Stability using Machine Learning and DFT Calculations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline Model Training and Evaluation (Priority: P1)

The researcher needs to train a Gradient Boosting Regressor using only bulk compositional descriptors (Magpie features) on the filtered OQMD dataset to establish a performance baseline for predicting formation energy.

**Why this priority**: This is the foundational step. Without a validated baseline model, the incremental value of local coordination features cannot be quantified. It establishes the "composition-only" error floor.

**Independent Test**: The system can be fully tested by training the baseline model on a majority training split, evaluating it on a held-out test split, and outputting a CSV containing predicted formation energies and calculated MAE/RMSE metrics without any local coordination features.

**Acceptance Scenarios**:

1. **Given** a filtered OQMD dataset of Li-rich rock-salt structures, **When** the baseline training pipeline executes, **Then** a Gradient Boosting Regressor model is trained using only Magpie compositional features and outputs a `baseline_results.csv` containing the predicted formation energies and the calculated Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) metrics.
2. **Given** the trained baseline model, **When** predictions are generated for the test set, **Then** the system calculates and logs the Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) against the DFT ground truth values.
3. **Given** a specific metastable compound in the test set, **When** the baseline model predicts its energy, **Then** the prediction is recorded in the output file even if the error exceeds 0.1 eV/atom, preserving the raw error distribution for later analysis.

---

### User Story 2 - Local Coordination Feature Integration and Comparative Analysis (Priority: P2)

The researcher needs to augment the dataset with local coordination environment features (Voronoi statistics, bond-length distributions) and train a second model to determine if these features significantly reduce prediction error compared to the baseline.

**Why this priority**: This directly addresses the core research question: whether local structural disorder captures instability mechanisms that bulk composition misses. It is the primary scientific contribution.

**Independent Test**: The system can be fully tested by executing the feature engineering step to generate local descriptors, training the augmented model, and producing a comparative report showing the delta in MAE and R² between the baseline and the augmented model.

**Acceptance Scenarios**:

1. **Given** the raw crystal structures from the OQMD dataset, **When** the feature engineering module runs, **Then** Voronoi tessellation statistics (coordination number, face area, solid angle) and bond-length histograms are computed and appended to the feature matrix.
2. **Given** the augmented feature set, **When** the second Gradient Boosting Regressor is trained and evaluated, **Then** the system outputs a `comparison_metrics.json` file recording the calculated MAE for the augmented model and the delta relative to the baseline MAE.
3. **Given** the two trained models, **When** the analysis script runs, **Then** it generates a feature importance plot highlighting the top 10 local coordination features contributing to the reduction in prediction error.

---

### User Story 3 - Metastable Phase Classification and Sensitivity Analysis (Priority: P3)

The researcher needs to classify materials as stable or metastable (defined as < 0.05 eV/atom above the convex hull) and perform a sensitivity analysis on this threshold to ensure the findings are robust to small variations in the cutoff.

**Why this priority**: The research specifically targets "metastable phases near the convex hull." Validating the classification performance (AUC-ROC) and ensuring the 0.05 eV/atom threshold is not arbitrary is critical for the validity of the conclusions regarding DRX instability mechanisms.

**Independent Test**: The system can be fully tested by running the classification module on the test set predictions, calculating the AUC-ROC, and executing a sensitivity sweep over the threshold values {0.04, 0.05, 0.06} to report the variation in recall/precision.

**Acceptance Scenarios**:

1. **Given** the predicted formation energies and the independent DFT ground truth, **When** the convex hull distance is calculated using `pymatgen`, **Then** the system classifies each material as "stable" (distance ≤ 0.00 eV/atom) or "metastable" (0.00 < distance ≤ threshold) and generates a ROC curve, recording the calculated AUC-ROC value.
2. **Given** the classification results, **When** the sensitivity analysis script runs, **Then** it re-evaluates the classification metrics (Recall, Precision, F1) for thresholds of 0.04, 0.05, and 0.06 eV/atom and outputs a `sensitivity_analysis.csv` showing the variance in false-positive and false-negative rates.
3. **Given** the sensitivity results, **When** the final report is generated, **Then** it explicitly states whether the model's ability to distinguish metastable phases is robust (variance < 5% across the sweep) or sensitive to the threshold choice.

### Edge Cases

- What happens when the OQMD API returns fewer than 100 samples after filtering for Li-rich rock-salts? The system must log a warning and proceed with the available data, but the `sensitivity_analysis` must flag the low sample size as a potential power limitation.
- How does the system handle crystal structures with missing bond length data or degenerate Voronoi cells? The pipeline must impute missing values with the dataset median or skip the specific feature for that entry, logging the count of skipped entries.
- What if the `pymatgen` convex hull calculation fails for a specific composition due to missing elemental reference energies? The system must exclude that entry from the classification metrics but retain it in the regression analysis, logging the exclusion reason.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and filter the OQMD dataset to include only Li-rich oxides with rock-salt structures and fully relaxed DFT energies, attempting to retrieve at least 500 samples; if fewer are available, the system proceeds with the available data and logs a warning about reduced statistical power (See US-1).
- **FR-002**: System MUST compute bulk compositional descriptors (Magpie features) and local coordination features (Voronoi tessellation, bond-length histograms) for every entry in the filtered dataset (See US-2).
- **FR-003**: System MUST train two distinct Gradient Boosting Regressor models: one using only bulk features and one using the combined feature set, with hyperparameter tuning performed on the validation split (See US-1, US-2).
- **FR-004**: System MUST calculate the distance to the convex hull for all predictions and ground truth values using `pymatgen` to enable binary classification of stable vs. metastable phases (See US-3).
- **FR-005**: System MUST perform a sensitivity analysis sweeping the metastability threshold across {0.04, 0.05, 0.06} eV/atom and report the resulting variation in classification metrics (See US-3).
- **FR-006**: System MUST execute the entire pipeline (data download, feature engineering, training, evaluation) on a CPU-only environment within a reasonable runtime (≤ 4 hours) and with a memory footprint not exceeding 7 GB RAM (See Assumptions).

### Key Entities

- **MaterialEntry**: Represents a single compound in the OQMD dataset; attributes include composition, crystal structure, DFT formation energy, and distance to convex hull.
- **FeatureVector**: A numerical representation of a material; attributes include bulk descriptors (Magpie) and local coordination descriptors (Voronoi stats, bond lengths).
- **ModelPerformance**: Aggregated metrics for a trained model; attributes include MAE, RMSE, R², and AUC-ROC.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reduction in Mean Absolute Error (MAE) between the baseline and augmented models is recorded and output to quantify the incremental value of local features (See US-2).
- **SC-002**: The Area Under the Receiver Operating Characteristic Curve (AUC-ROC) for classifying metastable phases is recorded and output to assess the improvement in identifying phases near the convex hull (See US-3).
- **SC-003**: The variance in Recall and Precision across the threshold sensitivity sweep ({0.04, 0.05, 0.06} eV/atom) is recorded and output to validate the robustness of the 0.05 eV/atom cutoff (See US-3).
- **SC-004**: The total runtime of the data processing and model training pipeline is recorded and output to ensure CPU-only feasibility (See FR-006).
- **SC-005**: The memory footprint of the feature engineering step is recorded and output to ensure compatibility with free-tier CI runners (See FR-006).

## Assumptions

- The OQMD Zenodo repository or API provides sufficient Li-rich rock-salt entries with fully relaxed structures to construct a training set of at least 500 samples; if fewer are available, the study will proceed with the available data but acknowledge reduced statistical power.
- The `pymatgen` library's `PhaseDiagram` class accurately calculates the convex hull distance for the specific Li-rich oxide compositions in the dataset using standard elemental references.
- The Gradient Boosting Regressor implementation in `scikit-learn` is computationally efficient enough to train on the full feature set within the 4-hour runtime limit on a 2-core CPU.
- The 0.05 eV/atom threshold for defining "metastable" is based on community standards for DFT uncertainty in formation energy (as cited in the literature review) and serves as the primary decision boundary. The sensitivity analysis is explicitly designed to account for the uncertainty in this ground truth label, as DFT errors can shift a material across this boundary.
- The dataset contains the necessary structural information (atomic positions, lattice vectors) to compute Voronoi tessellation and bond-length distributions; no additional crystallographic data acquisition is required.
- The analysis is observational; findings regarding the relationship between local features and instability will be framed as associational, as no random assignment of cation ordering is performed in the dataset.
- The classification task (stable vs. metastable) uses the DFT-calculated distance to the convex hull as the ground truth. This is acknowledged as a self-consistency check of the DFT model's predictive power for stability, not a substitute for experimental synthesis data. The goal is to measure the model's ability to learn the non-linear relationships in the DFT data that lead to hull distance predictions.
- The 7 GB RAM limit and 4-hour runtime are hard constraints for the execution environment; if exceeded, the system must log an error and terminate gracefully.