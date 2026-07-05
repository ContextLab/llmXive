# Research: Predicting Molecular Diffusion Coefficients in Liquids with Graph Neural Networks

## 1. Problem Definition

Predicting molecular diffusion coefficients ($D$) in liquids is a critical task in chemical engineering and drug discovery. Traditional methods rely on molecular dynamics (MD) simulations, which are computationally expensive and time-consuming. This project investigates whether **static molecular topology** (graph structure) combined with **scalar solvent descriptors** (viscosity, dielectric constant) can accurately predict $D$ using a lightweight Graph Neural Network (GNN), bypassing explicit dynamic simulations.

**Hypothesis**: A Message Passing Neural Network (MPNN) trained on static graphs and solvent properties will achieve a Pearson correlation ($r$) > 0.7 with experimental $D$ values, significantly outperforming a linear regression baseline on molecular fingerprints and a **solvent-only baseline**.

## 2. Dataset Strategy

### 2.1 Source Selection

The project relies on the following verified datasets. **No other URLs are cited.**

| Dataset Name | Verified URL / Source | Relevance |
|:--- |:--- |:--- |
| **NIST TRC Diffusion Data** | `thermo` Python library (proxies NIST Standard Reference Database 147) | Primary source of experimental diffusion coefficients ($D$), SMILES, solvent types, viscosity, and dielectric constants. |
| **SMILES Test Set** | ` | Validation source for SMILES parsing robustness (no diffusion data). |
| **SELFormer SMILES** | ` | Validation source for SMILES diversity (no diffusion data). |

**Data Access Strategy**:
The primary data source is the **NIST Thermodynamics Research Center (TRC)** database, accessible programmatically via the `thermo` Python library. This library provides verified, curated experimental diffusion coefficients for various solute-solvent pairs.
* **Action**: The `ingestion.py` script will use `thermo.diffusion` to query and download the required data (SMILES, solvent, $D$, viscosity, dielectric).
* **Fallback**: If the NIST query fails or yields insufficient data, the script will attempt to load a local CSV (if provided by the user) but will not proceed with results if the primary verified source is unavailable.

