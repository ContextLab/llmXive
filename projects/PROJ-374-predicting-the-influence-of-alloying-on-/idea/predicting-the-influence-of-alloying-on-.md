---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Influence of Alloying on the Seebeck Coefficient Using Public Data

**Field**: materials science

## Research question

How do specific compositional features in thermoelectric alloys (e.g., elemental electronegativity differences, atomic radius variance, and valence electron concentration) systematically correlate with Seebeck coefficient magnitude across publicly available materials datasets?

## Motivation

Thermoelectric materials enable waste-heat recovery and solid-state cooling, but experimental screening of alloy compositions is slow and costly. While computational databases exist, the compositional rules governing Seebeck coefficient variation remain poorly quantified. Establishing these relationships would accelerate materials design by identifying promising alloying strategies before synthesis.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and OpenAlex using the following search terms: "Seebeck coefficient prediction alloy composition", "thermoelectric materials machine learning dataset", and "electronic transport properties materials database". The search returned a single on-topic result from a comprehensive ab initio database, with no additional studies specifically addressing compositional feature–Seebeck coefficient relationships in alloy systems.

### What is known

- [An ab initio electronic transport database for inorganic materials (2017)](https://doi.org/10.1038/sdata.2017.85) — This work establishes a foundational database of calculated electronic transport properties (including Seebeck coefficient) for inorganic materials, but does not analyze compositional feature correlations across alloy series.

### What is NOT known

No published work has systematically quantified which compositional descriptors (electronegativity variance, atomic radius distribution, valence electron concentration) most strongly predict Seebeck coefficient magnitude in thermoelectric alloys. The existing database provides the raw properties but does not perform the feature importance analysis needed to guide alloy design decisions.

### Why this gap matters

Materials scientists designing thermoelectric alloys lack evidence-based guidance on which elemental substitutions will increase Seebeck coefficient. Filling this gap would enable faster screening of candidate compositions, reducing experimental iteration cycles and accelerating deployment of waste-heat recovery technologies.

### How this project addresses the gap

This project will download the electronic transport database, extract alloy composition data and Seebeck coefficients, engineer compositional descriptors, and apply gradient boosting to identify the most predictive features. The resulting feature importance rankings directly address the unknown compositional rules.

## Expected results

We expect to identify 2–3 compositional descriptors that explain >50% of Seebeck coefficient variance across the dataset (e.g., electronegativity difference or valence electron concentration). A hold-out test set R² ≥ 0.4 would confirm predictive utility; failure to exceed R² = 0.2 would suggest compositional descriptors alone are insufficient and other factors (crystal structure, defects) dominate.

## Methodology sketch

- Download the electronic transport database from https://doi.org/10.1038/sdata.2017.85 (JSON/CSV format, ~10–50 MB)
- Filter records to thermoelectric-relevant alloys (e.g., bismuth telluride, lead telluride, skutterudite families)
- Extract elemental composition and Seebeck coefficient values; exclude entries with missing data
- Engineer compositional features: mean atomic radius, electronegativity variance, valence electron concentration, atomic number variance
- Split data into 80/20 train/test sets stratified by material family
- Train gradient boosting regressor (scikit-learn, ≤100 trees) on training set; tune via 5-fold cross-validation
- Evaluate test set R² and mean absolute error; compare against linear regression baseline
- Extract feature importance scores and plot top 5 descriptors vs. Seebeck coefficient
- Generate figures showing composition–property relationships; document in README

## Duplicate-check

- Reviewed existing ideas: None found in current project corpus.
- Closest match: None.
- Verdict: NOT a duplicate
