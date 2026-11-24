# Research: Predicting Yield Strength of BCC Alloys

## Overview
The study quantifies how compositional descriptors and ILR‑transformed composition vectors predict the yield strength of body‑centered cubic (BCC) alloys. It follows a strict reproducibility regime, uses only publicly accessible data, and applies rigorous statistical validation.

## Dataset Strategy

| Dataset | Verified URL | Status | Notes |
|---------|--------------|--------|-------|
| **MPEA Database** | DOI: 10.1038/s41597-020-00768-9 (canonical source identifier required by FR‑001; resolved programmatically at runtime) | **Canonical source; runtime availability check** | Required by FR‑001. The pipeline resolves the DOI to a direct download link at runtime and validates required columns after download. If the file cannot be programmatically downloaded (paywall, credentials), the script halts with `DATA_UNAVAILABLE`. No alternative dataset provides the necessary composition + yield‑strength + BCC label; no substitute is fabricated. |
| **BCC (parquet) – HuggingFace** | <https://huggingface.co/datasets/bccnf/MeLiDC-shuffled-completo/resolve/main/data/test-00000-of-00001.parquet> | *Unsuitable* | Contains text data, not alloy compositions or yield strength. Not used. |
| **FCC (gzip) – HuggingFace** | <https://huggingface.co/datasets/slnader/fcc-comments/resolve/main/attachments.tar.gz> | *Unsuitable* | Not BCC, no yield strength. Not used. |
| **HCP (parquet) – HuggingFace** | <https://huggingface.co/datasets/7eu7d7/HCP-Diffusion-datas/resolve/main/Lexica.art.parquet> | *Unsuitable* | Wrong crystal system. Not used. |

**Decision/Rationale**  
The MPEA database (DOI 10.1038/s41597-020-00768-9) is the only source satisfying the variable requirements (elemental composition, yield strength, crystal structure). It is cited by its canonical DOI — the identifier mandated by the spec — and treated as a *runtime* data-availability check rather than a pre-verified direct URL. If unavailable, the project halts gracefully, preserving scientific integrity. Compute feasibility is CPU-first: all methods (scikit-learn regressors, classical statistics) run faithfully on the 2-core CI runner; no GPU escape hatch is needed.

### Dataset‑Variable Fit
Required columns:
- `elemental_composition` (atomic % per element)  
- `yield_strength` (MPa)  
- `crystal_structure` (must equal `"BCC"`)

The MPEA database is documented in the literature to contain these fields; the pipeline validates their presence after download. If a required variable is absent from the downloaded data, the pipeline halts with `DATA_UNAVAILABLE` rather than proceeding on a mismatched dataset.

## Statistical Rigor

