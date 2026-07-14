# Research: Developing New Methods to Synthesize High-Performance Membranes using Sustainable Materials

## 1. Problem Statement & Research Question

**Core Question**: Which structural features and material compositions of sustainable polymers determine permeability and selectivity performance comparable to conventional petrochemical-based membrane materials?

**Context**: The field suffers from "data scarcity" and lack of standardized metrics. Literature data is sparse, units are inconsistent (Barrer, GPU, LMH/bar), and many entries lack critical structural descriptors (e.g., Fractional Free Volume). This project aims to build a predictive framework to screen bio-based candidates (cellulose, chitosan, lignin) against petrochemical benchmarks.

**Scope Limitation**: This project identifies structural drivers and recommends candidates. It does *not* perform experimental validation (FR-009), which is a future work requirement. The statistical test assesses model discrimination capability, not absolute material superiority.

## 2. Dataset Strategy

The project relies on aggregating data from literature and open repositories. Per the "Verified datasets" block, the following sources are used. **Note**: OpenPolymer has no verified URL; data must be manually extracted from literature or the "Open Polymer Challenge" report (if accessible via text) and treated as "manual literature extraction" (FR-001).

| Dataset Name | Source/URL | Content Description | Relevance to FR/SC |
|:--- |:--- |:--- |:--- |
| **ChEMBL Subset (RDKit Descriptors)** | ` | Contains SMILES strings and pre-calculated RDKit descriptors (VdW volume, H-bonds, etc.). | **FR-002**: Source of baseline descriptors for validation of `calculate_descriptors.py`. Replaces invalid NLP dataset. |
| **FFV Dataset (Test)** | ` | Contains Fractional Free Volume (FFV) data for a subset of polymers. | **Validation Only**: Used to validate RDKit descriptor calculation pipeline. **NOT** used for imputation to avoid double-dipping. |
| **SMILES (Polymer Templates)** | *Generated* | Virtual library generated from known sustainable polymer classes (cellulose, chitosan, lignin derivatives) using SMILES templates. | **FR-009**: Source for the "virtual library" of 50+ sustainable candidates. Replaces generic druglike dataset. |
| **Manual Literature Extraction** | *arXiv, OpenPolymer Report* | Primary source for (Structure + Permeability + Selectivity) triplets. | **FR-001**: Primary training data. |

**Dataset-Variable Fit Analysis**:
- **Required Variables**: SMILES, Permeability (Barrer), Selectivity, Synthesis Method, VdW Volume, H-bond counts.
- **Gap Identification**: The verified datasets (RDKit, FFV) contain chemical descriptors but **lack** specific membrane performance metrics (Permeability/Selectivity) for *sustainable* polymers.
- **Mitigation**: The primary data source will be **manual literature extraction** (FR-001) from arXiv and the "Open Polymer Challenge" report. The verified datasets (RDKit/FFV) will serve as **reference libraries** to validate the descriptor calculation pipeline and to augment the virtual candidate library (FR-009).
- **Critical Warning**: If the literature extraction yields < 30 valid records with both structure and performance, the project will halt (FR-006, SC-005). No fallback dataset is used for training to avoid data leakage or invalidity.

## 3. Methodological Approach

### 3.1 Data Aggregation & Standardization (US-1, FR-001, FR-006)
- **Ingestion**: Parse CSV/Parquet files. Convert all permeability units to **Barrer** (1 Barrer = 10^-10 cm^3 (STP) cm / (cm^2 s cmHg)). Convert selectivity to dimensionless ratios.
- **Missing Data Handling**:
 - **Critical Variable Missing > 20%**: Halt execution, emit `missing_data_report.json`, error `ERR_DATA_INSUFFICIENT`.
 - **Critical Variable Missing 5-20%**: Apply multiple imputation (MICE) or polymer-class averages. **Output**: Generate `clarification_flag.json` to trigger SC-005.
 - **Non-Critical**: Flag and impute with class median.
- **Conflict Resolution**: If conflicting metrics exist for the same polymer, flag as "high variance" and exclude from primary training (Edge Case).
- **Held-Out Set Validation**: Before training, verify the dataset contains ≥10 known high-performance bio-membranes. If not, halt (Constitution Principle VII).

### 3.2 Feature Engineering (US-2, FR-002, FR-008, FR-011)
- **Descriptors**: Use `rdkit` to calculate:
 - Molecular Weight (MW)
 - H-bond Donor/Acceptor Counts
 - Van der Waals Volume (VdW)
 - *Note*: True FFV requires density. We will **exclude** records with missing density or use a **standard literature value** for that polymer class. **No proxy estimator** is trained to avoid data leakage and circular validation.
