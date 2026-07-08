---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Diffusion of Carbon in BCC Metals from Compositional Data

**Field**: materials science

## Research question

Which compositional descriptors (atomic radius variance, valence electron concentration, electronegativity spread) most strongly govern carbon diffusion coefficients in body-centered cubic (BCC) metals, and what fraction of diffusion-rate variance can be explained by composition alone versus microstructural factors?

## Motivation

Carbon diffusion is the rate-limiting step in critical processes like carburization and steel hardening, yet traditional physics-based models struggle to capture complex compositional interactions in multi-element BCC alloys. While machine learning offers a path to rapid screening, the specific contribution of bulk composition versus microstructural defects (grain boundaries, dislocations) remains poorly quantified. This project addresses that gap by isolating the predictive power of compositional features alone, establishing a baseline for when composition is sufficient and when microstructural data becomes necessary.

## Literature gap analysis

### What we searched
We queried Semantic Scholar, arXiv, and OpenAlex using terms including "carbon diffusion BCC metals machine learning," "compositional descriptors diffusion coefficient," and "valence electron concentration diffusion kinetics." We also broadened the search to "materials informatics diffusion" and "data-driven diffusion modeling." The results returned were sparse regarding the specific intersection of carbon diffusion in BCC lattices and supervised learning on compositional data; most literature focused on general ML methodologies, data sources for official statistics, or biological applications rather than specific metallurgical diffusion mechanisms.

### What is known
- *No on-topic primary sources were found in the provided literature block.* The available search results focus on general machine learning validation in biology (DOME), learning curves, and data source changes in statistics, none of which provide specific empirical data or mechanistic models for carbon diffusion in BCC metals.

### What is NOT known
There is no published work that quantitatively partitions the variance of carbon diffusion coefficients in BCC metals into components explainable by bulk composition (e.g., atomic radius variance, VEC) versus those requiring microstructural descriptors. Current literature lacks a systematic benchmark demonstrating how much predictive accuracy is lost when excluding microstructural factors, leaving a gap in understanding the fundamental limits of composition-only models.

### Why this gap matters
Materials scientists and alloy designers need to know if high-throughput screening based solely on bulk composition is viable for carbon diffusion, or if expensive microstructural characterization is mandatory. Filling this gap will clarify whether composition-driven proxies are sufficient for initial alloy selection or if they inherently fail to capture the physics of carbon mobility in defective lattices, thereby guiding resource allocation in computational materials discovery.

### How this project addresses the gap
This project will construct a dataset of carbon diffusion coefficients in BCC metals and train regression models using only compositional descriptors. By evaluating the $R^2$ and feature importance of these models, we will directly quantify the fraction of variance explainable by composition. The methodology will explicitly test the limits of composition-only prediction, providing the first empirical estimate of the "microstructural gap" in this specific domain.

## Expected results

We expect that compositional descriptors alone will explain a moderate fraction (likely $R^2 \approx 0.4-0.6$) of the variance in carbon diffusion coefficients, indicating that while composition sets the baseline, microstructural factors play a significant role. Feature importance analysis should reveal that valence electron concentration and atomic size mismatch are the dominant predictors, while the residual variance will serve as a proxy for the influence of unmodeled microstructural defects.

## Methodology sketch