| Aspect | Method | Specification |
|--------|--------|---------------|
| **Cross‑validation** | Repeated 5‑Fold CV | `n_folds=5`, `n_repeats=10`, `random_state=42` (FR‑005) |
| **Bootstrap CI** | Percentile method, 1000 resamples of hold‑out predictions (FR‑006) |
| **Multiple‑Comparison Correction** | Bonferroni correction applied to the three pairwise model‑R² comparisons (RF vs GB, RF vs Ridge, GB vs Ridge) |
| **Power & Sample‑size** | Minimum N = 80 enforced by FR‑004; if N < 80, pipeline halts with `DATA_SCARCITY`. Honest a priori power analysis on the independent sample size (see plan.md "Statistical Power & Sample-Size Justification"): with N = 80 and ~10–30 predictors, power ≈ 0.80 only for large effects (Cohen's f² ≈ 0.35); power for medium effects (f² ≈ 0.15) is limited (~0.35–0.50). This limitation is explicitly reported in the results. |
| **Causal Claim Scope** | Observational study; all statements limited to *associational* relationships. Feature importance is reported for predictive insight only (SC‑001). |
| **Measurement Validity** | Yield strength values are taken directly from the source; the pipeline checks that a `yield_definition` field exists and contains a non‑empty string. If missing, it halts with `YIELD_DEFINITION_INVALID`. |
| **Collinearity Mitigation** | ILR transformation addresses compositional closure; L1/RFE feature selection removes redundant scalar/ILR features (FR‑003.1). Correlation matrix is logged for reference. |
| **Confounding Variables** | Testing temperature, strain‑rate, and processing history materially affect yield strength. If the source dataset includes these columns, the pipeline (a) filters to entries measured under standard conditions and logs exclusions, and (b) records the fraction of entries carrying testing-condition metadata in `reports/results.json`. Missing metadata is logged (`CONFOUNDING_METADATA_MISSING`) and reported as a construct-validity limitation of the target variable; it does not cause a halt. |

## Descriptor Construct Validity (independent literature)

The scalar descriptors are physically motivated heuristics validated in independent peer-reviewed HEA literature, distinct from the MPEA yield-strength source:

- **δ (atomic radius mismatch)** — lattice distortion / solid-solution strengthening in BCC refractory HEAs (Senkov et al., refractory HEA strengthening studies; Zhang et al., Adv. Eng. Mater. 10 (2008) δ-based solid-solution formation rules).
- **VEC** — electronic-structure/phase-stability correlation (Guo et al., VEC-based FCC/BCC phase prediction).
- **ΔS_mix, ΔH_mix** — configurational disorder and thermodynamic interaction (Zhang et al. 2008; George et al., Nat. Rev. Mater. HEA reviews).
- **Δχ (electronegativity difference)** — chemical/charge-transfer mismatch (Zhang et al. 2008 Δχ rule).

These are associational predictors, not validated causal mechanisms; the study frames all findings accordingly.

## Compute Feasibility

- **CPU‑First**: All models (`RandomForestRegressor`, `GradientBoostingRegressor`, `Ridge`) are from `scikit-learn` and run efficiently on 2 CPU cores. Expected runtime < 4 h for ≤ 10 k rows.
- **Memory**: Feature matrix size ≤ 10 k × (~30) ≈ 3 MB; well within the 7 GB RAM limit.
- **No GPU**: No deep‑learning components; GPU escape hatch is unnecessary.

## Data Availability Plan

1. **Resolve DOI**: `download.py` uses `requests` to resolve the DOI `10.1038/s41597-020-00768-9` to a direct download link. If a link is found, the file is streamed to `data/raw/mpea.csv`.  
2. **Checksum**: SHA‑256 of the downloaded file is stored in `state/projects/PROJ-525...yaml`.  
3. **Verification**: After download, the script checks that required columns exist and that `crystal_structure` entries are present.  
4. **Scarcity Check**: If < 80 BCC rows remain after filtering, the pipeline aborts with the mandated message.  
5. **Streaming (fallback)**: If the raw file exceeds 7 GB, the loader will stream it row-by-row (though the MPEA size is far smaller).  
6. **No Synthetic Data**: In any failure scenario (unavailable DOI, missing columns, insufficient rows) the pipeline halts; it never fabricates or substitutes another dataset.

## Contingency Plan

| Failure Mode | Detection | Action |
|--------------|-----------|--------|
| DOI resolution returns non‑200 or redirects to a paywall | HTTP status ≠ 200 or missing `Content-Disposition` header | Log `DATA_UNAVAILABLE: MPEA requires access credentials`; exit code 1. |
| Yield‑definition field absent or non‑standard | After parsing, `yield_definition` column missing or empty | Log `YIELD_DEFINITION_INVALID: Source data lacks standard yield strength definition`; exit code 1. |
| Post‑filter count < 80 | Count computed after Phase 1 | Log `DATA_SCARCITY: Insufficient BCC alloys (N < 80)`; exit code 1. |
| Feature selection removes all ILR or all scalar descriptors | After L1/RFE step | Log `COMPLEMENTARITY_FAILURE: Feature selection removed all ILR or all Scalar features`; exit code 1. |
| Confounding metadata missing when required | Detection of non‑standard testing conditions | Log `CONFOUNDING_METADATA_MISSING`; continue with available data and report the limitation in `reports/results.json` (no halt). |

All failure messages are written to `stderr` as required by the spec.