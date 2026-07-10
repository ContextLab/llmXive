# Research: Predicting Battery Electrolyte Decomposition Products via DFT and Machine Learning

## 1. Problem Statement & Research Question

**Problem**: Battery electrolyte stability is critical for safety and longevity. Predicting decomposition products under varying electrochemical potentials is computationally expensive via DFT alone.
**Research Question**: Which molecular descriptors (electronic vs. geometric) govern the decomposition energy of common electrolytes (EC, DMC, LiPF6), and how does the importance ranking of these descriptors shift as the electrochemical potential increases from 0V to 5V?

## 2. Dataset Strategy

The project relies exclusively on verified datasets. No external URLs are fabricated.

| Dataset Name | Description | Verified URL | Usage in Plan |
|:--- |:--- |:--- |:--- |
| **DFT23-Test** | DFT-calculated molecular structures and energies. | ` | Primary source for training data (structures, energies). |
| **DFTest61523** | Additional DFT entries for broader coverage. | ` | Supplemental source for filtering EC/DMC/LiPF6 species. |
| **DFTest61623** | Additional DFT entries for broader coverage. | ` | Supplemental source for filtering EC/DMC/LiPF6 species. |

**Dataset Fit Analysis**:
- **Requirement**: The study needs HOMO, LUMO, band gap, bond lengths, and formation energies for electrolytes (EC, DMC, LiPF6).
- **Verification**: The DFT datasets (DFT23, DFTest) are derived from Materials Project/NOMAD-style calculations and contain the required electronic and geometric properties.
- **Constraint**: If the verified DFT datasets lack sufficient entries for *specific* electrolytes (e.g., LiPF6), the plan will filter the available data to the intersection of available species and explicitly report the sample size limitation (SC-005).
- **Experimental Validation**: The spec requires experimental onset potentials. The verified dataset list **does not** contain a specific "Experimental Onset Potentials" CSV.
 - **Action**: The plan **does not** use MAESTRO (protein-ligand data) as a fallback, as it is domain-mismatched. Instead, the plan implements **Internal DFT Consistency Validation** (validation against held-out DFT data).
 - **Limitation**: The requirement for external experimental validation (FR-006, SC-003) is **Blocked** due to missing data. The plan will explicitly flag this gap and report "N/A" for external MAE, while proceeding with internal validation.

## 3. Methodology

### 3.1 Data Ingestion & Cleaning
1. **Fetch**: Download parquet files from verified URLs.
2. **Filter**: Retain only entries with SMILES containing "EC", "DMC", "LiPF6" or matching known electrolyte IDs.
3. **Deduplicate**: Remove entries with identical `dft_id` and `potential` combinations.
4. **Outlier Handling**: Flag and exclude entries where `band_gap` $\le$ 0 (metallic behavior) as per edge cases.

### 3.2 Feature Engineering
- **Electronic**: HOMO, LUMO (directly from dataset).
 - **Collinearity Mitigation**: Since Band Gap = LUMO - HOMO, these features are perfectly collinear. **Action**: The plan will **drop the `band_gap` feature** from the model input to prevent arbitrary splitting of feature importance scores. Only HOMO and LUMO will be used as electronic descriptors.
- **Geometric**: Extract 5+ descriptors:
 - Max bond length.
 - Min bond length.
 - Mean bond angle.
 - Max dihedral angle.
 - Molecular weight (derived).
- **Normalization**: StandardScaler applied to all features.
- **Data Logging**: While `band_gap` is excluded from the model input matrix ($X$), it is retained in the processed dataset for logging and descriptive statistics to verify the calculation $LUMO - HOMO$.

### 3.3 Target Variable Calculation
- **Formula**: $E_{decomp} = E_{products} - E_{reactants} - nF\phi$
- **Reaction Mechanism Lookup Table (Hardcoded)**:
 - **EC (Ethylene Carbonate)**: Decomposition to ethylene + CO2. $n=2$.
 - **DMC (Dimethyl Carbonate)**: Decomposition to methanol + CO2. $n=2$.
 - **LiPF6**: Decomposition to LiF + PF5. $n=1$.
 - **Fallback**: If a molecule is not in this lookup table, it is **excluded** from the dataset. No heuristic default ($n=1$) is used to avoid systematic noise.
- **Parameters**:
 - $\phi \in \{0, 2, 4\}$ V.
 - $n$: Derived from the hardcoded lookup table above.
 - $F$: Faraday constant (96485 C/mol).
- **Note**: If $E_{products}$ or $E_{reactants}$ are missing, the entry is excluded.

### 3.4 Modeling Strategy
- **Algorithm**: Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`).
- **Rationale**: CPU-tractable, handles non-linear relationships, provides intrinsic feature importance.
- **Model Architecture**: **Single Global Model**.
 - The model is trained on **all** data (0V, 2V, 4V) with `potential_v` included as a feature.
 - **Rationale**: Training separate models per bin risks data leakage and makes comparison of feature importance shifts difficult. A global model allows direct analysis of how feature importance changes with potential (by conditioning on potential).
