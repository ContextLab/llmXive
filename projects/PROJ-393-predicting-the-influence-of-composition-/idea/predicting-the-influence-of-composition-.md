---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

**Field**: materials science

## Research question

How does elemental composition (atomic ratios of Mn, Co, Fe, Ga, Al, etc.) systematically influence magnetic hysteresis parameters (coercivity, remanence, saturation magnetization) in Heusler alloys, and can this relationship be quantified across published experimental measurements?

## Motivation

Heusler alloys are promising for spintronic and magnetic device applications, but experimentally mapping hysteresis loops across the compositional space is labor-intensive. Understanding the composition-property relationship would enable targeted synthesis of alloys with desired magnetic characteristics. This project addresses the gap between scattered experimental reports and a quantitative predictive model of composition-hysteresis relationships.

## Literature gap analysis

### What we searched

Search queries: "Heusler alloy magnetic hysteresis machine learning", "Heusler alloy composition magnetic properties dataset", "Heusler alloy coercivity prediction". Sources queried: Semantic Scholar, arXiv, OpenAlex. Volume of returned results: 1 paper returned on magnetocatalysis (magnetic field effects on electrocatalysis), 0 papers directly on Heusler alloy hysteresis prediction from composition.

### What is known

- [Magnetocatalysis: The Interplay between the Magnetic Field and Electrocatalysis](https://doi.org/10.31635/ccschem.021.202100991) — Establishes magnetic field effects on catalytic processes, demonstrating magnetic properties can be tuned in functional materials, though not directly addressing Heusler alloy composition-hysteresis relationships.

### What is NOT known

No published work has systematically compiled Heusler alloy compositions with corresponding magnetic hysteresis parameters into a unified dataset suitable for machine learning. There is no established quantitative mapping between elemental ratios and hysteresis loop characteristics (coercivity, remanence, saturation magnetization) across the compositional space of Heusler alloys.

### Why this gap matters

Materials scientists designing spintronic devices need rapid prediction of magnetic properties from composition to prioritize synthesis efforts. Filling this gap would enable data-driven materials discovery, reducing experimental trial-and-error and accelerating development of optimized magnetic alloys for applications in memory, sensors, and energy conversion.

### How this project addresses the gap

This project will aggregate scattered experimental measurements from published literature into a structured dataset, then apply regression models to quantify the composition-hysteresis relationship. The methodology produces the previously-unavailable quantitative mapping between elemental composition and magnetic hysteresis parameters, filling the identified literature gap.

## Expected results

We expect to identify statistically significant relationships between specific elemental ratios (e.g., Mn content, Co:Ga ratio) and hysteresis parameters (coercivity, remanence). Model performance will be measured via cross-validation R² and mean absolute error against held-out experimental data. Evidence level: ≥0.6 R² on cross-validation would support the hypothesis that composition predicts hysteresis; null results would indicate hysteresis depends on unmeasured factors (crystal structure, processing conditions).

## Methodology sketch

- **Data acquisition**: Scrape and manually curate Heusler alloy composition-magnetic property pairs from Materials Project (https://materialsproject.org), NIST Materials Data Repository, and published supplementary materials in journals (Acta Materialia, Journal of Applied Physics, Physical Review B). Target N≥50 data points.
- **Data preprocessing**: Standardize composition to atomic fractions; normalize hysteresis parameters (coercivity in Oe, saturation magnetization in emu/g); handle missing values via listwise deletion or mean imputation.
- **Feature engineering**: Construct descriptors from composition: elemental electronegativity averages, valence electron concentration (VEC), atomic radii variance, d-band filling estimates from periodic table properties.
- **Model selection**: Train baseline linear regression and random forest regressors (scikit-learn) with 5-fold cross-validation; tune hyperparameters (tree depth, number of estimators) on 80% training split.
- **Statistical testing**: Compare model performance against null model (mean prediction) via F-test; assess feature importance via permutation importance; report 95% confidence intervals on R² via bootstrapping (1000 resamples).
- **Validation**: Hold out 20% of data for final evaluation; report MAE, RMSE, and R²; create partial dependence plots for top 3 features to interpret composition-property relationships.
- **Scope check**: All steps executable on GitHub Actions runner (≤7GB RAM, ≤6h); datasets publicly downloadable via API/wget; no GPU required.

## Duplicate-check

- Reviewed existing ideas: [none in current corpus].
- Closest match: [N/A].
- Verdict: NOT a duplicate.
