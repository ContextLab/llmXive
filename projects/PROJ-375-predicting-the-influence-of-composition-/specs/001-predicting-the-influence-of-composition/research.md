# Research: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

## Objective
Assess whether compositional descriptors derived solely from elemental properties can predict the coefficient of thermal expansion (CTE) of metallic glasses, identify the most influential descriptors, and rigorously test statistical significance, computational efficiency, and baseline physical approximations.

## Dataset Strategy
| Source | Access Method | Notes |
|--------|---------------|-------|
| **Curated literature CSV** (user‑provided) | Local file `data/raw/curated_metallic_glass.csv` | Primary ground‑truth dataset (FR‑001). Must contain `material_id`, `composition`, `cte`. |
| **Materials Project API** | `pymatgen.ext.matproj.MPRester` with free API key (`MP_API_KEY`) | Retrieves additional entries where the description contains “glass”. Used for supplemental coverage (FR‑001). |
| **AFLOWlib API** | Public REST endpoint (no verified URL) | Optional supplemental source; if unreachable, pipeline proceeds with MP data only. |
| **Elemental CTE values** | Materials Project pure‑element entries (via same API) | Supplies baseline predictor (SC‑001). If elemental CTEs are unavailable, baseline uses the average of known elemental CTEs from the curated dataset. |

> **Dataset Availability Verdict**: The curated CSV is part of the repository; the Materials Project API provides open, programmatic access to additional metallic‑glass entries. No gated datasets are required, satisfying the compute‑feasibility constraints.

## Methodological Decisions & Rationale
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **CPU‑only modeling (scikit‑learn)** | Guarantees execution on free GitHub Actions runner. | All steps on default runner. |
| **5‑fold GroupKFold by alloy family** | Prevents leakage of identical composition families between train and test (Constitution VII). | `sklearn.model_selection.GroupKFold`. |
| **Permutation test (≥ 1 000 iterations) with target shuffling** | Provides a robust p‑value for SC‑002; shuffling destroys any true X‑Y relationship while preserving feature structure. | Parallelised across 2 cores (`joblib`). |
| **VIF threshold = 5.0 with PCA‑Ridge fallback** | Enforces FR‑008; ensures multicollinearity does not invalidate coefficient interpretations. | One‑time computation after descriptor generation. |
| **Baseline weighted‑average elemental CTE model** | Supplies SC‑001 comparison; uses independent physical data (elemental CTE). | Simple linear regression on a single predictor. |
| **Runtime & memory logging** | Implements SC‑004; logs stored in `results/computational_efficiency.json`. | Minimal overhead. |
| **Power analysis** | Confirms dataset size is sufficient to detect modest effect sizes; if not, limitation is reported. | Performed after ingestion; results saved to `results/power_analysis.txt`. |
| **Fixed random seeds** | Guarantees reproducibility (Constitution I). | `np.random.seed(42)` and `random.seed(42)` at script start; `random_state=42` for all estimators and `joblib`. |

### Statistical Rigor Checklist
- **Multiple‑Comparison Correction**: Not required (single primary hypothesis per model).  
- **Power / Sample‑Size**: Reported in Phase 0; contingency plan for N < 500.  
- **Causal Claims**: All statements are **associational**; data are observational (DFT or experimental).  
- **Measurement Validity**: CTE values sourced directly from the curated CSV (experimental) or the Materials Project (DFT).  
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
| High VIF across all descriptors | Forces fallback to PCA, reducing interpretability. | Document fallback; still satisfies FR‑008. |
| AFLOWlib endpoint downtime | Loss of supplemental data. | Log warning; continue with MP data only. |
| Runtime or memory overrun on CI | Job failure. | Phase 6 monitors limits; aborts early with clear error. |
| Mis‑identification of alloy families for stratification | Potential leakage. | Use full elemental set as grouping key; fallback to random split. |
| Permutation test randomness | Unstable p‑values. | Fixed random seed (`np.random.seed(42)`). |

---