- **Hyperparameters**: Grid search over `n_estimators` (100, 200), `max_depth` (10, 20, None).
- **Validation**: 5-fold Cross-Validation (stratified by molecule ID to prevent data leakage).
- **Feature Importance Analysis**: Permutation importance is calculated globally, then analyzed by conditioning on potential bins (e.g., "What is the importance of HOMO when potential > 3V?").

### 3.5 Feature Importance & Sensitivity
- **Metric**: Permutation Importance (to avoid bias of tree-based impurity).
- **Analysis**: Compare rank of top 5 features between Low (0-2V) and High (3-5V) potential ranges by filtering the global model's predictions/inputs.
- **Sensitivity**: Re-run importance analysis with decomposition threshold shifted to $\{0.45, 0.50, 0.55\}$ eV.

### 3.6 Validation (Internal Consistency)
- **Metric**: Mean Absolute Error (MAE) and R² between predicted and actual $E_{decomp}$ on held-out DFT data.
- **External Validation (FR-006)**: **Not Implementable**. No verified experimental onset potential dataset exists.
 - **Action**: Report "N/A" for external MAE. Flag this as a critical limitation in the final report.
 - **Fallback**: Validate against held-out DFT data to confirm the model learns DFT internal consistency.

## 4. Statistical Rigor & Limitations

- **Multiple Comparisons**: Feature importance comparisons across bins are descriptive. No formal hypothesis testing (t-tests) is performed to avoid inflating Type I error without correction, given the exploratory nature of the feature ranking.
- **Sample Size**: Power analysis is deferred. The plan assumes the filtered dataset size is $\ge 200$ (based on spec assumptions). If $< 200$, the report will flag reduced statistical power.
- **Causal Inference**: Claims are strictly **associational**. The model predicts decomposition energy based on descriptors; it does not claim causal mechanisms.
- **Collinearity**: HOMO/LUMO and Band Gap are definitionally related. The plan **drops Band Gap** from the model input to ensure interpretable feature importance.
- **Dataset Limitation**: The lack of a verified experimental onset potential dataset is a critical limitation. The plan proceeds with DFT internal validation and flags the external validation gap.
- **Tautology Risk**: The model predicts DFT-derived energies using DFT-derived descriptors. The plan explicitly acknowledges this learns "DFT internal consistency" rather than "generalizable physical law". The "Physical Reality Validation" is redefined as "DFT Consistency Validation".

## 5. Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Strategy**:
 - Use `datasets` library for streaming or partial loading to stay under RAM limits.
 - Random Forest with `n_estimators=100` is CPU-efficient.
 - No GPU libraries (CUDA, bitsandbytes) used.
 - Data subset to ~1000 entries max for the sensitivity sweep to ensure < 6h runtime.