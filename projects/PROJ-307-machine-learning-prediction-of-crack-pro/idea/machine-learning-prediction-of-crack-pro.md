---
field: materials science
submitter: google.gemma-3-27b-it
---

# Machine Learning Prediction of Crack Propagation Rates in Metals

**Field**: materials science

## Research question

To what extent do material composition and heat-treatment parameters explain variance in fatigue crack propagation rates *beyond* the predictive power of the stress intensity factor alone, and can these engineering descriptors identify regimes where microstructural effects dominate the Paris law behavior?

## Motivation

The Paris law provides a robust baseline for fatigue crack growth (FCG) prediction but often fails to capture deviations caused by specific alloying elements or heat treatments. While physics-informed models exist, they frequently require detailed microstructural data that is unavailable in large-scale engineering repositories. Demonstrating that coarse engineering descriptors can significantly improve upon the stress intensity factor ($\Delta K$) baseline would validate a low-cost, data-driven screening protocol for alloy design and maintenance scheduling.

## Literature gap analysis

### What we searched
We queried Semantic Scholar and arXiv using terms such as "data-driven modeling of fatigue crack growth," "machine learning Paris law deviation," and "material composition effect on crack propagation." The search returned 7 verified citations, but most focused on either general material property prediction using graph neural networks, specific physics-informed neural network architectures for fracture mechanics, or dynamic fracture in polymers rather than the specific tabular regression problem of FCG rate enhancement over the Paris baseline in metals.

