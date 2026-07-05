# Research: Predicting the Stability of Perovskite Structures Using Machine Learning

## 1. Problem Definition
The goal is to predict the thermodynamic stability (decomposition energy) of ABX₃ perovskite structures using machine learning. Stability is quantified by the decomposition energy ($E_{decomp}$) in eV/atom, where lower (more negative) values indicate higher stability. The model will use physical descriptors derived from ionic radii and electronegativity to generalize stability predictions to hypothetical compositions.

## 2. Dataset Strategy

### 2.1 Verified Sources
The plan relies exclusively on the following verified datasets to ensure reproducibility and accuracy. **Note**: The Materials Project REST API is used as a primary source, but the OQMD datasets serve as the verified fallback to ensure CI reliability.

| Dataset Name | Description | Verified URL | Usage in Plan |
|:--- |:--- |:--- |:--- |
| **OQMD (Parquet)** | Structural database with decomposition energies and lattice parameters. | ` | **Primary SSoT** if it contains required structural columns. Used for efficient streaming. |
| **OQMD (CSV)** | CSV version of OQMD targets. | ` | **Fallback** if Parquet lacks structural columns or is inaccessible. |
| **Materials Project** | REST API for crystal structures and energies. | ` Name or service not known)"))] | Primary source; fallback to OQMD if API fails or yields < 5,000 entries. |

*Note: The plan explicitly excludes NLP/ChemNLP text corpora (e.g., `kjappelbaum/chemnlp-oqmd` as a text dataset) as they do not contain the raw crystallographic data (lattice parameters, atomic coordinates) required for `pymatgen` descriptor calculation.*

### 2.2 Dataset Fit Analysis
- **Target Variable**: The verified OQMD datasets contain `decomposition_energy` (or `e_above_hull`), which serves as the regression target.
- **Predictor Variables**: The datasets contain structural information (Space Group, lattice parameters, atomic species).
 - *Gap Check*: The datasets do not pre-calculate the Goldschmidt tolerance factor ($t$) or octahedral factor ($\mu$).
 - *Resolution*: The plan (Phase 1) will use `pymatgen` to calculate these descriptors dynamically from the raw structural data (ionic radii, electronegativity) available in the `pymatgen` periodic table, ensuring the features match the spec's requirements.
- **Structural Filter**: The plan will filter for Space Group 221 (Cubic) and 148 (Rhombohedral) as required by FR-001. The verified OQMD datasets contain space group information, enabling this filter.
- **DFT Functional Consistency**: The OQMD dataset is based on **PBE** (Perdew-Burke-Ernzerhof) functional. The plan will record this in the model metadata to ensure consistency between training and prediction contexts.

### 2.3 Data Volume & Feasibility
- **Target**: [deferred] to [deferred] entries.
- **Feasibility**: The OQMD datasets are large, but the plan will stream or sample data to fit within the 7GB RAM limit. The `pymatgen` descriptor calculation is CPU-intensive but feasible for ~10k entries on a 2-core runner within 6 hours.

## 3. Methodology

### 3.1 Descriptor Calculation (FR-002)
Descriptors are calculated using `pymatgen` to ensure numerical rigor (Constitution Principle VI):
- **Goldschmidt Tolerance Factor ($t$)**: $t = \frac{r_A + r_X}{\sqrt{2}(r_B + r_X)}$
- **Octahedral Factor ($\mu$)**: $\mu = \frac{r_B}{r_X}$
- **Ionic Radius Mismatch**: Variance or difference in ionic radii.
- **Electronegativity Difference**: Difference between A/B and X sites.

*Validation*: `pymatgen` uses standard Shannon-Prewitt radii. The plan will log any elements with missing radii (Edge Case) and exclude them.

### 3.2 Model Selection (FR-003)
- **Algorithm**: RandomForestRegressor.
- **Rationale**: Robust to non-linear relationships, handles mixed feature types, and provides feature importance (SC-002). It is CPU-tractable and does not require GPU acceleration (FR-006).
- **Hyperparameter Tuning**: **Nested Cross-Validation**.
 - **Outer Loop**: 80/20 split (Train/Test).
 - **Inner Loop**: 5-fold CV grid search over `max_depth` {10, 15, 20} and `min_samples_leaf` {1, 2, 4}.
- **Metric**: Root Mean Squared Error (RMSE) in eV/atom on the **held-out test set**.
- **Threshold**: Target RMSE ≤ 0.15 eV/atom (SC-001).
- **Validation**: **Permutation-based sensitivity analysis** will be used to validate feature importance (SC-002) rather than relying solely on intrinsic model weights.

### 3.3 Virtual Screening (FR-004)
- **Library Generation**: Combinatorial substitution of A={K,Rb,Cs,Ba,Sr}, B={Ti,Zr,Hf,Sn,Ge}, X={F,Cl,Br,I}.
- **Feasibility Filter**: 0.8 ≤ $t$ ≤ 1.1.
- **OOD Check**: Verify that the hypothetical library includes compositions with descriptor values outside the training distribution to ensure true extrapolation testing.
- **Prediction**: Apply the trained model to predict $E_{decomp}$.
- **Ranking**: Sort by predicted energy; flag candidates with $E_{decomp} < -0.1$ eV/atom.

## 4. Risk Assessment & Mitigation

| Risk | Impact | Mitigation Strategy |
|:--- |:--- |:--- |
| **API Rate Limiting** | High (Data ingestion fails) | Implement exponential backoff retry logic. Fall back to verified OQMD CSV/Parquet sources if MP API fails. |
| **Missing Ionic Radii** | Medium (Feature calculation fails) | Log warnings and exclude entries with undefined radii. Use `pymatgen`'s fallback radii if available, otherwise exclude. |
| **Memory Overflow** | High (CI job crashes) | Stream data processing; avoid loading the full OQMD tar.gz into RAM. Process in chunks. |
| **Model Performance** | Medium (RMSE > 0.15) | Log "low confidence" flag. Do not auto-flag candidates for experimental follow-up without manual review. |
| **Compute Time** | High (> 6 hours) | Limit grid search size. Use CPU-optimized `scikit-learn` settings. Sample data if necessary. |
| **DFT Functional Mismatch** | Medium (Systematic error) | Explicitly record PBE functional in model metadata. Acknowledge that predictions are valid within the PBE framework. |

## 5. Decision Rationale
- **Why RandomForest?** It is the standard baseline for materials property prediction, requires no hyperparameter tuning for initialization, and is robust to the small dataset size (relative to deep learning needs). It runs efficiently on CPU.
- **Why OQMD?** It is the only verified dataset in the input block that contains the necessary energy and structural data. The Materials Project API is used as a primary source but is not guaranteed to be accessible in CI; OQMD serves as the verified fallback.
- **Why CPU-only?** The spec explicitly forbids GPU usage (FR-006) and the compute constraints (2 cores, 7GB RAM) make GPU libraries (bitsandbytes, CUDA) infeasible. RandomForest is sufficiently powerful for this task without GPU acceleration.
- **Why Nested CV?** To prevent overfitting on the hyperparameter search and provide an unbiased estimate of generalization error on the held-out test set.
