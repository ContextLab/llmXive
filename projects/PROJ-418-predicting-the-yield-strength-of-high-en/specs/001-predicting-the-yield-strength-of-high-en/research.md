# Research: Predicting the Yield Strength of High‑Entropy Alloys

## Dataset Strategy

| Need | Candidate | Availability | Action |
|------|-----------|--------------|--------|
| Curated experimental HEA yield‑strength dataset (‑020‑00374‑5) | DOI ‑020‑00374‑5 (internal repository) | **Not publicly downloadable** (no verified URL) | Attempt download; if HTTP 404 or authentication required, abort with clear error and request user‑provided CSV. |
| Elemental property reference table | `elemental_properties.csv` (included in repo) | Open, version‑controlled | Use directly for descriptor calculations. |

> **Note:** No verified open dataset containing experimental HEA yield strength exists. The plan therefore treats the curated dataset as a *user‑supplied* asset. If the asset cannot be supplied, the pipeline will terminate early (FR‑001) and report the data gap.

## Methodology Decisions & Rationale

| Decision | Rationale | Compute Mode |
|----------|-----------|--------------|
| **Random Forest Regressor** (scikit‑learn) | Non‑parametric, robust to multicollinearity among compositional descriptors; fast CPU training; easy to extract permutation importance. | CPU‑first (fits comfortably on GitHub Actions runner). |
| **5‑fold Cross‑Validation** | Provides unbiased out‑of‑fold performance estimate; aligns with Principle VII (statistical rigor). | CPU‑first. |
| **Bootstrap CI (1 000 resamples)** | Generates confidence intervals for R² and r without analytic assumptions; complies with Principle VII. | CPU‑first (vectorized). |
| **Permutation Importance – 1 000 permutations** | Fixed count mandated by FR‑012; enables robust importance distributions for t‑tests. | CPU‑first; parallelized across features via `joblib`. |
| **Multiple‑Comparison Correction** | Permutation importance yields a p‑value per feature; we apply Benjamini‑Hochberg FDR (α = 0.05) to control false discoveries. | CPU‑first (simple sorting). |
| **Power / Sample‑Size Justification** | Dataset size is unknown until user supplies the CSV. The plan will report the actual N and note that power may be limited for small N (< 30). | N/A – descriptive. |
| **Causal Claims** | The study is purely observational; all claims are associative. | N/A. |
| **Collinearity Handling** | Descriptors are known to be correlated (e.g., δ and Δχ). We will report variance inflation factors (VIF) and avoid interpreting individual coefficients; importance is reported instead. | CPU‑first. |

## Statistical Rigor Checklist

- **Multiple‑comparison correction** – Benjamini‑Hochberg on permutation‑importance p‑values.  
- **Sample‑size / power** – Report N, compute Cohen’s f² for R²; flag if N < 50 as low power.  
- **Causal‑inference** – Explicitly label results as *associational*.  
- **Measurement validity** – Dataset documentation (curated experimental measurements) will be cited; if missing, the plan records the limitation.  
- **Collinearity** – Compute VIF for each descriptor; if VIF > 5, note high collinearity in report.  

## Compute Feasibility Statement

All steps are implementable on the free GitHub Actions runner (multiple CPU cores, sufficient RAM). No GPU‑only libraries are required. The only potential bottleneck is the permutation‑importance loop; we parallelize across 2 cores and limit memory by streaming descriptors from parquet.

If runtime exceeds the 2 h budget, the pipeline will automatically down‑scale `n_estimators` (from 500 to 300) and re‑measure; this adaptation is *allowed* because it does not violate any FR (the model architecture remains Random Forest).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Curated dataset not accessible | Fatal (FR‑001) | Abort early with informative error; request user‑provided CSV. |
| High descriptor collinearity → unstable importance | May affect SC‑006 | Compute VIF; report stability; if VIF > 10, combine correlated descriptors. |
| Runtime > 2 h | Violates SC‑004 | Parallelize permutation importance; fallback to fewer trees; early‑stop and report violation. |
| Missing element fields in user CSV | FR‑009 violation | Schema validation will catch and abort with clear message. |

---
