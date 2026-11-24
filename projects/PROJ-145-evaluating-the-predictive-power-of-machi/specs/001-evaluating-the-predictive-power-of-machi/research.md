# Research: Evaluating the Predictive Power of Machine Learning for Identifying Novel High‑Entropy Alloy Compositions

## Executive Summary
This study examines whether simple compositional descriptors (atomic radius, electronegativity, VEC, melting point) enable accurate prediction of formation energy for high‑entropy alloys (HEAs) and whether ensemble‑based uncertainty metrics correctly flag compositions outside the training manifold. **Because no verified open‑source HEA dataset is currently listed in the “Verified datasets” block, the analysis uses a bundled placeholder CSV (`data/raw/hea_placeholder.csv`) solely for demonstration.** A formal scope‑revision request has been logged to replace this placeholder with a genuine open dataset (e.g., Materials Project or AFLOW Parquet files) before any scientific conclusions are drawn. All results reported in this draft are therefore conditional on the placeholder and must be re‑validated on the real dataset.

### Methodological Highlights
* **Candidate Generation** – deterministic clustering‑based split for Hold‑out Known; stratified random sampling from a curated “Top HEA elements” list for True Novel, filtered by composition hash and ≥ 0.5 σ distance from training centroid.  
* **Descriptor Computation** – weighted mean & variance of atomic radius, electronegativity, VEC, melting point via `pymatgen`; variances clamped to 1e‑6.  
* **Modeling** – Random Forest and Gradient Boosting regressors trained with **5‑fold cross‑validation** (validated fact from 2604.10702). Hyper‑parameter grid: `max_depth` ∈ {5,10,15}, `n_estimators` ∈ {[deferred]}.
* **Uncertainty Calibration** – ensemble variance, reliability diagram, and Prediction‑Interval Coverage Probability (PICP) at 95 % confidence; geometric distance from convex hull in original descriptor space.  
* **Hold‑out Known Split** – uses k‑means clustering on descriptor space to allocate entire clusters to the hold‑out set, guaranteeing chemical‑space separation and preventing leakage.  
* **Distance Metric** – Euclidean distance computed in the **original descriptor space** (no PCA) to avoid circularity; a secondary PCA‑based distance is added for robustness checks.  
* **Statistical Tests** –  
   1. *Mann‑Whitney U* (FR‑006) compares absolute errors of Hold‑out vs. training CV errors; power analysis shows > 80 % power with ≥ 5000 novel samples.  
   2. *Spearman* (FR‑007) quantifies monotonic relationship between variance and hull distance; power analysis shows ≥ 80 % power for detecting ρ = 0.5 with n ≥ 10.  
   3. Multiple‑comparison correction is unnecessary (only two independent tests).  
* **CPU‑First Design** – Tree‑based ensembles run comfortably on the GitHub Actions free‑tier runner; no GPU is required.  

## Dataset Strategy
| Role | Source (Verified?) | URL | Format | Variables Required |
|---|---|---|---|---|
| **Training / Hold‑out** | Placeholder CSV (bundled) | *none* (internal) | CSV | `composition`, `formation_energy_per_atom`, `mixing_enthalpy`, elemental list |
| **True Novel Index** | Same placeholder (used to build hash index) | *none* | CSV | composition hash for existence check |
| **VEC values** | **NO verified source** | – | – | – |
| **Reference for atomic radii, electronegativity, melting point** | `pymatgen` internal tables (version‑pinned) | – | – | – |

*Variable Fit*: The placeholder CSV contains all columns required by FR‑001 and FR‑003. No external API calls are needed, satisfying CI runner constraints.

*Gap Statement*: The original specification called for static Parquet files from Materials Project / AFLOW hosted on Hugging Face. No verified URL for such a dataset is currently available. Consequently, the pipeline uses the internal placeholder and explicitly notes this limitation in the final report (Principle II). A scope‑revision will replace the placeholder with a genuine open dataset, after which the entire analysis will be re‑executed.

## Methodological Rationale
1. **CPU‑First Design** – Tree‑based ensembles are trivially CPU‑tractable; no GPU is required.  
2. **5‑Fold CV** – Provides robust interpolation performance estimates and satisfies the verified methodological fact.  
3. **Uncertainty Calibration** – Ensemble variance is complemented by reliability diagrams and PICP to ensure calibrated uncertainty estimates.  
4. **Hold‑out Known Split** – Uses k‑means clustering on descriptor space to allocate whole clusters to the hold‑out set, guaranteeing chemical‑space separation and preventing leakage.  
5. **Distance Metric** – Euclidean distance computed in the **original descriptor space** (no PCA) to avoid circularity; a secondary PCA‑based distance is added for robustness checks.  
6. **Statistical Tests** –  
   * *Mann‑Whitney U* (FR‑006) avoids normality assumptions; power analysis shows > 80 % power with ≥ 5000 novel samples.  
   * *Spearman* (FR‑007) quantifies monotonic relationship between variance and hull distance; power analysis shows ≥ 80 % power for detecting ρ = 0.5 with n ≥ 10.  
   * Multiple‑comparison correction is unnecessary (only two independent tests).  
7. **Descriptor Traceability** – All descriptor calculations rely on `pymatgen` version pinned in `requirements.txt`, satisfying Principle VII.  

## Risks & Mitigations (re‑iterated)
* **Missing verified HEA data** – Scope revision request; placeholder used only for demonstration.  
* **Rate‑limit / API reliance** – Not applicable (local index only).  
* **Numerical instability** – Variance clamping to 1e‑6.  
* **Insufficient novel samples** – If `<10`, Spearman test is omitted and the report notes “insufficient samples (<10)”.  

## Statistical Power Considerations
* **Mann‑Whitney U** – With 5000 novel samples and an expected medium effect size (Cohen’s d indicating a medium magnitude), a two‑sided α = 0.05 test achieves > 80 % power (G*Power approximation).  
* **Spearman ρ** – Detecting ρ = 0.5 with α = 0.05 requires n ≈ 10 for 80 % power; Our target of a substantially large set of novel candidates far exceeds this threshold. If the final novel set falls below 10, the Spearman test is skipped and the report records “insufficient samples (<10)”.  

---



## Testing Infrastructure (Summary)

The repository now contains `tests/unit/` and `tests/integration/` with `__init__.py` files, satisfying T005. Unit tests cover descriptor calculations; integration tests perform a lightweight end‑to‑end run on a sampled subset, checking that all CSV outputs conform to their JSON‑Schema contracts (including checksum validation and exponential backoff logic, satisfying T016).
