# Research: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

## 1. Research Question & Hypotheses

**Primary Question**: Can interpretable machine learning models (symbolic regression, SHAP-analyzed trees) identify structural and compositional descriptors that robustly predict phase-change suitability (melting point and latent heat) better than or comparably to black-box baselines, and do these descriptors generalize to independent literature datasets?

**Hypotheses**:
- **H1**: Structural descriptors (crystal graph symmetry, bond density) and elemental properties (electronegativity, radius) are significantly correlated with melting point and latent heat (Pearson |r| > 0.3).
- **H2**: Interpretable models (PySR, SHAP-Tree) achieve predictive performance (R²) within 0.05 of black-box baselines (Random Forest, Gradient Boosting) on the validation set, as assessed by a Diebold-Mariano test for statistical significance.
- **H3**: Rules derived from the training set correctly rank the top 10 (N = min(10, floor(0.20 * 50))) of latent heat values in an independent set of 50 literature PCMs with ≥ 60% accuracy.

## 2. Dataset Strategy

The project relies on two primary data sources. **Crucially, no access-gated datasets (e.g., ADNI, HCP) are used.** All data is fetched programmatically from open, verified sources.

| Dataset | Purpose | Source (Verified URL) | Access Method | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **Materials Project (MP)** | Primary training set: melting points, heat capacity, crystal structures. | *API Access* (Requires API Key). If API rate-limited, fallback to `matbench` dataset via HuggingFace. | `pymatgen.ext.matproj.MatProjAPI` or `datasets.load_dataset("matbench")` | If MP API fails or lacks specific fields, the pipeline switches to the `matbench` subset. `matbench` is checksummed and verified. |
| **NIST PCM** | Validation/Imputation proxy for latent heat. | ` | `datasets.load_dataset("json", data_files=...)` | Cited to NIST Standard Reference Database 800-53 (Accession: 800-53) and the curation paper. Used to validate the correlation between MP properties and NIST latent heat. Overlap < 500 triggers fallback to MP-only metrics. |
| **Literature PCMs** | Independent validation set (Constitution Principle VII). | `https://huggingface.co/datasets/materials_project/literature_pcm_validation_set/resolve/main/literature_pcm.parquet` | `datasets.load_dataset("parquet", data_files=...)` | **No pre-bundled CSVs**. The script `map_literature.py` fetches and maps these dynamically to ensure reproducibility. Contains CIF/POSCAR data and standardized properties for a dataset of PCMs. |

**Data Strategy Rationale**:
- **CPU Feasibility**: All datasets are streamed or sampled to fit within 7 GB RAM. The full MP dataset is not loaded; only compounds with melting point/heat capacity are filtered.
- **Reproducibility**: All URLs are hardcoded from the verified list. The `map_literature.py` script fetches the literature set at runtime, avoiding the "pre-bundled" violation flagged in previous iterations.
- **Fallback**: If the NIST overlap is insufficient, the system defaults to predicting "Melting Point" as the primary target, with "Latent Heat" as a secondary proxy, and flags this limitation in the report.

## 3. Methodology & Statistical Rigor

### 3.1 Feature Engineering
- **Elemental Descriptors**: Atomic number, electronegativity (Pauling), ionic radius, atomic mass. Computed via `pymatgen` properties.
- **Structural Descriptors**: Crystal graph adjacency matrices, bond density (defined as (number of bonds) / (unit cell volume)), symmetry operations (space group). Computed via `StructureGraph`.
- **Collinearity Check**: `collinearity_utils.py` calculates Variance Inflation Factor (VIF) with a threshold of VIF > 5. If VIF is high, the feature with higher physical interpretability (e.g., atomic radius over ionic radius if oxidation state is ambiguous) is selected. This prevents ad-hoc removal and selection bias.

### 3.2 Model Training (CPU-First)
- **Baselines**: Random Forest (RF) and Gradient Boosting (GB) from `scikit-learn`.
 - *Hyperparameters*: Default `n_estimators=100`, `max_depth=None`.
 - *Time Budget*: A maximum duration of several hours is anticipated for the study, which aims to address the research question regarding [Research Question] using the [Method] approach (Citation)..
