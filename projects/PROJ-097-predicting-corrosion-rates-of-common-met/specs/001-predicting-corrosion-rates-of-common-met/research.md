# Research: Predicting Corrosion Rates of Common Metals Using Machine Learning on Public Databases

## Overview
This research plan outlines how we will answer the user’s question about quantitative interaction effects between environmental stressors (pH, salinity, temperature) and material properties (composition, crystal structure) on corrosion rates, using only publicly available tabular datasets and CPU‑only compute.

## Dataset Strategy
| Requirement | Availability | Action |
|-------------|--------------|--------|
| Required columns (pH, salinity, temperature, material composition, corrosion rate) | **No verified open dataset currently provides all five columns** (the "# Verified datasets" block is empty). | The pipeline will abort with a clear `Error: MISSING_VARIABLE [column_name] in [dataset_source]` (FR‑001). The project scope must be revisited to either (a) relax the predictor set to match an available dataset, or (b) locate a suitable open dataset before proceeding. No synthetic or gated data will be fabricated. |
| Optional column (crystal structure) | May be absent | Log as limitation; continue if other required columns are present. |
| Provenance | Required | Record DOI/URL and SHA‑256 checksum in `metadata/dataset.yaml`. |

*Decision*: Until a suitable dataset is identified, the pipeline halts early with a missing‑variable error, and the research question will be reformulated accordingly.

## Compute Strategy
- **CPU‑first**: All modeling uses scikit‑learn’s CPU implementation. No GPU libraries are referenced.  
- **Memory Management**: `psutil` monitors RSS; if > 7 GB, the pipeline triggers the stratified‑sampling fallback described in FR‑003 (random seed 42, of rows preserving group distribution).
- **Runtime Budget**: Estimated total wall‑time ≤ 6 h on GitHub Actions free tier (2 vCPUs, 7 GB RAM).  

## Power Analysis
Using Cohen’s f² = ΔR² / (1‑ΔR²) and conventional effect‑size thresholds (small = 0.02, medium = 0.15, large = 0.35), a sample size of **N ≈ 800** provides ≥ 80 % power to detect a medium interaction effect (ΔR² ≈ 0.10) at α = 0.05. If the available dataset contains fewer than 800 rows, we will explicitly state that the study is under‑powered to detect modest interaction effects and interpret results cautiously. The power calculation is performed a priori and reported in `report.md`.

## Statistical Methods & Rigor
| Analysis | Method | Multiple‑Comparison | Power / Sample Size | Causal Claim |
|----------|--------|----------------------|---------------------|--------------|
| Model performance (RMSE, R²) | 5‑fold GroupKFold CV, R² as primary metric | N/A | Power analysis above; if N < 800, note limited power (SC‑003). | Associational (SC‑006) |
| Interaction gain | Hierarchical target‑permutation test (200 permutations) comparing Full vs Null RMSE; statistic = ΔR² | N/A (single hierarchical test) | Same power note as above. | Associational |
| Feature‑importance p‑values | Permutation‑importance per interaction column (200 shuffles each) → empirical p‑values; Benjamini‑Hochberg correction (FR‑005, SC‑004) | BH correction applied | Same as above. | Associational |
| Collinearity diagnostics | Variance Inflation Factor (VIF) > 5 flagged for base predictors **and** for interaction terms (diagnostic only) (FR‑006) | N/A | N/A | N/A |
| Hyper‑parameter stability | Jaccard similarity of top‑5 feature sets across `max_depth` values (FR‑007) | N/A | N/A | N/A |
| Power analysis | Cohen’s f², α = 0.05, power = 0.8; calculates minimum detectable ΔR² for given N | N/A | Reported in `report.md`; if N insufficient, limitation noted. | N/A |

All p‑values are two‑sided; significance threshold α = 0.05 (SC‑002).

## Reproducibility Measures
- Fixed random seeds (`np.random.seed(42)`, `random_state=42`).  
- Dependencies pinned in `requirements.txt`.  
- Data download via deterministic URLs; SHA‑256 checksum verification.  
- All intermediate artifacts version‑hashed; references stored in `metadata/`.  

## Risk & Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open dataset with required variables | Blocking (cannot answer FR‑001) | Early dataset scoping; if unavailable, adjust research question or drop interaction analysis. |
| Memory overflow > 7 GB | Pipeline crash | Automated stratified sampling fallback (FR‑003). |
| Runtime > 6 h | CI timeout | Reduced permutation count to 200 (empirically fits within budget) and SHAP limited to top‑10 interactions; profiling‑guided limits. |
| High collinearity among predictors | Mis‑interpretation of independent effects | VIF check (Phase 0) flags VIF > 5; interaction VIFs reported as diagnostics only; no claim of independence for flagged pairs. |
| Residual confounding between composition and experimental batches | Inflated interaction importance | Composition‑balanced stratified GroupKFold (Phase 2) ensures each fold contains a representative mix of material types. |
| Limited statistical power | False‑negative conclusions | Power analysis (above) disclosed; limitations noted in report. |

## Deliverables
- `cleaned_dataset.csv` + `metadata/dataset.yaml` (provenance).  
- Trained `model_artifact.yaml` (best Full model).  
- Figures: SHAP summary, interaction dependence plots, partial‑dependence curves.  
- `report.md` containing performance metrics, hierarchical permutation‑test results, BH‑corrected p‑values, stability analysis, and explicit associational disclaimer (SC‑006).  

---



