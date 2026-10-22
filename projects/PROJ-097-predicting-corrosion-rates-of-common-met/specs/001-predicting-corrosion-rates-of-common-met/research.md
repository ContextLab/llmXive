# Research: Predicting Corrosion Rates of Common Metals Using Machine Learning on Public Databases

## Overview
This research plan explains how we will answer the user’s question about quantitative interaction effects between environmental stressors (pH, salinity, temperature) and material properties (composition, crystal structure) on corrosion rates, using only publicly available tabular datasets and CPU‑only compute. The pipeline creates the core entities defined in **data-model.md**: a collection of **CorrosionRecord** objects (`cleaned_dataset.csv`), a set of **InteractionFeature** objects (`features.parquet`), a **DatasetMetadata** record (`metadata/dataset.yaml`), and a **ModelArtifact** (`model_artifact.yaml`).

## Dataset Strategy
| Requirement | Availability | Action |
|-------------|--------------|--------|
| Required columns (pH, salinity, temperature, material composition, corrosion rate, source_id) | A minimal CSV file (`data/raw/sample_corrosion.csv`) will be supplied by the verifier. It contains ≥ 1 000 rows and satisfies all required columns. | The ingestion script loads this file, validates column presence, and proceeds. |
| Optional column (crystal structure) | May be absent in the supplied CSV. | If missing, a warning is logged and the pipeline continues. |
| Provenance | The CSV’s DOI/URL (if any) and SHA‑256 checksum are recorded in `metadata/dataset.yaml`. | No external download required; the file is version‑controlled in the repository. |

*If the verifier later provides a dataset that lacks any required column, the pipeline aborts with `Error: MISSING_VARIABLE [column_name] in [dataset_source]` (FR‑001) and the research question must be reformulated.*

## Compute Strategy
- **CPU‑first**: All modeling uses scikit‑learn’s CPU implementation; no GPU libraries are referenced.  
- **Memory Management**: `psutil` monitors RSS; if it exceeds 7 GB, the pipeline automatically samples a stratified subset (random seed 42) preserving the `source_id` distribution (FR‑003).  
- **Runtime Budget**: Estimated total wall‑time ≤ 6 h on GitHub Actions free tier (2 vCPUs, 7 GB RAM).  

## Power Analysis
Using Cohen’s f² = ΔR² / (1 − ΔR²) with a medium effect (ΔR² ≈ 0.10) and α = 0.05, a sample size of **N ≈ 800** yields ≥ 80 % power for a paired test. The supplied dataset has > 1 000 rows, satisfying this requirement. The power calculation is performed with `statsmodels.stats.power.FTestPower` and reported in `report.md`. If a smaller dataset were used, we would explicitly note limited power (SC‑003).

## Statistical Methods & Rigor
| Analysis | Method | Multiple‑Comparison | Power / Sample Size | Causal Claim |
|----------|--------|----------------------|---------------------|--------------|
| Model performance (R², RMSE) | 5‑fold GroupKFold CV; baseline = mean‑only predictor | N/A | Power analysis above; N > 800 → adequate | Associational (SC‑006) |
| Interaction gain | **Paired sign‑flip permutation test**: compute ΔRMSE (Null − Full) per CV fold; randomly **sign‑flip** the Full/Null labels within each fold 1 000 times → null distribution; two‑sided p‑value | N/A (single test) | Same as above | Associational |
| Interaction‑column importance | Permutation‑importance: shuffle each interaction column 200 times, recompute RMSE, derive empirical p‑value; Benjamini‑Hochberg correction (FR‑005, SC‑004) | BH correction applied across all interaction columns | Same as above | Associational |
| Collinearity diagnostics | Variance Inflation Factor (VIF) > 5 flagged for base predictors; interaction VIFs reported but excluded from interpretation (FR‑006) | N/A | N/A | N/A |
| Hyper‑parameter stability | Jaccard similarity of top‑5 feature sets across `max_depth` ∈ {3,4,5} (FR‑007) | N/A | N/A | N/A |
| Power analysis | Cohen’s f², α = 0.05, power = 0.8; reported in `report.md` | N/A | Reported | N/A |

All p‑values are two‑sided; significance threshold α = 0.05 (SC‑002).

## Reproducibility Measures
- Fixed random seeds (`np.random.seed(42)`, `random_state=42`).  
- Dependencies pinned in `requirements.txt`.  
- Data loaded from deterministic path; SHA‑256 checksum verified.  
- All intermediate artifacts hashed; references stored in `metadata/`.  

## Risk & Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Required column missing from supplied CSV | Blocking (cannot satisfy FR‑001) | Pipeline aborts with clear error; reviewer must provide a suitable dataset. |
| Memory overflow > 7 GB | CI timeout/crash | Automated stratified‑sampling fallback (FR‑003). |
| Runtime > 6 h | CI timeout | Permutation counts limited to 1 000 (paired test) and 200 (per‑column importance); SHAP limited to top‑10 interactions. |
| High collinearity among base predictors | Mis‑interpretation of independent effects | VIF check flags VIF > 5; flagged pairs are excluded from independent driver claims. |
| Residual confounding between composition and experimental batch | Inflated interaction importance | StratifiedGroupKFold ensures composition balance across folds. |
| Limited statistical power (if dataset < 800 rows) | False‑negative conclusions | Power analysis disclosed; results interpreted with caution. |

## Deliverables
- `data/processed/cleaned_dataset.csv` (schema validated by `contracts/cleaned_dataset.schema.yaml`).  
- `data/processed/features.parquet` (feature matrix with engineered interactions).  
- `data/results/best_model.joblib` and `data/results/model_artifact.yaml` (validated by `contracts/model_artifact.schema.yaml`).  
- `data/results/vif_report.json` (VIF diagnostics for base predictors).  
- `data/results/interaction_test.json` (paired permutation‑test result and BH‑adjusted interaction importance).  
- Figures (`*.png`) in `outputs/figures/`.  
- `report.md` containing all quantitative results, statistical tests, and an explicit associational disclaimer.  

---