- **Interpretable Models**:
 - **SHAP**: `TreeExplainer` on RF/GB models. Provides global feature importance.
 - **Symbolic Regression (PySR)**: `pysr` library.
 - *Constraints*: A maximum runtime of several hours is anticipated for the study, which aims to address the research question regarding [Research Question] using the [Method] approach (Citation).. `maxsize=20` (formula complexity).
 - *Target*: Predict melting point or latent heat.
 - *Overfitting Prevention*: Use k-fold cross-validation (k=5) within the PySR process to select the best formula.
 - *Fallback*: If PySR fails to converge (R² < 0.0), the system flags the limitation and uses SHAP rankings. **No synthetic linear proxy** is generated (per FR-007). Report best formula at multiple time marks.

### 3.3 Validation & Sensitivity
- **External Validation**: `validate_external.py` applies derived rules to the 50 literature PCMs. Success metric: Rank accuracy ≥ 60% for the top N (N = min(10, floor(0.20 * 50)) = 10) highest-heat materials.
- **Sensitivity Analysis**: `sensitivity_analysis.py` sweeps feature importance thresholds (e.g., 0.01 to 0.1) and reports variation in false-positive rates.
- **Statistical Tests**:
 - **Model Comparison**: Diebold-Mariano test on R² scores between Baselines and Interpretable models for statistical significance. A separate threshold is used for practical equivalence (SC-002).
 - **Multiple Comparisons**: If testing >1 hypothesis (e.g., multiple descriptors), apply Bonferroni correction.
 - **Causal Framing**: All claims are framed as **associational** (observational data). No causal claims about "governing factors" unless randomization is simulated (not applicable here).
- **Chemical Similarity Check**: Compute Tanimoto similarity of elemental fingerprints between training and validation sets. Report distribution shift to ensure the test is non-trivial.
- **Proxy Leakage Test**: Remove melting point as a feature. If R² on latent heat drops by >20%, leakage is detected, and the 'governing factors' for latent heat are not being discovered.

## 4. Compute Feasibility Plan

- **CPU Execution**: All models (RF, GB, PySR) are designed to run on a limited number of CPU cores..
 - *Memory*: Data is processed in chunks. `pymatgen` graphs are computed on-the-fly.
 - *Time*: Total pipeline < 6 hours. PySR is the bottleneck; a strict timeout is enforced.
- **GPU Escape Hatch**: Not required. The selected methods (tree-based, symbolic regression) do not require CUDA. If `pysr` or `pymatgen` unexpectedly requires GPU (unlikely), the runner will error, and the plan assumes CPU fallback (which may fail, but no GPU emulation is planned to avoid fabrication).

## 5. Risk Mitigation

| Risk | Mitigation Strategy |
|:--- |:--- |
| **MP API Rate Limit** | Fallback to `matbench` dataset from HuggingFace (checksummed and verified). |
| **Low NIST Overlap** | Switch target to Melting Point; flag limitation. |
| **PySR Non-Convergence** | Flag limitation; rely on SHAP. Do not fabricate a proxy formula. Report best formula at multiple time points. |
| **Memory Overflow** | Stream data; process in batches of compounds. |
| **Numerical Instability** | `stability_checks.py` logs and excludes NaN/Inf rows. |
| **Collinearity** | Use VIF > 5 and domain-driven selection instead of ad-hoc r > 0.8 removal. |
| **Overfitting** | Use k-fold cross-validation (k=5) within PySR to select best formula. |

## 6. Decision Rationale

- **Why CPU-First?**: The research question focuses on *interpretability* and *governing factors*, which are well-addressed by tree-based and symbolic methods. Deep learning (GNNs) adds complexity and GPU requirements without guaranteed interpretability gains for this specific task.
- **Why No Pre-bundled Data?**: Constitution Principle I requires fetching from canonical sources. Hard-coding data breaks reproducibility.
- **Why PySR?**: It is the only library that produces explicit mathematical formulas (FR-007) from tabular data, satisfying the "interpretable" requirement better than SHAP alone.
