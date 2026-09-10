# Research: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

## Objective
To determine whether compositional descriptors derived from elemental properties can predict the coefficient of thermal expansion (CTE) of metallic glasses, and to identify the key compositional drivers while rigorously testing statistical significance, computational efficiency, and the robustness of baseline physical approximations.

## Dataset Strategy
| Source | Access Method | Notes |
|--------|---------------|-------|
| Materials Project (MP) API | `pymatgen.ext.matproj.MPRester` with a free API key (environment variable `MP_API_KEY`) | Retrieves entries that include the `thermal_expansion_coefficient` field via the **Thermal Properties** endpoint. Amorphous entries are identified by the MP `"glass"` tag, or, if missing, by the absence of a space‑group and a `structure_type` containing “amorphous”. |
| AFLOWlib | Public REST API (`https://aflowlib.org/AFLOWDATA/AFLOWLIB_LIBRARY/v1.2.0/`) | Queries for `property=thermal_expansion_coefficient` and `keywords=glass`. If the endpoint is unreachable or returns no glass entries, the pipeline logs a warning and proceeds with MP data only (still satisfying FR‑001). |

> **Dataset Availability Verdict**: Open, programmatic sources exist for both MP and AFLOWlib. If the combined dataset yields an insufficient number of entries, a power‑analysis limitation will be reported in the final paper (SC‑004).

## Methodological Decisions & Rationale
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **CPU‑only modeling** (scikit‑learn) | Fits within GitHub Actions free tier; no GPU needed for linear models or Random Forests. | All steps run on the default runner. |
| **k‑fold stratified CV by alloy family** | Required by Constitution Principle VII; stratification by the two most abundant elements reduces leakage compared to single‑element stratification. | Scikit‑learn `StratifiedKFold` (n_splits=5). |
| **Permutation test (1 000 iterations) with target shuffling** | Provides a robust p‑value for SC‑002; shuffling the CTE target relative to the fixed feature matrix breaks any X‑Y relationship while preserving feature structure, yielding a valid null distribution. | Parallelized across the two CPU cores (`joblib.Parallel`). |
| **VIF threshold with PCA‑Ridge fallback** | Implements FR‑008; if *all* descriptors exceed VIF > 5.0, the pipeline retains the descriptor with the lowest VIF, applies PCA (≥95 % variance retained) and trains a Ridge Regression model, ensuring a trainable model. | Computed once after descriptor generation. |
| **Baseline weighted‑average elemental CTE model** | Supplies SC‑001 comparison; elemental CTE values are taken from the Materials Project pure‑element entries (e.g., `mp-112` for Zr), guaranteeing independence from the alloy dataset. The baseline is trained as a linear regression on the single predictor and evaluated with the same metrics as the main models. | Minimal cost; training is a single‑parameter fit. |
| **Thermal‑history flagging & sensitivity analysis** | Implements FR‑009; entries with non‑standard `thermal_history` strings are flagged (`thermal_history_flag=True`) for downstream sensitivity analysis (Phase 5). |
| **Resource & efficiency measurement** | Implements SC‑004; runtime and memory are measured, compared to the free‑tier limits, and a boolean `pass` flag is stored in `results/computational_efficiency.json`. |
| **Citation of elemental property source** | Satisfies Constitution Principle II; the `mendeleev` package is cited with its verified PyPI URL. |

### Statistical Rigor Checklist
- **Multiple‑Comparison Correction**: Not required (only one primary hypothesis per model).  
- **Power / Sample‑Size**: The actual number of metallic‑glass entries retrieved will be reported; if < 200, a power‑limitation note will be included (per SC‑004).  
- **Causal Claims**: All statements are **associational**; the data are observational (DFT or experimental values from MP/AFLOWlib).  
- **Measurement Validity**: CTE values come from the Materials Project `thermal_expansion_coefficient` field and from AFLOWlib where available; both are documented in their respective APIs.  
- **Collinearity**: VIF analysis (FR‑008) and the PCA‑Ridge fallback ensure that reported importances are not confounded by severe multicollinearity.

## Expected Deliverables
- Cleaned dataset (`clean_mg_data.parquet`) with all required columns, VIF report, and `thermal_history_flags.csv`.  
- Trained model artifacts (`linear_regression.pkl`, `random_forest.pkl`, `baseline_linear.pkl`).  
- Performance metrics JSON (`model_performance.json`) and baseline metrics (`baseline_metrics.json`).  
- Permutation p‑value and null distribution (`permutation_null_distribution.npy`).  
- Feature‑importance CSV (`feature_importance.csv`) and Spearman diagnostic (`spearman_correlation.txt`).  
- Computational‑efficiency JSON (`computational_efficiency.json`).  
- Full reproducible CI pipeline (GitHub Actions workflow not shown here).  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient metallic‑glass entries from MP/AFLOWlib | May reduce statistical power (SC‑004). | Report actual count; if < 200, include a limitation statement and perform a bootstrap power estimate. |
| Missing `amorphous` flag for some entries | May leak crystalline data into the model. | Use the tag‑based detection plus space‑group absence heuristic; flag ambiguous entries for sensitivity analysis. |
| High VIF leading to dropping all descriptors | Could leave no predictors. | Fallback strategy (retain lowest‑VIF descriptor, PCA, Ridge Regression) as described in Phase 1. |
| AFLOWlib endpoint downtime | Data loss. | Log the failure and continue with MP data; the warning is recorded in `results/runtime_log.txt`. |
| Resource overrun on CI | Job abort. | Phase 6 monitors runtime/memory and aborts early with a clear error message; the CI will report the failure. |
| Baseline elemental CTE source bias | Baseline may be tautologically linked to targets. | Elemental CTEs are taken from **pure‑element** MP entries, which are independent of alloy calculations. |
| Ambiguous thermal‑history strings | Inconsistent metadata. | Flag non‑standard strings; downstream analyses can optionally exclude flagged rows. |
| Stratified split leakage | Inflated test performance. | Stratify by alloy family (two most abundant elements) rather than a single primary element. |
| Deterministic coupling of radius and size‑mismatch | Redundant predictors. | Drop `atomic_size_mismatch` when VIF > 5.0; retain only `weighted_mean_atomic_radius`. |
| Permutation test ambiguity | Invalid null hypothesis. | Explicitly shuffle the target vector while keeping features fixed, refit, and compute test‑set R² to build the null distribution. |
| Baseline comparison ambiguity | Unclear metric. | Train a baseline linear regression on the weighted‑average elemental CTE and evaluate R², MAE, RMSE on the test set. |

---



