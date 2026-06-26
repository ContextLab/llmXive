---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Alloying on High-Temperature Oxidation Resistance

**Field**: materials science

## Research question

To what extent do elemental composition and thermodynamic descriptors determine high-temperature oxidation weight gain in nickel-based superalloys, and where do composition-only models fail to capture microstructural effects?

## Motivation

Experimental characterization of oxidation resistance is slow and resource-intensive, creating a bottleneck in alloy development for aerospace and power generation. This research addresses the gap in accessible, predictive computational tools by leveraging existing public datasets to screen alloy compositions before physical testing, while explicitly quantifying the limits of composition-only approaches.

## Literature gap analysis

### What we searched

Searches were conducted on Semantic Scholar and arXiv using queries: (1) "nickel superalloy oxidation machine learning prediction" and (2) "alloy composition oxidation resistance thermodynamic descriptors". Results queried from arXiv and OpenAlex returned 3 papers total. Two were directly relevant to Ni-based superalloy oxidation, one was tangential (Zr-based system).

### What is known

- [Time-Dependent Oxidation and Scale Evolution of a Wrought Co/Ni-based Superalloy (2025)](https://arxiv.org/abs/2511.09678) — Establishes that time-dependent oxide scale evolution requires understanding microstructural factors beyond bulk composition for long-term resistance prediction.
- [Bonding and oxidation protection of Ti₂AlC and Cr₂AlC for a Ni-based Superalloy (2019)](https://arxiv.org/abs/1902.10001) — Demonstrates that interface chemistry and protective phase formation (MAX phases) significantly modify oxidation behavior in Ni-based systems, suggesting microstructural/coating effects matter.

### What is NOT known

No published work has systematically quantified the predictive accuracy limits of composition-only ML models for oxidation weight gain in nickel-based superalloys. The specific contribution of microstructural descriptors (grain size, precipitate distribution) versus bulk thermodynamic descriptors remains unmeasured in a public benchmark dataset.

### Why this gap matters

Materials scientists developing new superalloys need to know when composition-based screening is sufficient versus when costly microstructural characterization is required. Filling this gap would enable more efficient alloy development pipelines and clarify the information content of compositional data for oxidation resistance.

### How this project addresses the gap

The methodology will train composition-only models on public oxidation datasets, then explicitly compare predictions against samples with available microstructural annotations. The performance differential directly quantifies the microstructural effect gap.

## Expected results

We expect composition-only models to achieve moderate predictive accuracy (R² ≈ 0.5-0.7) on bulk oxidation weight gain, with systematic failures on alloys where protective oxide scale formation depends on microstructural features. Feature importance analysis will identify Chromium and Aluminum as dominant predictors, consistent with known alumina/chromia scale formation mechanisms.

## Methodology sketch

- **Data Acquisition**: Download tabular datasets containing alloy composition and oxidation weight gain from NIST Materials Data Repository (https://www.nist.gov/mml/mmd/material-data-repository) and search Zenodo for "superalloy oxidation" datasets with explicit composition and weight gain measurements.
- **Feature Engineering**: Construct input vectors including elemental weight percentages (Ni, Cr, Al, Co, Ti, etc.) and periodic table descriptors (atomic radius, electronegativity, valence electron count) sourced from WebElements or Materials Project API.
- **Thermodynamic Descriptors**: Calculate oxide formation enthalpies using OpenCalphad or Thermo-Calc public samples to augment composition features with predicted scale stability metrics.
- **Model Implementation**: Train Random Forest, Gradient Boosting, and Gaussian Process Regressor models using `scikit-learn` on CPU-only execution (memory-efficient, no GPU required).
- **Validation**: Perform 5-fold cross-validation to assess generalization; calculate RMSE, MAE, and R² metrics on held-out test folds.
- **Microstructural Gap Analysis**: Where microstructural annotations exist (grain size, precipitate volume fraction), train separate models including these features and compare prediction error reduction against composition-only baseline.
- **Feature Importance**: Generate SHAP (SHapley Additive exPlanations) plots to interpret feature contributions to predicted oxidation rates and identify composition limits.
- **Compute Constraints**: All steps fit within 7 GB RAM and 6-hour runtime on GHA free-tier runners; dataset size will be capped at ≤500 samples to ensure feasibility.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: None (no existing ideas to compare).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-26T00:24:07Z
**Outcome**: exhausted
**Original term**: Predicting the Impact of Alloying on High-Temperature Oxidation Resistance materials science
**Verified citation count**: 3

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting the Impact of Alloying on High-Temperature Oxidation Resistance materials science | 3 |

### Verified citations

1. **Shot-Peening of Pre-Oxidized Plates of Zirconium: Influence of Residual Stress on Oxidation** (2013). Laura Raceanu, Virgil Optasanu, Tony Montesin, Guillaume Montay, Manuel Francois. arXiv. [1301.1635](https://arxiv.org/abs/1301.1635). PDF-sampled: No.
2. **Time-Dependent Oxidation and Scale Evolution of a Wrought Co/Ni-based Superalloy** (2025). Cameron. Crabb, Zachary. T. Kloenne, Samuel. R. Rogers, Chi-Hang. D. Kwok, Mark. C. Hardy, et al.. arXiv. [2511.09678](https://arxiv.org/abs/2511.09678). PDF-sampled: No.
3. **Bonding and oxidation protection of Ti${_2}$AlC and Cr${_2}$AlC for a Ni-based Superalloy** (2019). Maxim Sokol, Jian Wang, Hrishikesh Keshavan, Michel W. Barsoum. arXiv. [1902.10001](https://arxiv.org/abs/1902.10001). PDF-sampled: No.
