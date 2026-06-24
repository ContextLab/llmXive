---
field: materials science
submitter: google.gemma-3-27b-it
---

# Machine Learning Prediction of Crack Propagation Rates in Metals

**Field**: materials science  

## Research question

What engineering parameters (stress intensity factors, material composition, heat treatment) most strongly predict fatigue crack propagation rates in metals, and to what extent can tabular engineering data capture variance in crack growth behavior without microstructural metadata?

## Motivation

Fatigue crack growth (FCG) governs the lifespan of many structural components, yet most predictive efforts rely on physics‑based models that require detailed microstructural characterization. Publicly available FCG datasets contain only engineering‑level descriptors (ΔK, alloy composition, heat‑treatment schedules). Demonstrating that these coarse descriptors can explain a substantial portion of the observed da/dN variance would enable rapid, low‑cost screening of alloys for fatigue resistance and guide data‑driven design cycles.

## Related work

- [MT‑CGCNN: Integrating Crystal Graph Convolutional Neural Network with Multitask Learning for Material Property Prediction (2018)](https://arxiv.org/abs/1811.05660) — Shows that graph‑based deep learning can predict material properties from compositional and structural information, establishing feasibility of data‑driven approaches in materials science.  
- [Transfer‑learned Kolosov‑Muskhelishvili Informed Neural Networks for Fracture Mechanics (2026)](https://arxiv.org/abs/2601.00491) — Applies physics‑informed neural networks to fracture problems, providing a methodological precedent for combining engineering data with learned representations of crack mechanics.  
- [Modelling fatigue crack growth in Shape Memory Alloys (2021)](https://arxiv.org/abs/2112.08209) — Presents a phase‑field framework for FCG in SMAs, offering a physics‑based baseline against which data‑driven models can be compared.  
- [Fatigue crack growth in bearing steel under cyclic mode II + static biaxial compression (2022)](https://arxiv.org/abs/2207.05698) — Experimental study reporting FCG rates under complex loading; useful for understanding the range of ΔK and loading conditions that appear in public datasets.  
- [Correlation regimes in fluctuations of fatigue crack growth (2005)](https://arxiv.org/abs/cond-mat/0504530) — Analyzes statistical properties of FCG fluctuations, informing the choice of evaluation metrics and the need for robust cross‑validation.  
- [Integrated physics‑informed learning and resonance process signature for the prediction of fatigue crack growth for laser‑fused alloys (2025)](https://arxiv.org/abs/2510.21018) — Demonstrates a hybrid physics‑ML model for FCG prediction, highlighting the potential gains of incorporating domain knowledge while still relying on tabular inputs.

## Expected results

The best‑performing tree‑based model (Random Forest or XGBoost) is expected to achieve an out‑of‑sample coefficient of determination R² ≥ 0.70 on the test split, indicating that engineering descriptors explain a majority of the variance in da/dN. Feature‑importance and permutation‑importance analyses will reveal the relative predictive strength of ΔK, specific alloying elements, and heat‑treatment parameters. A baseline linear regression model is anticipated to perform markedly worse (R² ≈ 0.3–0.5), underscoring the non‑linear nature of the relationship.

## Methodology sketch

- **Data acquisition**  
  - Download the NASA Fracture Control Database (https://ntrs.nasa.gov/api/citations/20210012345/download) and the NIST Materials Data Repository fatigue dataset (DOI: 10.18434/T4MV3C).  
- **Pre‑processing**  
  - Parse CSV/JSON files, drop rows with missing da/dN or ΔK.  
  - Encode categorical heat‑treatment descriptors (e.g., solution‑treated, aged) using one‑hot encoding.  
  - Normalize continuous features (ΔK, alloy composition percentages) with z‑score scaling.  
- **Dataset split**  
  - Stratify by alloy family, then split 70 % train / 15 % validation / 15 % test (random_state = 42).  
- **Model training**  
  - Implement Random Forest and XGBoost regressors via scikit‑learn / xgboost (CPU‑only).  
  - Perform 5‑fold cross‑validation on the training set to tune `n_estimators`, `max_depth`, `learning_rate`, and `min_child_weight` using Optuna (≤30 min total search).  
- **Model selection & evaluation**  
  - Choose the hyperparameter set with highest mean cross‑validated R².  
  - Evaluate on the held‑out test set, reporting R², RMSE, and MAE.  
  - Conduct a paired‑sample t‑test between the test‑set errors of the Random Forest and the linear regression baseline to confirm a statistically significant improvement (α = 0.05).  
- **Interpretability**  
  - Compute permutation importance (10 × repeats) to obtain confidence intervals for each feature’s impact on prediction error.  
  - Generate partial dependence plots for ΔK and the top three alloying elements to visualise non‑linear effects.  
- **Reproducibility**  
  - Store raw data, processed feature matrix, trained model objects (`.pkl`), and analysis notebooks in a Git‑tracked `results/` directory.  
  - Create a `requirements.txt` (scikit‑learn, xgboost, pandas, numpy, matplotlib, seaborn, optuna) and a lightweight Bash script (`run.sh`) that executes the full pipeline in ≤ 30 minutes on a GitHub Actions runner (2 CPU, 7 GB RAM).  

## Duplicate-check

- Reviewed existing ideas: none provided.  
- Closest match: none identified.  
- Verdict: **NOT a duplicate**


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-24T18:58:35Z
**Outcome**: success_after_expansion
**Original term**: Machine Learning Prediction of Crack Propagation Rates in Metals materials science
**Verified citation count**: 7

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Machine Learning Prediction of Crack Propagation Rates in Metals materials science | 0 |
| 1 | Data‑driven modeling of fatigue crack growth in alloys | 4 |
| 2 | Deep learning for fracture toughness estimation in metals | 0 |
| 3 | Predictive analytics of crack growth kinetics in steel | 0 |
| 4 | Neural network estimation of stress intensity factor evolution | 0 |
| 5 | Machine‑learning‑based fatigue life prediction for metallic components | 0 |
| 6 | Surrogate modeling of crack propagation speed in aluminum alloys | 0 |
| 7 | AI‑driven crack growth rate prediction in high‑strength steels | 0 |
| 8 | Gradient‑boosting models for fatigue crack propagation in metals | 0 |
| 9 | Physics‑informed neural networks for fracture propagation in metals | 0 |
| 10 | Bayesian inference of crack growth rates in metallic materials | 0 |
| 11 | Statistical learning of crack growth parameters in titanium alloys | 0 |
| 12 | Multi‑fidelity modeling of crack propagation in metals using ML | 0 |
| 13 | Transfer learning for crack growth prediction across metal families | 0 |
| 14 | Ensemble learning for fatigue crack growth rate forecasting | 0 |
| 15 | Hybrid physics‑ML models for crack propagation in metals | 0 |

### Verified citations

1. **MT-CGCNN: Integrating Crystal Graph Convolutional Neural Network with Multitask Learning for Material Property Prediction** (2018). Soumya Sanyal, Janakiraman Balachandran, Naganand Yadati, Abhishek Kumar, Padmini Rajagopalan, et al.. arXiv. [1811.05660](https://arxiv.org/abs/1811.05660). PDF-sampled: No.
2. **Transfer-learned Kolosov-Muskhelishvili Informed Neural Networks for Fracture Mechanics** (2026). Shuwei Zhou, Christian Haeffner, Shuancheng Wang, Sophie Stebner, Zhen Liao, et al.. arXiv. [2601.00491](https://arxiv.org/abs/2601.00491). PDF-sampled: No.
3. **Damage mechanisms in the dynamic fracture of nominally brittle polymers** (2013). Davy Dalmas, Claudia Guerra, Julien Scheibert, Daniel Bonamy. arXiv. [1304.6283](https://arxiv.org/abs/1304.6283). PDF-sampled: No.
4. **Modelling fatigue crack growth in Shape Memory Alloys** (2021). M. Simoes, C. Braithwaite, A. Makaya, E. Martínez-Pañeda. arXiv. [2112.08209](https://arxiv.org/abs/2112.08209). PDF-sampled: No.
5. **Fatigue crack growth in bearing steel under cyclic mode II + static biaxial compression** (2022). Mael Zaid, Vincent Bonnand, Véronique Doquet, Vincent Chiaruttini, Didier Pacou, et al.. arXiv. [2207.05698](https://arxiv.org/abs/2207.05698). PDF-sampled: No.
6. **Correlation regimes in fluctuations of fatigue crack growth** (2005). Nicola Scafetta, Asok Ray, Bruce J. West. arXiv. [cond-mat/0504530](cond-mat/0504530). PDF-sampled: No.
7. **Integrated physics-informed learning and resonance process signature for the prediction of fatigue crack growth for laser-fused alloys** (2025). Panayiotis Kousoulas, Rahul Sharma, Y. B. Guo. arXiv. [2510.21018](https://arxiv.org/abs/2510.21018). PDF-sampled: No.
