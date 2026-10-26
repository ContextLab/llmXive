# Research: Predicting Corrosion Rates of Common Metals Using Machine Learning on Public Databases  

## Overview
We answer the user’s question about **quantitative interaction effects** between environmental stressors (pH, salinity, temperature) and material properties (composition, crystal structure) on corrosion rates using **only publicly available tabular data** and **CPU‑only compute**. The pipeline creates the core entities defined in **data‑model.md**: a cleaned `CorrosionRecord` collection, a set of engineered `InteractionFeature`s, a `DatasetMetadata` provenance record, and a `ModelArtifact` containing the best‑performing model.

## Dataset Strategy
| Requirement | Availability | Action |
|-------------|--------------|--------|
| Required columns (pH, salinity, temperature, composition, corrosion_rate, source_id) | A version‑controlled CSV `data/raw/sample_corrosion.csv` (≥ 1 000 rows) is stored in the repository and meets all required columns. | Ingestion script loads this file, validates column presence, and proceeds. |
| Optional column (crystal_structure) | May be absent in the supplied CSV. | If missing, a warning is logged and the pipeline continues (FR‑001). |
| Provenance | DOI/URL (if any) and SHA‑256 checksum are recorded in `metadata/dataset.yaml`. | No external download required; the file is version‑controlled. |

*If a future dataset lacks any required column, the pipeline aborts with `Error: MISSING_VARIABLE [column_name] in [dataset_source]` (FR‑001) and the research question must be reformulated.*

## Compute Strategy
- **CPU‑first**: All modeling uses scikit‑learn’s CPU implementation; no GPU libraries are referenced.  
- **Memory Management**: `psutil` monitors RSS; if it exceeds 7 GB, the pipeline automatically draws a stratified sample (random seed 42) preserving the `source_id` distribution (FR‑003).  
- **Runtime Budget**: Estimated total wall‑time ≤ 6 h on GitHub Actions free tier (2 vCPUs, 7 GB RAM).  

## Power Analysis
Using Cohen’s f² = ΔR² / (1 − ΔR²) with a medium effect (ΔR² ≈ 0.10) and α = 0.05, a paired test requires **N ≈ 800** observations for ≥ 80 % power. The supplied dataset has > 1 000 rows, satisfying this requirement. The calculation is performed with `statsmodels.stats.power.FTestPower` and recorded in `report.md`. If a smaller dataset were used, we would explicitly note limited power (SC‑003).

## Statistical Methods & Rigor
| Analysis | Method | Multiple‑Comparison | Power / Sample Size | Causal Claim |
|----------|--------|----------------------|---------------------|--------------|
| Model performance (R², RMSE) | 5‑fold GroupKFold CV; baseline = mean‑only predictor (Phase 5) | N/A | Power analysis above; N > 800 → adequate | Associational (SC‑006) |
| Interaction‑gain significance | **Target‑permutation test**: shuffle the response variable *y* 1 000 times, refit Full and Null models, compute ΔRMSE = RMSE<sub>Null</sub> − RMSE<sub>Full</sub> per permutation; two‑sided p‑value = proportion of |ΔRMSE| ≥ observed. | Same as above | Associational |
| Interaction‑column importance | **Conditional permutation‑importance**: orthogonalize each interaction column against its base features, shuffle the residuals 1 000 times, recompute ΔRMSE; empirical p‑value = proportion of shuffled ΔRMSE ≥ observed (upper‑tail); Benjamini‑Hochberg correction across all interactions (FR‑005, SC‑004) | BH correction applied | Same as above | Associational |
| Collinearity diagnostics | Variance Inflation Factor (VIF) > 5 flagged for base predictors; interaction VIFs reported but excluded from interpretation (FR‑006) | N/A | N/A | N/A |
| Hyper‑parameter stability | Jaccard similarity of top‑5 feature sets across `max_depth` ∈ {3,4,5} (FR‑007) | N/A | N/A | N/A |
| Power analysis | Cohen’s f², α = 0.05, power = 0.8; reported in `report.md` | N/A | Reported | N/A |

All p‑values are two‑sided; significance threshold α = 0.05 (SC‑002). The target‑permutation test correctly isolates the *incremental* contribution of interaction features without conflating the two models’ performance on shuffled targets.

## Reproducibility Measures
- Fixed random seeds (`np.random.seed(42)`, `random_state=42`).  
- Dependencies pinned in `src/requirements.txt`; identical copy placed in `code/requirements.txt`.  
- Data loaded from deterministic path; SHA‑256 checksum verified.  
- All intermediate artifacts hashed; references stored in `metadata/`.  

## Risk & Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Required column missing from supplied CSV | Blocking (cannot satisfy FR‑001) | Pipeline aborts with clear error; reviewer must provide a suitable dataset. |
| Memory overflow > 7 GB | CI timeout/crash | Automated stratified‑sampling fallback (FR‑003). |
| Runtime > 6 h | CI timeout | Permutation counts limited to 1 000; SHAP limited to top‑5 interactions; optional exploratory sweep runs only if time permits. |
| High collinearity among base predictors | Mis‑interpretation of independent effects | VIF check flags VIF > 5; flagged pairs excluded from independent driver claims. |
| Batch leakage between source studies | Inflated interaction importance | GroupKFold ensures no `source_id` appears in both train and test folds. |
| Limited statistical power (if dataset < 800 rows) | False‑negative conclusions | Power analysis disclosed; results interpreted with caution. |
| Potential under‑power due to restrictive hyper‑parameters | Missed interaction effects | Primary model respects FR‑003; an **optional exploratory sweep** with relaxed limits (`max_depth ≤ 6`, `n_estimators ≤ 250`) is performed solely for power diagnostics and is **not** used for final claims. |

## Deliverables
- `data/processed/cleaned_dataset.csv` – validated, imputed, standardized dataset.  
- `data/processed/features.parquet` and `data/processed/feature_names.txt` – engineered feature matrix.  
- `data/results/vif_diagnostics.json` – VIF diagnostics for base predictors.  
- `data/processed/splits.pkl` – serialized GroupKFold split indices.  
- `data/results/best_full_model.joblib`, `data/results/best_null_model.joblib`, `data/results/model_artifact.yaml` – trained models and metadata.  
- `data/results/baseline_performance.json` – baseline mean‑only model metrics (R², RMSE).  
- `data/results/interaction_gain_test.json` – target‑permutation test result (ΔRMSE, p‑value).  
- `data/results/interaction_permutation_importance.json` – raw & BH‑adjusted p‑values for each interaction.  
- SHAP visualisations under `outputs/figures/`.  
- `data/results/sensitivity.json` – hyper‑parameter stability diagnostics (Jaccard scores, VIF with interactions, optional exploratory results).  
- `report.md` – full narrative with metrics, statistical tests, and associational disclaimer.  
- `metadata/dataset.yaml` – provenance (DOI/URL, SHA‑256, column list).  

---



