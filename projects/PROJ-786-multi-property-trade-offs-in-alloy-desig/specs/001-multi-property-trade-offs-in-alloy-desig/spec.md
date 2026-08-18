# Project Specification: Multi-Property Trade-Offs in Alloy Design Using Public Compositional Data

## 1. Introduction

This project investigates the trade-offs between Bulk and Shear Moduli in multi-component alloys using public compositional data (OQMD) and machine learning techniques. The goal is to identify regions in compositional space where these properties can be decoupled, allowing for the design of alloys with tailored mechanical properties.

## 2. Functional Requirements

### FR-001: Data Ingestion and Filtering
The system must ingest public alloy data from the OQMD (via HuggingFace datasets) and filter for entries with valid Bulk and Shear Moduli (DFT Proxies). Entries with missing or non-positive values for these properties must be excluded.

### FR-002: Composition Encoding
The system must encode alloy compositions using elemental fractions and periodic descriptors (atomic radius, electronegativity) fetched via `pymatgen` or `mendeleev`.

### FR-003: Surrogate Modeling
The system must train separate Gradient Boosting Regressor models to predict Bulk and Shear Moduli from the encoded compositions. The models must be trained on CPU with `n_jobs=2` and memory constraints (<7GB).

### FR-004: Pareto Frontier Generation
The system must generate a Pareto frontier representing the optimal trade-offs between Bulk and Shear Moduli using the NSGA-II algorithm on synthetic points generated within the convex hull of the training data.

### FR-005: Trade-Off Decoupling Analysis
The system must perform K-Means clustering on the compositional space to identify regions where the correlation between Bulk and Shear Moduli is minimized (decoupled regions).

### FR-006: Uncertainty Quantification
The system must calculate uncertainty metrics (variance from LOSO-CV) and flag regions where prediction uncertainty exceeds a configured threshold.

## 3. Scientific Constraints

### SC-001: Physical Bounds
All generated synthetic points and model predictions must be validated against DFT-derived physical bounds (Rule of Mixtures for Bulk/Shear Moduli). Predictions outside these bounds must be flagged or clamped.

### SC-002: Correlation Analysis
The system must calculate both global and local (cluster-specific) correlation coefficients between Bulk and Shear Moduli to quantify the degree of decoupling in identified regions.

### SC-003: Robustness Validation
The identified decoupled regions must be robust to changes in the correlation threshold. A sensitivity analysis must be performed to validate the stability of the results.

## 4. User Stories

### US-1: Data Ingestion and Preprocessing
**As a** materials scientist,
**I want** to ingest and clean public alloy data,
**So that** I can use it for training machine learning models.

**Acceptance Criteria:**
1. The system successfully loads data from the OQMD dataset via HuggingFace.
2. The system filters out entries with missing or invalid Bulk and Shear Moduli values.
3. The system encodes compositions with at least two periodic descriptors per element.
4. The system outputs a clean CSV file (`data/processed/encoded_alloys.csv`) with no nulls in key columns.
5. If the dataset contains fewer than 500 valid entries, the system logs a warning and exits gracefully.

### US-2: Model Training and Pareto Optimization
**As a** computational materials engineer,
**I want** to train surrogate models and generate a Pareto frontier,
**So that** I can explore the optimal trade-offs between Bulk and Shear Moduli.

**Acceptance Criteria:**
1. The system trains Gradient Boosting models for both Bulk and Shear Moduli.
2. The system performs Leave-One-System-Out Cross-Validation (LOSO-CV) to assess generalizability.
3. The system generates synthetic points within the convex hull of the training data.
4. The system computes the Pareto frontier using NSGA-II.
5. The system calculates the percentage of empirical data dominated by the frontier.

### US-3: Decoupling Analysis and Visualization
**As a** alloy designer,
**I want** to identify compositional regions where Bulk and Shear Moduli are decoupled,
**So that** I can target these regions for new alloy development.

**Acceptance Criteria:**
1. The system performs K-Means clustering on the compositional space.
2. The system identifies the cluster with the minimum correlation between Bulk and Shear Moduli.
3. The system performs a sensitivity analysis on the correlation threshold.
4. The system generates a 2D visualization highlighting the decoupled region and Pareto frontier.
5. The system reports the robustness score of the identified region.

## 5. Technical Specifications

### 5.1 Data Sources
- **OQMD Elastic Properties**: `datasets.load_dataset('OQMD/elastic_properties')`

### 5.2 Dependencies
- Python 3.11+
- `pandas`, `numpy`, `scipy`, `scikit-learn`, `deap`, `pymatgen`, `mendeleev`, `matplotlib`, `seaborn`, `pyyaml`, `python-dotenv`, `datasets`

### 5.3 Hardware Constraints
- CPU-only execution (no GPU/CUDA)
- Memory limit: < 7GB
- Runtime limit: 6 hours for optimization tasks

## 6. Output Artifacts

- `data/processed/encoded_alloys.csv`: Cleaned and encoded dataset.
- `data/processed/model_validation_report.json`: LOSO-CV results and uncertainty metrics.
- `data/processed/theoretical_bounds.json`: Rule of Mixtures bounds for Bulk/Shear Moduli.
- `data/processed/correlation_stats.csv`: Cluster-wise correlation coefficients.
- `data/processed/sensitivity_analysis.csv`: Sensitivity analysis results.
- `data/results/robustness_validation.json`: Validation of threshold robustness.
- `figures/decoupling_plot.png`: Visualization of compositional space and decoupled regions.

## 7. Version History
- v1.0: Initial specification focusing on Yield Strength and Elongation.
- v1.1: Updated to focus on Bulk and Shear Moduli (DFT Proxies) per project plan pivot.
- v1.2: Updated FR-001, FR-003, FR-005, SC-001, SC-002, and US-1 to explicitly reference Bulk and Shear Moduli.