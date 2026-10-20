# Research: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

## Objective
To assess whether compositional descriptors derived solely from elemental properties can predict the coefficient of thermal expansion (CTE) of *metallic glasses*, and to identify the most influential descriptors while rigorously testing statistical significance, computational efficiency, and baseline physical approximations.

## Dataset Strategy
| Source | Access Method | Notes |
|--------|---------------|-------|
| Materials Project (MP) API | `pymatgen.ext.matproj.MPRester` with free API key (`MP_API_KEY`) | Retrieves **all** entries that contain a non‑null `thermal_expansion_coefficient` **and** contain the keyword “glass” in the description or have `material_type` indicating amorphous/metallic‑glass. This yields the metallic‑glass subset required by FR‑001. |
| AFLOWlib (optional) | Public REST API (no verified URL) | Queried for additional metallic‑glass entries; if unreachable, the pipeline proceeds with MP data only (still satisfies FR‑001 after scope adjustment). |

> **Dataset Availability Verdict**: Open, programmatic access exists for metallic‑glass CTE data via keyword filtering on the Materials Project. The dataset size (typically a few hundred to a few thousand rows) fits comfortably within CI storage and memory limits.

## Methodological Decisions & Rationale
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **CPU‑only modeling** (scikit‑learn) | Guarantees execution on the free GitHub Actions runner. | All steps on the default runner. |
| **5‑fold GroupKFold by alloy family** | Prevents leakage of identical composition families between train and test folds (Constitution Principle VII). | Scikit‑learn `GroupKFold`. |
| **Permutation test (≥ 1 000 iterations) with target shuffling** | Provides a robust p‑value for SC‑002; shuffling breaks any real X‑Y relationship while preserving feature structure. | Parallelised across 2 cores (`joblib`). |
| **VIF threshold (5.0) with PCA‑Ridge fallback** | Enforces FR‑008; ensures multicollinearity does not invalidate coefficient interpretations. | One‑time computation after descriptor generation. |
| **Baseline weighted‑average elemental CTE model** | Supplies SC‑001 comparison; uses independent elemental CTE values from pure‑element MP entries. | Simple linear regression on a single predictor. |
| **Runtime & memory logging** | Implements SC‑004; logs are stored in `results/computational_efficiency.json`. | Minimal overhead. |
| **Power analysis** | Confirms that the dataset size is sufficient to detect modest effect sizes; if not, a limitation is reported. | Performed after ingestion; results saved to `results/power_analysis.txt`. |
| **Random seed fixing** | Guarantees reproducibility (Constitution Principle I). | `np.random.seed(42)` and `random.seed(42)` at script start; `random_state=42` for all scikit‑learn estimators and `joblib` parallelism. |

### Statistical Rigor Checklist
- **Multiple‑Comparison Correction**: Not needed (single primary hypothesis per model).  
- **Power / Sample‑Size**: Reported above; contingency plan for N < 200.  
- **Causal Claims**: All statements are **associational**; data are observational (DFT or experimental).  
- **Measurement Validity**: CTE values sourced directly from the Materials Project `thermal_expansion_coefficient` field.  
- **Collinearity**: Addressed via VIF analysis and PCA‑Ridge fallback (FR‑008).  

## Expected Deliverables
- `data/processed/clean_alloy_data.parquet` – cleaned dataset with all required columns and VIF report.  
- Trained model files: `models/linear_regression.pkl`, `models/random_forest.pkl`, `models/baseline_linear.pkl`.  
- Performance metrics JSON: `results/model_performance.json` and `results/baseline_metrics.json`.  
- Permutation test outputs: `results/permutation_null_distribution.npy` and p‑value.  
- Feature‑importance CSV and correlation diagnostics (`results/feature_importance.csv`, `results/correlation_diagnostics.json`).  
- Computational‑efficiency JSON (`results/computational_efficiency.json`).  
- JSON‑Schema contracts (`contracts/*.schema.yaml`).  
- Unit tests validating schema compliance (`tests/unit/`).  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient metallic‑glass CTE entries | May reduce statistical power (SC‑004). | Power analysis; explicit coverage warning; Specification Amendment flag. |
| High VIF across all descriptors | Could force fallback to PCA, altering interpretability. | Document fallback clearly; still satisfies FR‑008. |
| AFLOWlib endpoint downtime | Loss of supplemental data. | Log warning; continue with MP data only. |
| Runtime or memory overrun on CI | Job failure. | Phase 6 monitors limits; aborts early with clear error. |
| Mis‑identification of alloy families for stratification | Potential leakage. | Use full elemental set as grouping key; fallback to random split if needed. |
| Permutation test randomness | Unstable p‑values. | Fixed random seed (`np.random.seed(42)`) for reproducibility. |

---