**Dataset Size Estimation & Power Analysis (Addressing Concern methodology-40836e09)**:
* **Source Characteristics**: NIST Standard Reference Database 147 (via `thermo`) historically contains approximately **[deferred] to [deferred] unique binary diffusion coefficient entries** across a wide range of solute-solvent pairs.
* **Filtering Impact**: The requirement for specific solvent descriptors (viscosity, dielectric constant) will filter out entries where these are missing or undefined. Based on typical coverage in NIST TRC for common solvents (water, alcohols, hydrocarbons), we conservatively estimate that **~60-70%** of the raw diffusion entries will have complete descriptor data.
* **Estimated Usable N**: $[deferred] \times 0.6 \approx 900$ to $[deferred] \times 0.7 \approx [deferred]$ usable pairs.
* **Power Justification**: A sample size of **N = 900+** is well above the threshold required for the **paired t-test** (FR-005) to achieve >90% statistical power at $\alpha=0.05$ for detecting medium effect sizes (Cohen's $d \approx 0.5$) in the difference of absolute errors between the GNN and baseline. Even if the dataset shrinks to the lower bound of ~500 pairs after strict filtering, power remains >80%.
* **Safety Net**: The `eval.py` script will include a runtime check: if the final usable $N < 50$, the pipeline will abort with a clear error message indicating insufficient power for statistical significance testing, preventing invalid claims.

### 2.2 Data Requirements

To train the model, the dataset must contain:
1. **SMILES**: String representation of the solute molecule.
2. **Solvent Type**: Identifier for the solvent (to map to descriptors).
3. **Diffusion Coefficient**: Target variable ($D$).
4. **Solvent Descriptors**: Viscosity ($\eta$), Dielectric Constant ($\epsilon$).

If a record lacks any of these, it will be excluded and logged as `[MISSING_DATA_EXCLUDED]` (FR-007).

## 3. Methodology

### 3.1 Featurization (FR-002)

1. **Graph Construction**: Use `RDKit` to convert SMILES into a `PyTorch Geometric` `Data` object.
 * Nodes: Atoms (features: atomic number, degree, hybridization, formal charge).
 * Edges: Bonds (features: bond type, conjugation, stereo).
2. **Solvent Descriptors**: Map solvent types to scalar values (viscosity, dielectric constant). These are concatenated to the graph's global context vector or added as node features.

### 3.2 Model Architecture (FR-003)

* **MPNN**: A single-layer Message Passing Neural Network.
 * Aggregation: Mean or Sum.
 * Update: MLP with ReLU.
 * Readout: Global mean pooling + MLP.
 * **Constraint**: Must run on CPU (`torch.device("cpu")`). No CUDA.
* **Baseline 1 (Fingerprint + Solvent)**: Linear Regression.
 * Input: Morgan Fingerprints (radius=2, 2048 bits) + Solvent Descriptors.
 * Purpose: To establish a lower bound for performance using standard descriptors.
* **Baseline 2 (Solvent-Only)**: Linear Regression.
 * Input: Viscosity + Dielectric Constant ONLY (no molecular structure).
 * Purpose: To isolate the contribution of the molecular graph topology. If GNN $\approx$ Baseline 2, the graph adds no value.

### 3.3 Training Strategy (FR-004)

* **Split**: 5-fold Cross-Validation.
* **Stratification**: By solvent type to ensure balanced distribution of solvent environments.
* **Random Seed**: Fixed at 42 for all random operations (numpy, torch, sklearn).
* **Optimizer**: Adam (learning rate 0.001).
* **Loss**: Mean Squared Error (MSE).
* **Epochs**: 50 (or early stopping if validation loss plateaus).

### 3.4 Evaluation & Statistical Testing (FR-005)

* **Metrics**: Pearson Correlation Coefficient ($r$), Root Mean Squared Error (RMSE).
* **Primary Statistical Test**: **Paired t-test** on the absolute errors ($|y_{pred} - y_{true}|$) of the GNN vs. the Baselines, **as mandated by FR-005**.
 * *Normality Check*: Before running the t-test, a Shapiro-Wilk test will be performed on the distribution of *differences* in absolute errors.
 * *Fallback*: If the differences are found to be significantly non-normal (p < 0.05), the pipeline will fall back to the **Wilcoxon signed-rank test** to ensure robustness, but the primary report will note the violation of normality assumptions.
 * $H_0$: No difference in error distributions (mean difference = 0).
 * $H_1$: GNN errors are significantly lower (mean difference > 0).
 * Significance level: $\alpha = 0.05$.
* **Comparisons**:
 1. GNN vs. Baseline 1 (Fingerprint + Solvent)
 2. GNN vs. Baseline 2 (Solvent-Only)
* **Power Consideration**: As detailed in Section 2.1, the estimated dataset size (N ~ 900-1400) provides sufficient power for the t-test to detect meaningful improvements.

### 3.5 Sensitivity & Robustness (FR-006)

* **Hyperparameter Sweep**: Message passing steps $\in \{1, 2, 3\}$.
* **Ablation Study**: Train a version of the GNN *without* solvent descriptors to isolate the contribution of the graph structure.
* **Outlier Handling**: Report metrics with full dataset and with top [deferred]% residuals removed.

## 4. Compute Feasibility

* **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
* **Memory**:
 * Graph featurization of a large-scale molecular dataset: substantial storage requirements.
 * Model training: < 1GB.
 * Total overhead: < 2GB.
* **Runtime**:
 * Ingestion (NIST query): < 5 mins.
 * Training (multiple folds): ~ mins.
 * Sensitivity: ~ mins.
 * **Total**: Well [deferred].
* **Strategy**: If the dataset exceeds a predefined size threshold, a random sample will be taken for training to ensure feasibility.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **NIST Data Access Failure** | Critical (Project cannot run) | Script checks `thermo` connectivity; if fail, exit with clear error. Do NOT fabricate data. |
| **Negative Correlation** | Low (Valid scientific result) | Report $r < 0.3$ as a "null result" per SC-001. |
| **Memory Overflow** | Medium | Sample dataset to a representative scale of molecules; monitor RAM usage. |
| **SMILES Parsing Errors** | Low | Log invalid SMILES and exclude; continue processing. |
| **Insufficient Sample Size** | Medium (Invalid stats) | Runtime check for N < 50; abort if power is insufficient. |

## 6. Decision Log

* **Decision**: Use `torch-geometric` with CPU backend.
 * *Rationale*: Required for GNN capability; CPU-only wheels available and fit memory constraints.
* **Decision**: Exclude records with missing data rather than impute.
 * *Rationale*: Imputation of physical properties (viscosity) introduces bias; exclusion is safer for scientific rigor (FR-007).
* **Decision**: Use Paired t-test (with normality check) as primary test.
 * *Rationale*: Mandated by FR-005; Wilcoxon fallback added for robustness if normality assumptions are violated, ensuring scientific soundness without violating the spec.
* **Decision**: Add Solvent-Only Baseline.
 * *Rationale*: Necessary to distinguish molecular structure effects from solvent effects (Scientific Soundness concern).
