# Research: Predicting Corrosion Potential from Composition and Environment

## Executive Summary
The goal is to evaluate whether alloy composition and aqueous testing conditions can predict corrosion potential (mV vs SHE) using publicly available data. The primary data source specified in the spec—**NIST‑IR‑8200**—has **no verified programmatic download URL**, making it inaccessible to an unattended CI runner. Consequently, the pipeline is designed to **detect this failure early**, report the exact record count, and halt with a `SchemaMismatchError`. No synthetic data will be fabricated, respecting the spec’s prohibition on fabricated observations.

If a future open‑access dataset meeting the required joint distribution becomes available, the same pipeline can be re‑run without code changes.

## Dataset Strategy

| Dataset | Availability | Reason for Use / Fallback |
|---------|--------------|---------------------------|
| **NIST‑IR‑8200** | *No verified source* (see “Verified Datasets” block) | Primary target per spec. Attempted via standard HTTP GET; if unavailable, pipeline aborts. |
| **Materials Project API** | Verified open API: https://materialsproject.org/open | Used to augment alloy composition when available (FR‑019). |
| **Simulation Mode** | *Only if both real sources fail* | Allowed only as a **last‑resort diagnostic**; results are labeled “simulation” and not used for scientific conclusions. |

### Pivot Strategy & Failure Protocol
1. **Attempt download** of NIST‑IR‑8200 via `datasets.load_dataset(..., streaming=True)`.  
2. **If HTTP 429** or any network error occurs, apply **exponential backoff** (FR‑015) with up to 3 retries, base delay = 5 s, max delay = 60 s, and log each attempt.  
3. **If download succeeds but < 500 records** or < 10 distinct alloy designations, raise `SchemaMismatchError` (FR‑014, FR‑017).  
4. **If download fails entirely** (no verified URL), log “No verified source for NIST‑IR‑8200” and halt.  
5. **Only** after both steps 2‑4 fail, optionally run a **physics‑informed synthetic generator** (clearly labeled “Simulation Mode”) to produce a dummy dataset for debugging; **no scientific claims** are drawn from it.

## Data Quality & Preprocessing Plan
- **Missing critical env variables** (pH, temperature) → **exclude** from primary regression (FR‑013) and log in `extreme_conditions.csv`.  
- **Out‑of‑range pH** (< 0 or > 14) → flag as outlier, exclude, add to separate diagnostic report (FR‑016).  
- **Composition handling**: Raw weight fractions are CLR‑transformed (FR‑020) to address the unit‑sum constraint.  
- **Encoding**: pH and temperature remain numeric; electrolyte type is one‑hot encoded.  
- **Group Split**: “Leave‑One‑Specific‑Alloy‑Out” with environment‑balancing (stratify by pH/temperature bins) to prevent alloy‑environment confounding (addresses methodology‑0d5d2d9c). Minimum 10 alloy designations required; otherwise abort (FR‑012, FR‑017).  
- **Schema validation** ensures non‑null composition, pH, temperature, corrosion potential (FR‑011) and records count ≥ 500 (SC‑006).

## Methodological Rigor
1. **Model Selection** – Random Forest & Gradient Boosting (CPU‑only, scikit‑learn).  
2. **Validation** – Group split with environment balancing prevents alloy‑level leakage (Principle VII).  
3. **Metrics** – R² and RMSE on held‑out test set; null baseline (mean prediction).  
4. **Learnability Classification** – Relationship deemed learnable if **R² > 0.05** with a permutation‑test p < 0.05 (Bonferroni‑corrected across the two models) **and** the bootstrapped 95 % CI for RMSE does **not** overlap the ASTM G‑series tolerance of 150 mV. This replaces the earlier arbitrary RMSE cutoff (addressing scientific_soundness‑86a97fe8).  
5. **Feature Importance** – Conditional Permutation Importance (CPI) is used to respect CLR‑induced feature correlations (addressing scientific_soundness‑0cb4417e). Significance is assessed with 1,000 permutations and Bonferroni/FDR correction (FR‑008).  
6. **Partial Dependence** – Replaced with Accumulated Local Effects (ALE) plots for compositional features, which are robust to the sum‑zero constraint (addressing scientific_soundness‑9de34d4e).  
7. **Statistical Limitations** – Observational data → only **associational** statements; compositional collinearity mitigated via CLR; power limited if dataset < 500 records (pipeline halts).  

## Decision Rationale
| Decision | Rationale |
|----------|-----------|
| **CPU‑first execution** | RF & GB on ≤ 10k rows run comfortably on the free‑tier GitHub Actions runner; GPU not needed. |
| **Hard halt on < 500 records / < 10 alloys** | Guarantees statistical validity and respects FR‑014, FR‑017. |
| **No synthetic fallback for primary analysis** | Spec explicitly forbids synthetic data; synthetic mode only for debugging, not for scientific claims. |
| **Group split with environment balancing** | Prevents data leakage and alloy‑environment confounding (Methodology‑0d5d2d9c). |
| **CLR transformation** | Addresses compositional closure, ensuring meaningful CPI scores. |
| **Permutation‑test learnability** | Provides a statistically grounded p‑value; combined with RMSE CI gives a robust decision rule (Scientific‑Soundness‑86a97fe8). |
| **CPI over vanilla permutation** | Accounts for feature dependence introduced by CLR (Scientific‑Soundness‑0cb4417e). |
| **ALE over PDP** | Avoids misleading marginal effects for compositional data (Scientific‑Soundness‑9de34d4e). |

---

