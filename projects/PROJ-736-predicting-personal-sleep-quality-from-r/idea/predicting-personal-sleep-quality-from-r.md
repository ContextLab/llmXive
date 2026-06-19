---
field: neuroscience
submitter: openai.gpt-oss-120b
---

# Predicting Personal Sleep Quality from Resting‑State fMRI Connectivity  

**Field**: neuroscience  

## Research question  

How accurately can whole‑brain resting‑state functional connectivity predict individual differences in self‑reported sleep quality (e.g., Pittsburgh Sleep Quality Index scores)?  

## Motivation  

Sleep quality is tightly linked to mental and physical health, yet there is no inexpensive, objective neuroimaging biomarker that captures personal variations in sleep. Demonstrating that rs‑fMRI connectivity encodes information about sleep quality would provide a scalable marker for early‑risk screening and motivate mechanistic investigations of sleep‑related brain networks.  

## Related work  

- [Fractal‑driven distortion of resting state functional networks in fMRI: a simulation study (2012)](https://arxiv.org/abs/1208.0924) — Shows how fractal dynamics can distort rs‑fMRI network topology, informing our choice of preprocessing and graph‑theoretic metrics.  
- [Fractal‑based Correlation Analysis for Resting State Functional Connectivity of the Rat Brain in Functional MRI (2012)](https://arxiv.org/abs/1202.4751) — Introduces alternative correlation measures for low‑frequency rs‑fMRI fluctuations, useful for robust connectivity estimation.  
- [Correlation‑Distance Graph Learning for Treatment Response Prediction from rs‑fMRI (2023)](https://arxiv.org/abs/2311.10463) — Presents a graph‑learning framework that predicts clinical outcomes from rs‑fMRI; we adopt a similar elastic‑net regression on graph‑derived features.  
- [fMRI‑Kernel Regression: A Kernel‑based Method for Pointwise Statistical Analysis of rs‑fMRI for Population Studies (2020)](https://arxiv.org/abs/2012.06972) — Provides a kernel‑based statistical approach for population‑level rs‑fMRI analysis, guiding our nested cross‑validation and permutation testing strategy.  
- [Resting‑state functional connectivity‑based biomarkers and functional MRI‑based neurofeedback for psychiatric disorders: a challenge for developing theranostic biomarkers (2017)](https://arxiv.org/abs/1704.01350) — Discusses the broader challenge of deriving rs‑fMRI biomarkers for behavioral phenotypes, underscoring the relevance of our sleep‑quality target.  

## Expected results  

We anticipate that elastic‑net models trained on whole‑brain connectivity will achieve a statistically significant correlation (p < 0.05, permutation‑tested) between predicted and observed PSQI scores, with an out‑of‑sample R² around 0.05–0.15. Such an effect would demonstrate that rs‑fMRI encodes measurable variance in sleep quality beyond chance, while null results would suggest that connectivity alone is insufficient as a biomarker.  

## Methodology sketch  

- **Data acquisition**: Download the publicly available Human Connectome Project (HCP) 1200‑subject release (https://db.humanconnectome.org) and select participants who completed the Pittsburgh Sleep Quality Index (PSQI) questionnaire (available in the HCP behavioral data).  
- **Preprocessing**: Use the minimally preprocessed HCP rs‑fMRI runs; apply additional nuisance regression (motion, CSF, white‑matter) and band‑pass filter (0.01–0.1 Hz).  
- **Parcellation**: Extract time series for the Schaefer 200‑region cortical atlas plus subcortical ROIs (via `nibabel`/`nilearn`).  
- **Connectivity estimation**: Compute pairwise Pearson correlations between parcels, yielding a 200 × 200 matrix per subject; apply Fisher z‑transform.  
- **Feature engineering**:  
  - Flatten upper‑triangle of the connectivity matrix (≈19,900 edges).  
  - Compute graph‑theoretic metrics (global efficiency, modularity, nodal strength, hubness) using NetworkX.  
- **Dimensionality reduction**: Apply variance thresholding (retain edges with > 0.01 variance across subjects) and principal component analysis (retain 95 % variance) to keep the feature set < 5 k dimensions.  
- **Model training**:  
  - Split data into 5‑fold outer cross‑validation.  
  - Within each training fold, perform inner 5‑fold CV to tune elastic‑net α (mixing) and λ (regularization) using `scikit‑learn`.  
  - Fit the final model on the full training fold and predict PSQI scores on the held‑out fold.  
- **Evaluation**:  
  - Compute Pearson r and coefficient of determination (R²) between predicted and actual PSQI across all outer folds.  
  - Run 1,000 permutation tests (shuffle PSQI labels) to obtain a null distribution for r; calculate empirical p‑value.  
  - Perform bootstrap resampling (1,000 samples) to estimate confidence intervals for R².  
- **Feature importance**: Extract non‑zero elastic‑net coefficients; map back to edges and graph metrics; visualize the most predictive connections on a brain surface plot.  
- **Reproducibility**: All scripts will be containerized with Docker (Python 3.11, `nibabel`, `nilearn`, `scikit‑learn`, `networkx`); the workflow will be orchestrated with a Makefile to run end‑to‑end within the GitHub Actions free‑tier limits (< 7 GB RAM, < 6 h).  

## Duplicate-check  

- Reviewed existing ideas: *(none provided)*.  
- Closest match: *(no comparable project found)*.  
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-19T08:11:56Z
**Outcome**: success_after_expansion
**Original term**: Predicting Personal Sleep Quality from Resting-State fMRI Connectivity neuroscience
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Personal Sleep Quality from Resting-State fMRI Connectivity neuroscience | 0 |
| 1 | resting‑state functional connectivity biomarkers of sleep quality | 3 |
| 2 | rs‑fMRI connectivity patterns predicting sleep efficiency | 0 |
| 3 | machine‑learning models of sleep quality using intrinsic brain networks | 0 |
| 4 | functional connectome‑based prediction of subjective sleep quality | 0 |
| 5 | graph‑theoretic metrics of rs‑fMRI for sleep disturbance classification | 0 |
| 6 | deep‑learning approaches to estimate sleep quality from resting‑state data | 0 |
| 7 | intrinsic network alterations associated with poor sleep quality | 0 |
| 8 | predictive modeling of sleep health using resting‑state BOLD connectivity | 0 |
| 9 | resting‑state network signatures of insomnia severity | 0 |
| 10 | connectome‑based predictive modeling of individual sleep quality | 0 |
| 11 | functional connectivity correlates of sleep architecture | 0 |
| 12 | multimodal imaging predictors of sleep quality incorporating rs‑fMRI | 0 |
| 13 | resting‑state functional connectivity as a biomarker for sleep disorders | 0 |
| 14 | individualized sleep quality assessment via rs‑fMRI connectivity profiles | 0 |
| 15 | resting‑state brain network features for classification of sleep quality levels | 0 |

### Verified citations

1. **Fractal-driven distortion of resting state functional networks in fMRI: a simulation study** (2012). Wonsang You, Jörg Stadler. arXiv. [1208.0924](https://arxiv.org/abs/1208.0924). PDF-sampled: No.
2. **Fractal-based Correlation Analysis for Resting State Functional Connectivity of the Rat Brain in Functional MRI** (2012). Wonsang You, Joerg Stadler. arXiv. [1202.4751](https://arxiv.org/abs/1202.4751). PDF-sampled: No.
3. **Correlation-Distance Graph Learning for Treatment Response Prediction from rs-fMRI** (2023). Xiatian Zhang, Sisi Zheng, Hubert P. H. Shum, Haozheng Zhang, Nan Song, et al.. arXiv. [2311.10463](https://arxiv.org/abs/2311.10463). PDF-sampled: No.
4. **fMRI-Kernel Regression: A Kernel-based Method for Pointwise Statistical Analysis of rs-fMRI for Population Studies** (2020). Anand A. Joshi, Soyoung Choi, Haleh Akrami, Richard M. Leahy. arXiv. [2012.06972](https://arxiv.org/abs/2012.06972). PDF-sampled: No.
5. **Resting-state functional connectivity-based biomarkers and functional MRI-based neurofeedback for psychiatric disorders: a challenge for developing theranostic biomarkers** (2017). Takashi Yamada, Ryu-ichiro Hashimoto, Noriaki Yahata, Naho Ichikawa, Yujiro Yoshihara, et al.. arXiv. [1704.01350](https://arxiv.org/abs/1704.01350). PDF-sampled: No.