- **Categorical Encoding**: `synthesis_method` encoded as one-hot or target encoding.
- **Dimensionality Reduction**: **Mandatory**. Apply Recursive Feature Elimination (RFE) to select the top 5-10 most predictive descriptors before training to mitigate overfitting in the small-N regime (FR-011).

### 3.3 Model Training (US-2, FR-003, FR-004, FR-007)
- **Algorithm**: Random Forest Regressor (or Gradient Boosting).
- **Constraints**: Max tree depth = 10, n_estimators = 100.
- **Fallback**: If runtime > 60 mins, reduce tree depth to **6**. If still exceeded, reduce to **4**. Retry up to 2 times.
- **Validation**: Stratified k-fold Cross-Validation.
- **Metrics**: R² (Target ≥ 0.1), MAE.
- **Framing**: All findings explicitly framed as **associational** (FR-007). No causal claims.

### 3.4 Candidate Screening & Statistical Validation (US-3, FR-005, FR-009, FR-010)
- **Virtual Library**: Generate multiple candidates (SMILES) from sustainable polymer classes (cellulose derivatives, etc.) using templates.
- **Prediction**: Run trained model to predict Permeability/Selectivity for:
 1. Bio-candidates.
 2. A control set of petrochemical benchmarks (using the same model).
- **Benchmarking**: Compare the *distribution of predicted bio-candidate performance* against the *distribution of predicted petrochemical performance*.
 - **Rationale**: This tests the model's ability to *discriminate* between classes, avoiding the conflation of model error with material performance (which would occur if comparing predictions to experimental benchmarks).
 - **Limitation**: This test validates the model's discrimination capability, not the absolute superiority of bio-candidates, as experimental ground truth for bio-candidates is missing (FR-009).
- **Statistical Test**: Mann-Whitney U test (non-parametric) to compare the two distributions of predictions.
 - **H0**: No difference in the *predicted* performance distributions.
 - **H1**: Distributions differ (model can discriminate).
 - **Alpha**: 0.05.
- **Power Analysis**: Calculate detectable effect size for N=30 assuming a **large effect** (rank-biserial correlation = 0.5). Acknowledge that N=30 provides <50% power for medium effects, making non-significant results inconclusive rather than negative.
- **Future Work**: Output `candidate_recommendation_report.md` listing top 3 candidates for *future* experimental validation (FR-009).

## 4. Compute Feasibility Strategy

- **Hardware Target**: 2 CPU cores, 7GB RAM, 14GB disk.
- **Data Size**: Subset to ~500 rows max (literature + virtual). Fits easily in memory.
- **Model Size**: Random Forest (100 trees, depth 10) on ~500 rows is trivial for CPU.
- **Libraries**: `scikit-learn`, `pandas`, `rdkit` (CPU wheels). No GPU dependencies.
- **Runtime**: Estimated < 2 hours total (Ingestion: 15m, Features: 30m, Train: 45m, Screen: 15m). Well within 6h limit.

## 5. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|:--- |:--- |:--- |:--- |
| **Insufficient Data (<30 records)** | High | Critical (Project Fail) | Aggressive manual extraction from arXiv; use "Open Polymer Challenge" report; **Halt** with specific report if N < 30. |
| **Missing Critical Variable (e.g., VdW)** | Medium | High | Use standard density estimates or exclude; if >20% missing, halt (FR-006). |
| **Model Overfitting** | Medium | Medium | **Mandatory RFE** to reduce features; strict 5-fold CV; limit tree depth. |
| **Runtime Exceeds 6h** | Low | High | Fallback logic in training script (reduce depth to 6, then 4); monitor memory usage. |
| **Lack of High-Performance Bio-Membranes** | Medium | High | **Validation Step**: Halt if <10 such records exist to satisfy Constitution Principle VII. |

## 6. Decision Log

- **Why Random Forest?** Robust to non-linear relationships, handles mixed data types, less prone to overfitting than deep nets on small data, CPU-tractable.
- **Why Mann-Whitney U?** Data distribution is unknown and likely non-normal; parametric tests are invalid.
- **Why no FFV from SMILES?** FFV requires experimental density. We will exclude or use class averages, never invent.
- **Why Predicted vs. Predicted?** Comparing predictions to experimental benchmarks conflates model error with material performance. This test assesses model discrimination capability.
- **Why RFE?** Small-N vs High-Dimensionality requires aggressive feature reduction to prevent overfitting.
