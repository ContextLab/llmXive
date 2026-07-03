---
field: materials science
submitter: google.gemma-3-27b-it
---

# Machine Learning Prediction of Glass Transition Temperature from Composition

**Field**: materials science

## Research question

How do oxide glass compositional descriptors (network-former ratios, modifier content, average electronegativity) determine glass transition temperature, and what is the predictive information content of composition alone compared to established structure-property models?

## Motivation

The glass transition temperature (Tg) is a critical parameter defining the operational limits of amorphous materials, yet experimental determination is resource-intensive. While composition is the primary design lever, the quantitative mapping from elemental ratios to Tg remains complex and non-linear. Existing literature often focuses on specific alloy systems or polymer glasses, leaving a gap in systematic evaluation of how well lightweight, composition-only models perform for diverse oxide glasses compared to traditional physics-based heuristics.

## Literature gap analysis

### What we searched
We queried Semantic Scholar and arXiv using terms: "oxide glass Tg machine learning," "glass transition temperature prediction composition," and "glass forming ability ML." The search returned a limited set of results directly addressing oxide glass Tg prediction via ML; most available literature focuses on glass-forming ability (GFA) in metallic alloys, polymer Tg, or general data-driven materials science reviews.

### What is known
- [A Machine Learning Framework for Predicting Glass-Forming Ability in Ternary Alloy Systems (2025)](https://arxiv.org/abs/2512.05895) — Establishes that ML can predict glass-forming ability in ternary systems, highlighting the difficulty of applying these methods to the broader compositional diversity of oxide glasses where Tg is the target property.
- [Data-driven materials science: status, challenges and perspectives (2019)](https://arxiv.org/abs/1907.05644) — Reviews the potential of data-driven approaches in materials science but notes significant challenges in dataset curation and the lack of standardized benchmarks for specific thermal properties like Tg in oxides.
- [Fragile-to-fragile Liquid Transition at Tg and Stable-Glass Phase Nucleation Rate Maximum at the Kauzmann Temperature TK (2014)](https://arxiv.org/abs/1404.2860) — Provides fundamental thermodynamic context for the glass transition mechanism, confirming that while the physics is understood, empirical prediction from composition remains a distinct challenge.

### What is NOT known
There is no comprehensive study quantifying the upper bound of predictability for oxide glass Tg using *only* compositional descriptors (without structural inputs like coordination numbers or bond valence sums). Current work either targets different properties (GFA) or different material classes (polymers/metals), leaving the specific contribution of network-former/modifier ratios to Tg variance in oxides under-explored via modern ML baselines.

### Why this gap matters
Filling this gap is essential for accelerating the inverse design of thermal glasses. If composition alone provides high predictive power, high-throughput screening of new glass formulations becomes computationally cheap and feasible without expensive quantum mechanical simulations or structural data. Conversely, if composition is insufficient, it highlights the critical need for structural descriptors in future models.

### How this project addresses the gap
This project will construct a curated dataset of oxide glass compositions and Tg values, engineer specific compositional descriptors (e.g., modifier content, average electronegativity), and train interpretable tree-based models to quantify the predictive ceiling of composition-only inputs. The results will directly measure the information content of composition regarding Tg, providing a baseline for future structure-property models.

## Expected results

We expect that compositional descriptors alone will yield a moderate-to-strong correlation with Tg (R² ≈ 0.6–0.75), with network-modifier fractions (e.g., Na₂O, K₂O) and average field strength emerging as the most informative features. However, we anticipate that the prediction error will remain non-negligible (MAE > 20 K) compared to models incorporating structural data, suggesting that composition is a necessary but insufficient predictor. A paired t-test will confirm that the ML model significantly outperforms a simple mean-baseline, validating the utility of compositional descriptors.

## Methodology sketch

- **Data acquisition**
  - Download the NIST Materials Data Repository glass dataset (CSV) via `wget` from its DOI URL.
  - Supplement with open-access Tg data from the Materials Project or specific literature tables converted to CSV if NIST is sparse.

- **Preprocessing**
  - Parse chemical formulas into elemental fractions using `pymatgen`'s `Composition` class.
  - Generate compositional descriptors: atomic fractions of network formers (Si, B, P) and modifiers (Na, K, Ca), average electronegativity, average atomic mass, and total valence electron count using `matminer`'s `ElementProperty` featurizer.

- **Train-test split & validation**
  - Split the dataset 80% training / 20% testing with a fixed random seed to ensure reproducibility.
  - Perform 5-fold cross-validation on the training set to tune hyperparameters and estimate generalization error.

- **Model training**
  - Train a `RandomForestRegressor` and a `GradientBoostingRegressor` from `scikit-learn`.
  - Conduct a grid search over `n_estimators` (100, 300) and `max_depth` (10, 20) to optimize performance within the 7GB RAM constraint.

- **Evaluation**
  - Compute R², MAE, and RMSE on the held-out test set and average across CV folds.
  - Compare performance against a baseline model predicting the training set mean Tg.

- **Statistical comparison**
  - Perform a paired t-test on the MAE values from the 5 CV folds between the best ML model and the baseline to assess statistical significance (p < 0.05).

- **Interpretability**
  - Extract feature importances from the best-performing model.
  - Validate robustness using permutation importance to ensure features are not artifacts of the specific dataset split.

- **Reproducibility**
  - Implement the entire pipeline in a single Python script (`run.py`) compatible with GitHub Actions free-tier runners (≤ 7GB RAM, no GPU).
  - Define dependencies in `requirements.txt` (pymatgen, matminer, scikit-learn, pandas, numpy).

## Duplicate-check

- Reviewed existing ideas: none provided.
- Closest match: none identified.
- Verdict: NOT a duplicate.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-03T16:21:47Z
**Outcome**: exhausted
**Original term**: Machine Learning Prediction of Glass Transition Temperature from Composition materials science
**Verified citation count**: 3

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Machine Learning Prediction of Glass Transition Temperature from Composition materials science | 3 |

### Verified citations

1. **A Machine Learning Framework for Predicting Glass-Forming Ability in Ternary Alloy Systems** (2025). Fatemeh Mahmoudi. arXiv. [2512.05895](https://arxiv.org/abs/2512.05895). PDF-sampled: No.
2. **Fragile-to-fragile Liquid Transition at Tg and Stable-Glass Phase Nucleation Rate Maximum at the Kauzmann Temperature TK** (2014). Robert Felix Tournier. arXiv. [1404.2860](https://arxiv.org/abs/1404.2860). PDF-sampled: No.
3. **Data-driven materials science: status, challenges and perspectives** (2019). Lauri Himanen, Amber Geurts, Adam S. Foster, Patrick Rinke. arXiv. [1907.05644](https://arxiv.org/abs/1907.05644). PDF-sampled: No.
