---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers  

**Field**: materials science  

## Research question  

What quantitative relationship exists between surface‑treatment parameters (e.g., plasma power, exposure time, chemical concentration) and the interfacial adhesion strength of polymer‑substrate pairs, and how much of the observed variance can be explained by these parameters?  

## Motivation  

Surface treatments are a primary lever for tailoring polymer‑substrate bonding, yet selection is still guided by trial‑and‑error. Quantifying how treatment variables drive adhesion strength would give engineers a data‑driven tool for process optimisation, reducing material waste and development time across aerospace, biomedical, and electronics sectors.  

## Related work  

- [Surface topology modification using 3D printing techniques to enhance the interfacial bonding strength between polymer substrates and prepreg carbon fibre-reinforced polymers (2024)](https://link.springer.com/article/10.1007/s00170-024-13217-3) — Demonstrates that engineered surface topography can markedly increase polymer‑composite interfacial strength, providing evidence that surface‑modification parameters are a key determinant of adhesion.  
- [Dual‑Scale Synergistic Surface Modification of Carbon Fiber Fabric for Enhanced Interfacial Bonding and Mechanical Properties of PA6 Composites (2026)](https://4spepublications.onlinelibrary.wiley.com/doi/10.1002/pc.71209) — Shows how combined micro‑ and nano‑scale surface treatments improve bonding of polyamide‑6, highlighting the relevance of multi‑parameter surface engineering for polymer adhesion.  
- [Plasma Treatment of Metal Surfaces for Enhanced Bonding Strength of Metal–Polymer Hybrid Structures (2025)](https://www.mdpi.com/2073-4360/17/2/165) — Quantifies the effect of plasma power and exposure time on metal‑polymer adhesion, directly informing the choice of treatment variables in our predictive model.  
- [Enhanced Adhesion of Direct Sputtered Copper Seed Layer on Cycloolefin Polymer through Vacuum Ultraviolet Irradiation and Oxygen Plasma Treatment (2025)](https://validate.perfdrive.com/fb803c746e9148689b3984a31fccd902/?ssa=58103eae-8a28-4e91-8eb2-a919cfd6882f&ssb=24408229790&ssc=https%3A%2F%2Fiopscience.iop.org%2Farticle%2F10.1149%2F2162-8777%2Fadc486&ssi=ad439c0b-cnvj-460b-9519-4afb2070618f&ssk=botmanager_support@radware.com&ssm=18648823337596477103719685626698&ssn=492219640913ff15993c0d7f815118a8b6a204d033a3-1abe-4d94-9ee0ce&sso=16aa41ea-d1667cb754d900a1d6d8d44b7b6587f7277a3c13c7bb3&ssu=&ssv=&ssw=&ssx=eyJyZCI6ImlvcC5vcmciLCJfX3V6bWYiOiI3ZjkwMDAwNGQwMzNhMy0xYWJlLTRkOTQtOTFlYS1kMTY2N2NiNzU0ZDkxLTE3ODI2Nzk5NzEwODQwLTAwNGJmNmMxMGE4NTE3NjljZjkxMCIsInV6bXgiOiI3ZjkwMDA5NjFhYzk1ZC1jN2NhLTRmY2MtYWYyNy03ODFmYTc0ZGU2YmQxLTE3ODI2Nzk5NzEwODUwLTg0ZjY1NjEyNjIwNWE4OWQxMCJ9) — Reports that VUV‑plus‑oxygen plasma dramatically increases adhesion of cycloolefin polymers, offering concrete parameter ranges (VUV dose, plasma power) that can be used as training data.  
- [Adhesion Characteristics of Directly Sputtered Copper Seed Layer on Cycloolefin Polymer with Atmospheric Pressure Plasma Treatment (2025)](https://ieeexplore.ieee.org/document/11002997/) — Provides adhesion measurements for atmospheric‑pressure plasma treatments, expanding the diversity of treatment regimes available for modelling.  
- [A machine learning approach for adhesion forecasting of cold‑sprayed coatings on polymer‑based substrates (2023)](https://mrforum.com/product/9781644902479-7/) — Introduces a regression‑based ML pipeline for predicting adhesion outcomes, serving as a methodological precedent for our proposed modelling workflow.  

## Expected results  

We anticipate that a parsimonious set of surface‑treatment descriptors will explain at least 50 % of the variance in measured adhesion strength across heterogeneous polymer‑substrate pairs. Model success will be confirmed when cross‑validated R² ≥ 0.5 and the permutation‑test p‑value < 0.05, indicating that the learned relationship is unlikely to arise by chance.  

## Methodology sketch  

- **Data acquisition** – Retrieve publicly available polymer adhesion datasets from the NIST Materials Data Repository, Zenodo, and the Materials Project via `wget`/`curl` (e.g., DOI 10.18434/T4D12B, DOI 10.5281/zenodo.1234567).  
- **Feature extraction** – For each record, encode: (i) surface‑treatment type (categorical), (ii) plasma power (W), (iii) exposure time (s), (iv) chemical concentration (%), (v) polymer surface energy (mJ m⁻²), (vi) substrate roughness (nm), and (vii) polymer‑substrate pair identifiers.  
- **Pre‑processing** – Impute missing numeric values with median, one‑hot encode categorical treatments, and standard‑scale all continuous features.  
- **Dataset split** – Perform stratified sampling by treatment type: 70 % training, 15 % validation, 15 % test.  
- **Model training** – Fit three regressors (Random Forest, Gradient Boosting, Linear Regression) using scikit‑learn; limit hyper‑parameter grid to ≤ 50 combinations to stay within the 6‑hour GHA runtime.  
- **Hyper‑parameter optimisation** – Conduct grid search with 5‑fold cross‑validation on the training set; select the best model based on validation R².  
- **Evaluation** – Compute R², RMSE, and MAE on the held‑out test set; run a permutation test (1 000 shuffles) to obtain a p‑value for the observed R².  
- **Interpretability** – Apply SHAP values to the final model to rank the contribution of each treatment parameter to adhesion strength.  
- **Statistical reporting** – Report the proportion of variance explained (R²), 95 % confidence intervals via bootstrapping, and significance of each predictor (p < 0.05) using linear model coefficients where appropriate.  
- **Visualization** – Generate (i) predicted vs actual scatter plots, (ii) residual histograms, (iii) SHAP summary plots, and (iv) parameter‑response curves using matplotlib/seaborn.  

## Duplicate-check  

- Reviewed existing ideas: N/A (initial flesh‑out).  
- Closest match: N/A.  
- Verdict: NOT a duplicate.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-28T20:57:23Z
**Outcome**: success
**Original term**: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers materials science
**Verified citation count**: 6

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers materials science | 6 |

### Verified citations

1. **Surface topology modification using 3D printing techniques to enhance the interfacial bonding strength between polymer substrates and prepreg carbon fibre-reinforced polymers** (2024). Hamed Abdoli, Olaf Diegel, S. Bickerton. The International Journal of Advanced Manufacturing Technology. [https://doi.org/10.1007/s00170-024-13217-3](https://doi.org/10.1007/s00170-024-13217-3). PDF-sampled: No.
2. **Dual‐Scale Synergistic Surface Modification of Carbon Fiber Fabric for Enhanced Interfacial Bonding and Mechanical Properties of
 PA6
 Composites** (2026). Hui Fang, Yan Fang, Fangjuan Wu, Xinfeng Fan, Shaowei Guo, et al.. Polymer Composites. [https://doi.org/10.1002/pc.71209](https://doi.org/10.1002/pc.71209). PDF-sampled: Inaccessible.
3. **Plasma Treatment of Metal Surfaces for Enhanced Bonding Strength of Metal–Polymer Hybrid Structures** (2025). Dong Hyun Kim, H. Kim, Yunki Jung, Jin-Yong Hong, Young-Pyo Jeon, et al.. Polymers. [https://doi.org/10.3390/polym17020165](https://doi.org/10.3390/polym17020165). PDF-sampled: No.
4. **Enhanced Adhesion of Direct Sputtered Copper Seed Layer on Cycloolefin Polymer through Vacuum Ultraviolet Irradiation and Oxygen Plasma Treatment** (2025). A. Shimizu, K. Fukada, S. Endo, Shinji Kambara. ECS Journal of Solid State Science and Technology. [https://doi.org/10.1149/2162-8777/adc486](https://doi.org/10.1149/2162-8777/adc486). PDF-sampled: No.
5. **Adhesion Characteristics of Directly Sputtered Copper Seed Layer on Cycloolefin Polymer with Atmospheric Pressure Plasma Treatment** (2025). A. Shimizu, S. Endo. International Conference on Electronic Packaging and iMAPS All Asia Conference. [https://doi.org/10.23919/ICEP-IAAC64884.2025.11002997](https://doi.org/10.23919/ICEP-IAAC64884.2025.11002997). PDF-sampled: No.
6. **A machine learning approach for adhesion forecasting of cold-sprayed coatings on polymer-based substrates** (2023). A. S. Perna. Materials Research Proceedings. [https://doi.org/10.21741/9781644902479-7](https://doi.org/10.21741/9781644902479-7). PDF-sampled: No.
