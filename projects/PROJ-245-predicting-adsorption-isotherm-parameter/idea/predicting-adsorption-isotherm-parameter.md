---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Adsorption Isotherm Parameters from Molecular Features

**Field**: chemistry

## Research question

Which molecular descriptors of adsorbates and physicochemical properties of adsorbents most strongly determine key adsorption isotherm parameters (Henry's constant, Freundlich exponent, Langmuir capacity), and can these relationships enable reliable computational screening of gas adsorption materials?

## Motivation

Determining adsorption isotherm parameters experimentally is resource-intensive, creating a bottleneck in the design of materials for gas storage and separation. While simplified fitting equations exist, there is a lack of data-driven models that explicitly map molecular and surface descriptors to these thermodynamic parameters. This project addresses that gap by identifying the dominant physical drivers of adsorption behavior, enabling faster, physics-informed computational screening without requiring full-scale molecular simulations or new experiments.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using combinations of "adsorption isotherm parameters prediction," "machine learning Henry's constant," "molecular descriptors adsorption," and "Langmuir parameter estimation." We also performed broader searches on "type I isotherm fitting" and "surface defects adsorption theory" to capture foundational modeling approaches. The search yielded a small number of results directly addressing the predictive mapping of descriptors to parameters, with most literature focusing on fitting existing data or theoretical derivations rather than predictive modeling.

### What is known

- [Simple isotherm equations to fit type I adsorption data (2009)](https://arxiv.org/abs/0911.2012) — Establishes simplified analytical models for fitting experimental type I isotherm data on microporous adsorbents, providing the baseline mathematical framework for parameter extraction but not predictive modeling from descriptors.
- [Dose-dependent isotherm of Kr adsorption on heterogeneous bundles of closed single-walled carbon nanotubes (2021)](https://arxiv.org/abs/2111.06657) — Provides high-resolution experimental isotherm data for specific nanomaterials, illustrating the complexity of adsorption on heterogeneous surfaces but does not generalize to parameter prediction across diverse materials.
- [Adsorption from Binary Liquid Solutions into Mesoporous Silica: A Capacitance Isotherm on 5CB Nematogen/Methanol Mixtures (2021)](https://arxiv.org/abs/2102.06908) — Demonstrates advanced measurement techniques for liquid-phase adsorption, highlighting the importance of surface properties but remaining focused on specific binary systems rather than general predictive rules.

### What is NOT known

No published work has systematically quantified the relative importance of specific molecular descriptors (e.g., polarizability, van der Waals volume) versus adsorbent properties (e.g., pore volume, surface area) in determining Henry's constants or Langmuir capacities across a broad dataset. Furthermore, there is no established benchmark for whether machine learning models can reliably predict these parameters using only these descriptors, leaving the feasibility of rapid computational screening unproven.

### Why this gap matters

Filling this gap would allow researchers to prioritize high-potential adsorbent candidates for synthesis and testing based solely on their calculated molecular and structural properties, significantly accelerating the materials discovery cycle. Understanding the specific descriptors that drive adsorption strength could also guide the rational design of new materials with tailored surface properties for specific gas separation applications.

### How this project addresses the gap

This project will construct a dataset linking molecular and adsorbent descriptors to experimentally derived isotherm parameters, then train interpretable machine learning models to predict these parameters. By applying SHAP analysis and feature importance ranking, the study will explicitly identify which descriptors most strongly determine the parameters, directly answering the research question and providing a validated framework for computational screening.

## Expected results

We expect to identify a small subset of molecular descriptors (e.g., polarizability, kinetic diameter) and adsorbent properties (e.g., accessible surface area) that explain >70% of the variance in Henry's constants. The machine learning model is expected to achieve an R-squared value of at least 0.7 on held-out test data, demonstrating that these parameters can be predicted with sufficient accuracy for preliminary material screening. The feature importance rankings are expected to align with established physicochemical principles of gas-surface interactions, validating the model's physical interpretability.

## Methodology sketch

- Download and curate adsorption isotherm datasets from the NIST Adsorption Database and public repositories (e.g., MOF-1000 dataset via Zenodo DOI: 10.5281/zenodo.3933373) to extract Henry's constants, Freundlich exponents, and Langmuir parameters.
- Calculate molecular descriptors for adsorbates using RDKit (molecular weight, polar surface area, polarizability, H-bond donors/acceptors, van der Waals volume) and extract adsorbent properties (pore volume, surface area, functional group counts) from dataset metadata or crystallographic files.
- Preprocess the data by filtering for type I isotherms, removing entries with missing parameters or inconsistent units, and normalizing numerical features.
- Split the dataset into training (80%) and independent test (20%) sets, ensuring that different adsorbent materials are not split across sets to prevent data leakage.
- Train baseline linear regression, Random Forest, and Gradient Boosting regressors using scikit-learn, optimizing hyperparameters via 5-fold cross-validation on the training set.
- Evaluate model performance using R-squared, RMSE, and MAE on the independent test set, comparing against a null model predicting the mean.
- Apply SHAP (SHapley Additive exPlanations) analysis to the best-performing model to quantify the contribution of each descriptor to the predicted parameters.
- Generate correlation heatmaps and partial dependence plots to visualize the relationship between key descriptors and isotherm parameters.
- Validate model robustness by testing on a small subset of literature data not included in the training set (e.g., from the Kr adsorption study) to assess generalizability.
- Document the entire pipeline in a GitHub repository with a requirements.txt file, ensuring all data processing and model training steps are reproducible within a 6-hour GitHub Actions job.

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: None identified.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-14T05:11:07Z
**Outcome**: exhausted
**Original term**: Predicting Adsorption Isotherm Parameters from Molecular Features chemistry
**Verified citation count**: 4

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Adsorption Isotherm Parameters from Molecular Features chemistry | 4 |

### Verified citations

1. **Dose-dependent isotherm of Kr adsorption on heterogeneous bundles of closed single-walled carbon nanotubes** (2021). Svetlana Yu Tsareva, Edward Mcrae, Fabrice Valsaque, Xavier Devaux. arXiv. [2111.06657](https://arxiv.org/abs/2111.06657). PDF-sampled: No.
2. **Adsorption from Binary Liquid Solutions into Mesoporous Silica: A Capacitance Isotherm on 5CB Nematogen/Methanol Mixtures** (2021). Andriy V. Kityk, Gennady Y. Gor, Patrick Huber. arXiv. [2102.06908](https://arxiv.org/abs/2102.06908). PDF-sampled: No.
3. **Simple isotherm equations to fit type I adsorption data** (2009). Martin A. Mosquera. arXiv. [0911.2012](https://arxiv.org/abs/0911.2012). PDF-sampled: No.
4. **Theory, Simulation and Nanotechnological Applications of Adsorption on a Surface with Defects** (1998). Yu. E. Lozovik, A. M. Popov. arXiv. [physics/9804012](physics/9804012). PDF-sampled: No.