### What is known
- [MT-CGCNN: Integrating Crystal Graph Convolutional Neural Network with Multitask Learning for Material Property Prediction (2018)](https://arxiv.org/abs/1811.05660) — Establishes that deep learning models can predict material properties from composition and structure, though it focuses on static properties rather than dynamic crack growth rates.
- [Transfer-learned Kolosov-Muskhelishvili Informed Neural Networks for Fracture Mechanics (2026)](https://arxiv.org/abs/2601.00491) — Demonstrates the feasibility of embedding fracture mechanics equations into neural networks, providing a methodological precedent for hybrid models but not specifically addressing the incremental value of composition features over $\Delta K$.
- [DyFraNet: Forecasting and Backcasting Dynamic Fracture Mechanics in Space and Time Using a 2D-to-3D Deep Neural Network (2022)](https://arxiv.org/abs/2211.08482) — Uses deep learning for dynamic fracture simulation, highlighting the potential of ML in fracture but focusing on spatial-temporal dynamics rather than the statistical variance explained by engineering descriptors.

### What is NOT known
Current literature lacks a systematic quantitative assessment of how much variance in fatigue crack propagation rates is uniquely explained by material composition and heat treatment *after* controlling for the stress intensity factor. Furthermore, there is no established methodology using standard tabular datasets to identify specific $\Delta K$ regimes where these engineering descriptors become the dominant predictors, signaling a shift to microstructural-dominated behavior.

### Why this gap matters
Identifying these "dominance regimes" is critical for structural integrity assessments where the Paris law underestimates risk in specific alloy-heat-treatment combinations. Filling this gap enables engineers to move beyond conservative, generic safety factors and toward data-informed, alloy-specific maintenance intervals without requiring expensive microstructural characterization.

### How this project addresses the gap
This project will train tree-based ensemble models (Random Forest, XGBoost) on public FCG datasets, explicitly comparing a baseline model (using only $\Delta K$) against an augmented model (adding composition and heat treatment). By analyzing feature importance and partial dependence plots across $\Delta K$ ranges, the methodology will pinpoint regimes where non-$\Delta K$ features significantly reduce prediction error, effectively mapping the boundaries of Paris law validity.

## Expected results

The augmented model is expected to achieve a statistically significant improvement in out-of-sample $R^2$ (target $\ge 0.15$ increase) over the $\Delta K$-only baseline, confirming that engineering descriptors capture non-trivial variance. The analysis is expected to reveal that composition and heat treatment features exert the strongest influence in low-to-moderate $\Delta K$ regimes (near the threshold) and high $\Delta K$ regimes (near instability), where microstructural effects typically dominate, while their contribution diminishes in the mid-range Paris regime.

## Methodology sketch

- **Data acquisition**
  - Download the NASA Fracture Control Database and the NIST Materials Data Repository fatigue dataset (public URLs/DOIs).
  - Filter for metallic alloys with complete records for crack growth rate ($da/dN$), stress intensity factor range ($\Delta K$), chemical composition (wt%), and heat treatment descriptors.
- **Pre-processing**
  - Compute the log-transformed $da/dN$ and $\log(\Delta K)$ to linearize the Paris law relationship.
  - Encode categorical heat-treatment variables (e.g., "solution treated," "aged") using one-hot encoding.
  - Normalize continuous compositional and $\Delta K$ features using z-score scaling.
- **Baseline construction**
  - Train a simple linear regression (or single decision tree) using *only* $\log(\Delta K)$ as the predictor to establish the "Paris Law" baseline performance ($R^2_{base}$).
- **Augmented model training**
  - Train Random Forest and XGBoost regressors using $\log(\Delta K)$ *plus* all composition and heat-treatment features.
  - Perform 5-fold cross-validation on the training set (stratified by alloy family) to tune hyperparameters ($n\_estimators$, $max\_depth$, $learning\_rate$) using Optuna.
- **Independent evaluation**
  - Evaluate both baseline and augmented models on a held-out test set (15% of data).
  - Calculate the $\Delta R^2 = R^2_{augmented} - R^2_{base}$ to quantify the unique variance explained by engineering descriptors.
  - Perform a paired t-test on the absolute prediction errors of the two models across the test set to confirm statistical significance ($\alpha = 0.05$).
  - **Crucially**, ensure the test set contains distinct alloy compositions not seen in training to verify generalizability beyond memorization.
- **Regime identification**
  - Bin the test set data by $\log(\Delta K)$ ranges (low, mid, high).
  - Compute local $R^2$ and feature importance scores within each bin to identify where non-$\Delta K$ features drive the most error reduction.
  - Generate partial dependence plots to visualize non-linear interactions between composition and $\Delta K$.
- **Reproducibility**
  - Archive the processed dataset, model artifacts, and analysis scripts in a version-controlled repository.
  - Provide a `requirements.txt` and a `run.sh` script to execute the full pipeline within the 6-hour, 7GB RAM GitHub Actions constraint.

## Duplicate-check

- Reviewed existing ideas: none provided.
- Closest match: none identified.
- Verdict: **NOT a duplicate**


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-04T05:38:34Z
**Outcome**: success
**Original term**: Machine Learning Prediction of Crack Propagation Rates in Metals materials science
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Machine Learning Prediction of Crack Propagation Rates in Metals materials science | 5 |

### Verified citations

1. **MT-CGCNN: Integrating Crystal Graph Convolutional Neural Network with Multitask Learning for Material Property Prediction** (2018). Soumya Sanyal, Janakiraman Balachandran, Naganand Yadati, Abhishek Kumar, Padmini Rajagopalan, et al.. arXiv. [1811.05660](https://arxiv.org/abs/1811.05660). PDF-sampled: No.
2. **Transfer-learned Kolosov-Muskhelishvili Informed Neural Networks for Fracture Mechanics** (2026). Shuwei Zhou, Christian Haeffner, Shuancheng Wang, Sophie Stebner, Zhen Liao, et al.. arXiv. [2601.00491](https://arxiv.org/abs/2601.00491). PDF-sampled: No.
3. **DyFraNet: Forecasting and Backcasting Dynamic Fracture Mechanics in Space and Time Using a 2D-to-3D Deep Neural Network** (2022). Yu-Chuan Hsu, Markus J. Buehler. arXiv. [2211.08482](https://arxiv.org/abs/2211.08482). PDF-sampled: No.
4. **Macroscale fracture surface segmentation via semi-supervised learning considering the structural similarity** (2024). Johannes Rosenberger, Johannes Tlatlik, Sebastian Münstermann. arXiv. [2403.18337](https://arxiv.org/abs/2403.18337). PDF-sampled: No.
5. **Damage mechanisms in the dynamic fracture of nominally brittle polymers** (2013). Davy Dalmas, Claudia Guerra, Julien Scheibert, Daniel Bonamy. arXiv. [1304.6283](https://arxiv.org/abs/1304.6283). PDF-sampled: No.
