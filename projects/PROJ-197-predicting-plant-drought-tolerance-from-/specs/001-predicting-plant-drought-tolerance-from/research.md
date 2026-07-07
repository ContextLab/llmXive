# Research: Predicting Plant Drought Tolerance from Publicly Available Physiological and Genomic Data

## 1. Problem Statement & Hypothesis

**Original Hypothesis**: A machine learning model trained on a combination of physiological traits and genomic markers will significantly outperform a phylogeny-only baseline in predicting binary drought tolerance in plants.

**Current Status**: **UNTESTABLE**. The `# Verified datasets` block provided for this project contains **NO** verified source for **Plant Genomic Data** (ABA-signaling genes) or **Plant Phylogeny**. The available RefSeq URLs are for Viral, Fungi, and Archaea, which are taxonomically inappropriate for plant prediction.

**Revised Project Goal**: **Pipeline Validation**.
This project will validate the **data ingestion, merging, and modeling pipeline** using:
1. Real physiological data from the verified TRY database.
2. **Synthetic genomic features** (binary presence/absence) and a **synthetic target label** (correlated with the synthetic features) to simulate the expected data structure.
3. A **synthetic phylogenetic distance matrix** for the baseline.

**Scientific Validity Disclaimer**:
- Results from this study **cannot** be used to make biological claims about drought tolerance mechanisms.
- The "feature importance" and "statistical significance" metrics will reflect the model's ability to fit the **synthetic signal**, not real biological associations.
- This is a **technical proof-of-concept** to ensure the code works before real data is acquired.

## 2. Dataset Strategy

### 2.1 Verified Sources & Data Gaps

| Dataset | Source URL | Content | Usage | Status |
|:--- |:--- |:--- |:--- |:--- |
| **TRY Database** | ` | Plant physiological traits (e.g., root depth, SLA) | Primary predictor source | **Verified** |
| **NCBI RefSeq (Plants)** | **NO VERIFIED SOURCE** | Plant genomic sequences/annotations | **MISSING** | **CRITICAL GAP** |
| **NCBI RefSeq (Viral/Fungi/Archaea)** | ` | Non-plant genomic data | **NOT USED** | Inappropriate for plant study |

### 2.2 Data Gap Analysis & Mitigation

**Critical Finding**: The `# Verified datasets` block provides **NO** verified source for **Plant Genomic Data** or **Plant Phylogeny**.

**Decision**:
1. **Physiological Data**: Proceed with the verified TRY dataset.
2. **Genomic Data**: Since no verified plant genomic dataset exists, the plan **cannot** fulfill the requirement to merge "genomic feature data from NCBI RefSeq for plant species".
 - *Mitigation*: The implementation will use a **Mock/Placeholder Genomic Dataset**.
 - *Generation*: Synthetic binary features (0/1) for 20 "genes" will be generated for the 50 target species using a fixed random seed (`random_state=42`).
 - *Label Generation*: A binary `drought_tolerance` label will be generated synthetically, with a known correlation to a subset of the synthetic genomic features (to allow for "ground truth" validation).
3. **Phylogeny**: A random distance matrix will be generated for the KNN baseline.

**Revised Dataset Strategy**:
- **Input 1**: TRY Physiological Data (Real, Verified).
- **Input 2**: Synthetic Genomic Data (Placeholder, for pipeline validation).
- **Input 3**: Synthetic Phylogeny Matrix (Placeholder, for KNN baseline).
- **Label**: Synthetic Binary Drought Tolerance (Correlated with synthetic features).

### 2.3 Data Preprocessing

- **Imputation**: True Phylogenetic MICE is not feasible without a verified phylogenetic tree. The plan will use **Standard MICE** (IterativeImputer) as a proxy. This is a known limitation.
- **Merging**: Join on `species_name`. Species missing in either dataset are excluded.
- **Normalization**: StandardScaler for continuous traits.

## 3. Model Strategy

### 3.1 Algorithms

1. **Random Forest Classifier**: Robust to noise, handles mixed data types.
 - *Parameters*: `n_estimators` grid search {100, 200, 500}.
2. **XGBoost Classifier**: High performance.
 - *Parameters*: `n_estimators` grid search {100, 200, 500}.
3. **Baseline (KNN)**: K-Nearest Neighbors (K=5) using a **synthetic** phylogenetic distance matrix.

### 3.2 Validation Strategy

- **Split**: Stratified 80/20 (Train/Test).
- **Cross-Validation**: 5-fold Stratified CV.
- **Metric**: ROC-AUC (primary).
- **Statistical Tests**:
 - **Paired T-Test**: Compare CV AUC scores of RF vs XGBoost.
 - **DeLong's Test**: Compare Best Model AUC vs Baseline AUC.
- **Feature Recovery (SC-005)**: Verify that the model identifies the **synthetic ground truth** features used to generate the label (instead of real ABA genes).

## 4. Computational Feasibility

- **Hardware**: 2 CPU cores, 7 GB RAM.
- **Data Size**: ~50 species x ~30 features. Extremely small.
- **Training Time**: < 1 minute.
- **Risk**: Primary risk is data availability. The pipeline is designed to be lightweight.

## 5. Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use Synthetic Genomic Data** | No verified source for plant ABA-signaling genes exists. Synthetic data allows pipeline validation. |
| **Use Standard MICE** | True Phylogenetic MICE requires a verified phylogenetic tree (unavailable). |
| **Use Synthetic Phylogeny** | No verified plant phylogeny available. Random matrix used for baseline logic test. |
| **CPU-Only Execution** | Mandatory for GitHub Actions free tier. |
| **Reframed Success Criteria** | SC-001 and SC-005 redefined to validate pipeline logic and synthetic ground truth recovery, not biological discovery. |

## 6. Limitations

- **Sample Size**: N=50 is small.
- **Data Quality**: Genomic features and labels are synthetic placeholders. **No biological conclusions can be drawn.**
- **Phylogeny**: Baseline model uses a synthetic distance matrix.
- **Imputation**: Standard MICE used instead of Phylogenetic MICE.
- **Scientific Validity**: This study is a **technical validation** only. It does not test the biological hypothesis that genomic markers predict drought tolerance.