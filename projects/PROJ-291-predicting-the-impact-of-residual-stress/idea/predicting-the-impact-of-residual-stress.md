---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets  

**Field**: materials science  

## Research question  

To what extent does residual stress mediate the relationship between manufacturing process parameters and fatigue life across different material classes, and how much predictive value does stress‑mediated estimation add beyond direct process‑to‑fatigue modeling?  

## Motivation  

Residual stresses introduced during manufacturing (e.g., welding, additive printing, machining) are known to shorten component fatigue life, yet measuring or simulating these stresses is costly. Publicly available materials datasets contain process parameters, material properties, and fatigue test results, offering a chance to quantify the *mediating* role of residual stress and to assess whether explicitly modelling this mediator improves fatigue‑life predictions for diverse alloys.  

## Related work  

- [Microstructure sensitive fatigue life prediction model for SLM fabricated Hastelloy‑X (2022)](https://arxiv.org/abs/2211.08305) — Demonstrates a physics‑informed machine‑learning pipeline that predicts fatigue life from detailed microstructural descriptors, illustrating how domain‑specific features can boost fatigue‑life forecasts.  
- [Machine Learning and Data Analytics for Design and Manufacturing of High‑Entropy Materials Exhibiting Mechanical or Fatigue Properties of Interest (2020)](https://arxiv.org/abs/2012.07583) — Reviews ML techniques applied to predict mechanical and fatigue properties of complex alloys, providing methodological precedent for data‑driven fatigue‑life modeling across material classes.  

## Expected results  

- Quantify the mediation effect of residual stress (e.g., via Sobel or bootstrap mediation analysis) and show that it accounts for a statistically significant portion of the variance in fatigue life beyond direct process‑parameter effects.  
- Models that include residual‑stress features will achieve ≥10 % lower mean absolute percentage error (MAPE) on held‑out test data compared with models that use only process parameters.  
- Cross‑material evaluation will reveal that the mediation strength differs between steels and aluminum alloys, informing material‑specific design guidelines.  

## Methodology sketch  

- **Dataset acquisition**  
  - Download public fatigue datasets from the NIST Materials Data Repository, the UCI Machine Learning Repository (e.g., “Fatigue‑Life” collection), and OpenML (search term “fatigue”).  
  - Record exact URLs/DOIs for reproducibility.  

- **Data preprocessing**  
  - Parse CSV/JSON files; retain columns for material composition, key process parameters (e.g., welding heat input, cooling rate, machining feed), measured residual‑stress values (when reported) and fatigue life (cycles to failure).  
  - Perform missing‑value imputation (median for numeric fields) and unit standardisation.  

- **Residual‑stress handling**  
  - Where residual‑stress measurements are present, use them directly (independent experimental observation).  
  - If absent, compute an *estimated* residual‑stress proxy using published empirical correlations (e.g., σ_res ≈ k·heat_input·cooling_rate) and treat this proxy as an additional feature while explicitly flagging its derived nature in the analysis.  

- **Feature engineering**  
  - Assemble three feature sets: (A) process parameters only, (B) process + estimated/measured residual stress, (C) full set including material‑property descriptors (yield strength, hardness).  
  - Standardise each feature to zero mean and unit variance.  

- **Model training**  
  - Fit baseline regressors (Random Forest, Gradient Boosting) using scikit‑learn and a shallow feed‑forward neural network (PyTorch, one hidden layer, ≤500 epochs, early stopping).  
  - All training runs on CPU; limit hyper‑parameter grid to ≤10 combinations to stay within GHA compute limits.  

- **Cross‑validation & test split**  
  - Stratify by material class; reserve 20 % of samples as a held‑out test set.  
  - Perform 5‑fold cross‑validation within the training set for model selection.  

- **Mediation analysis**  
  - Apply bootstrap mediation (10 000 resamples) to estimate the indirect effect of process parameters on fatigue life via residual stress.  
  - Report proportion mediated and 95 % confidence intervals.  

- **Statistical evaluation**  
  - Compute MAPE, R², and 95 % CI (bootstrapped) on the test set for each feature set.  
  - Compare models (B) vs (A) with paired t‑tests on absolute errors to assess added predictive value of stress‑mediated features.  

- **Cross‑material generalization**  
  - Train on one material class (e.g., steels) and test on another (e.g., aluminum alloys); quantify performance drop and test significance with paired t‑tests.  

- **Reproducibility**  
  - Publish all scripts, environment file (`requirements.txt`), and a `README` with exact dataset download commands.  
  - Fix random seeds for data splits, model initialization, and bootstrap resampling.  

## Duplicate-check  

- Reviewed existing ideas: *None provided in input*.  
- Closest match: No comparable idea found in the provided corpus.  
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-25T05:45:13Z
**Outcome**: exhausted
**Original term**: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets materials science
**Verified citation count**: 3

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets materials science | 0 |
| 1 | machine learning models for fatigue life prediction from residual stress data | 5 |
| 2 | data‑driven fatigue crack growth modeling using open material databases | 0 |
| 3 | statistical analysis of internal stress effects on high‑cycle fatigue | 0 |
| 4 | AI‑based estimation of fatigue limit incorporating pre‑stress measurements | 0 |
| 5 | open repository of residual stress and fatigue performance datasets | 0 |
| 6 | physics‑informed neural networks for stress‑induced fatigue degradation | 0 |
| 7 | X‑ray diffraction residual stress inputs for fatigue life forecasting | 0 |
| 8 | Bayesian inference of fatigue life under residual stress fields | 0 |
| 9 | deep learning of S‑N curves from publicly available material datasets | 0 |
| 10 | multiscale modeling of fatigue damage with measured stress fields | 0 |
| 11 | additive manufacturing residual stress impact on low‑cycle fatigue | 0 |
| 12 | data mining of public fatigue test archives for stress‑life correlations | 0 |
| 13 | stress intensity factor prediction for fatigue using machine‑learned models | 0 |
| 14 | fatigue life assessment with hole‑drilling residual stress data | 0 |
| 15 | open‑source fatigue data platforms for predictive analytics | 0 |
| 16 | transfer learning for fatigue life prediction across material systems | 0 |
| 17 | ensemble methods for residual stress‑fatigue relationship discovery | 0 |
| 18 | probabilistic fatigue life estimation from shared stress datasets | 0 |
| 19 | machine‑learning‑augmented Paris law parameters derived from public data | 0 |
| 20 | comparative study of residual stress measurement techniques for fatigue modeling | 0 |

### Verified citations

1. **Microstructure sensitive fatigue life prediction model for SLM fabricated Hastelloy-X** (2022). Chandrashekhar M. Pilgar, Ana Fernandez, Javier Segurado. arXiv. [2211.08305](https://arxiv.org/abs/2211.08305). PDF-sampled: No.
2. **An investigation of fatigue damage growth in composites materials using the vibration response phase decay** (2024). Matias Lasen, Dario Di Maio, Damaso De Bono, Michelle Peluzzo. arXiv. [2404.14834](https://arxiv.org/abs/2404.14834). PDF-sampled: No.
3. **Machine Learning and Data Analytics for Design and Manufacturing of High-Entropy Materials Exhibiting Mechanical or Fatigue Properties of Interest** (2020). Baldur Steingrimsson, Xuesong Fan, Anand Kulkarni, Michael C. Gao, Peter K. Liaw. arXiv. [2012.07583](https://arxiv.org/abs/2012.07583). PDF-sampled: No.