- **Data acquisition**: Retrieve carbon diffusion coefficients ($D$) and corresponding BCC metal compositions from the NIST Materials Data Repository (https://doi.org/10.18434/T4M88P) and the Materials Project (https://materialsproject.org); filter specifically for BCC crystal structures and interstitial carbon diffusion mechanisms.
- **Data preprocessing**: Clean the dataset by removing entries with non-BCC structures or missing composition data; normalize atomic fractions to sum to 1.0; log-transform diffusion coefficients ($\log_{10} D$) to handle the wide dynamic range typical of diffusion data.
- **Feature engineering**: Compute compositional descriptors using `pymatgen` and `matminer`: average atomic radius, electronegativity variance, valence electron concentration (VEC), and mixing entropy; exclude any microstructural features (grain size, dislocation density) to isolate composition effects.
- **Model training**: Split the dataset into 80% training and 20% test sets (stratified by metal type if possible); train Random Forest, XGBoost, and Elastic Net regression models using `scikit-learn` within a single 6-hour GitHub Actions job.
- **Hyperparameter tuning**: Perform a constrained grid search (10-15 combinations) focusing on tree depth and regularization strength to prevent overfitting on the likely small dataset size; limit total tuning time to 1 hour.
- **Evaluation metrics**: Calculate $R^2$, RMSE, and MAE on the held-out test set; perform 5-fold cross-validation to assess model stability and generalization error.
- **Statistical validation**: Apply a paired t-test (α=0.05) to compare the performance of the best ML model against a simple linear baseline; calculate the proportion of total variance in $\log_{10} D$ explained by the model (adjusted $R^2$).
- **Feature importance analysis**: Extract SHAP (SHapley Additive exPlanations) values to rank the contribution of each compositional descriptor; generate partial dependence plots to visualize the non-linear relationship between key descriptors (e.g., VEC) and diffusion rates.
- **Independent validation**: Compare the model's predicted trends against a separate, independent set of diffusion data from a different source (e.g., a specific subset of the OpenKIM repository) to ensure the model is not merely memorizing the training distribution.
- **Output**: Generate a CSV file of predictions, a JSON summary of feature importances, and PNG plots of the variance partitioning analysis for reproducibility.

## Duplicate-check

- Reviewed existing ideas: None in corpus.
- Closest match: None identified.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-08T07:14:23Z
**Outcome**: success_after_expansion
**Original term**: Predicting the Diffusion of Carbon in BCC Metals from Compositional Data materials science
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting the Diffusion of Carbon in BCC Metals from Compositional Data materials science | 0 |
| 1 | carbon diffusion coefficients in body-centered cubic metals | 0 |
| 2 | machine learning prediction of interstitial diffusion in BCC alloys | 5 |
| 3 | compositional descriptors for solute diffusion in iron | 0 |
| 4 | atomic diffusion mechanisms of carbon in ferrite | 0 |
| 5 | data-driven modeling of carbon mobility in BCC crystal structures | 0 |
| 6 | first-principles calculation of carbon migration barriers in BCC metals | 0 |
| 7 | composition-property relationships for diffusion in body-centered cubic lattices | 0 |
| 8 | interstitial solute diffusion prediction using neural networks | 0 |
| 9 | carbon diffusion in alpha-iron and bcc transition metals | 0 |
| 10 | high-throughput screening of diffusion coefficients in BCC alloys | 0 |
| 11 | activation energy prediction for carbon diffusion in body-centered cubic phases | 0 |
| 12 | machine learning interatomic potentials for carbon diffusion in BCC metals | 0 |
| 13 | solute diffusion kinetics in body-centered cubic crystal systems | 0 |
| 14 | predictive models for carbon transport in ferritic steels | 0 |
| 15 | computational materials design of diffusion in BCC metals | 0 |
| 16 | correlation between alloy composition and carbon diffusivity in BCC structures | 0 |
| 17 | diffusion of interstitial atoms in body-centered cubic lattices | 0 |
| 18 | data-centric approaches to estimating diffusion in BCC metallic systems | 0 |
| 19 | carbon migration pathways in body-centered cubic metal matrices | 0 |
| 20 | diffusion coefficient estimation for carbon in BCC alloys using compositional features | 0 |

### Verified citations

1. **Changing Data Sources in the Age of Machine Learning for Official Statistics** (2023). Cedric De Boom, Michael Reusens. arXiv. [2306.04338](https://arxiv.org/abs/2306.04338). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
2. **DOME: Recommendations for supervised machine learning validation in biology** (2020). Ian Walsh, Dmytro Fishman, Dario Garcia-Gasulla, Tiina Titma, Gianluca Pollastri, et al.. arXiv. [2006.16189](https://arxiv.org/abs/2006.16189). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
3. **Learning Curves for Decision Making in Supervised Machine Learning: A Survey** (2022). Felix Mohr, Jan N. van Rijn. arXiv. [2201.12150](https://arxiv.org/abs/2201.12150). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
4. **Active learning for data streams: a survey** (2023). Davide Cacciarelli, Murat Kulahci. arXiv. [2302.08893](https://arxiv.org/abs/2302.08893). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
5. **Privacy-preserving machine learning for healthcare: open challenges and future perspectives** (2023). Alejandro Guerra-Manzanares, L. Julian Lechuga Lopez, Michail Maniatakos, Farah E. Shamout. arXiv. [2303.15563](https://arxiv.org/abs/2303.15563). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
