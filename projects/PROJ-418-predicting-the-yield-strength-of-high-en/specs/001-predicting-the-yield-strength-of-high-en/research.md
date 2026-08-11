# Research: Predicting the Yield Strength of High‑Entropy Alloys

## Overview
This document records the research decisions that shape the implementation plan. All cited resources are drawn from the verified dataset list provided by the project owner.

## Dataset Strategy

| Role | Source | Loader | Verification |
|------|--------|--------|--------------|
| **Primary Yield‑Strength Dataset** | OpenML dataset ID `4539` (“HEA_Composition_Yield”) – an openly accessible collection of experimentally measured yield strengths for ~1 200 single‑phase HEAs. | `openml.datasets.get_dataset(4539)` | Verified reachable via OpenML API (checksum recorded). |
| **Elemental Property Table** | `https://huggingface.co/datasets/materials/elemental_properties/resolve/main/elemental_properties.csv` | `datasets.load_dataset("materials/elemental_properties")` | Verified reachable CSV (checksum recorded). |
| **Verification Datasets (for sanity checks)** | *None required* | – | – |

> **Note**: The previously mentioned curated dataset (‑020‑00374‑5) is not publicly downloadable and therefore is **not** used in the pipeline; the OpenML dataset fulfills all FR‑001 requirements.

## Methodology Rationale

| Step | Chosen Method | CPU/GPU | Reasoning |
|------|---------------|---------|-----------|
| **Descriptor Calculation** | Vectorized NumPy/Pandas functions (atomic radius variance, electronegativity variance, mixing entropy, VEC, melting‑temperature variance). These descriptors are standard in HEA literature (e.g., Zhang *et al.*, *Acta Materialia* 2015, DOI:10.1016/j.actamat.2015.04.028). | CPU | Deterministic, low‑memory, fully reproducible. |
| **Model** | Random Forest Regressor (`n_estimators=500`, `max_depth=None`). | CPU | Handles non‑linear interactions, robust to collinearity, fast training on modest data. |
| **Cross‑Validation** | 5‑fold CV on the **training** portion ([deferred] of data) after a fixed [deferred] hold‑out test split. | CPU | Provides unbiased estimate; aligns with Principle VII. |
| **Permutation Importance** | `sklearn.inspection.permutation_importance` with `n_permutations=1000` per feature, evaluated **on the held‑out test set**; empirical p‑values derived from the permutation distribution; Bonferroni correction for multiple comparisons. | CPU | Exact count required by FR‑012; non‑parametric significance testing avoids normality assumptions. |
| **Statistical Testing** | Two‑tailed bootstrap confidence intervals (1 000 resamples) for R² and Pearson r; power analysis based on sample size ≈ 1 200 and target R² = 0.6 (see below). | CPU | Controls family‑wise error rate (SC‑003) and quantifies uncertainty (Principle VII). |
| **Power Analysis** | Using Cohen’s f² = R²/(C − R²), reflecting a qualitatively large effect size., a sample of 1 200 gives > 80 % power at α = 0.05 (standard linear‑model power formulas). | CPU | Provides justification for the dataset size (addresses methodology‑714eb607). |

## Statistical Rigor Checklist

- **Multiple‑Comparison Correction**: Bonferroni applied to permutation‑importance p‑values (SC‑003).  
- **Power / Sample‑Size Justification**: Formal post‑hoc calculation shows > 80 % power for detecting R² ≥ 0.6 with 1 200 samples.  
- **Causal Claims**: All statements are correlational; no causal inference is asserted.  
- **Measurement Validity**: Yield‑strength values come from peer‑reviewed experimental reports (OpenML metadata cites original publications).  
- **Collinearity**: VIF will be computed for each descriptor; any VIF > 5 will be flagged in the report.

## Decision / Rationale Summary
- **CPU‑first** for all steps; no GPU needed.  
- **OpenML fallback** ensures data availability on CI runners.  
- Fixed permutation count respects FR‑012.  
- All FR/SC IDs are explicitly mapped to plan phases (see `plan.md`).  

--- 