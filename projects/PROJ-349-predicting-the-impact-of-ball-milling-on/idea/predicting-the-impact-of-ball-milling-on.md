---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Ball Milling on Particle Size Distribution

**Field**: materials science

## Research question

How do ball milling parameters (speed, time, ball-to-powder ratio) and material properties (Young's modulus, density) influence the final particle size distribution of milled powders?

## Motivation

Precise control of particle size distribution is critical in materials applications ranging from pharmaceuticals to battery electrodes. Current methods rely heavily on empirical testing and iterative optimization, which is time-consuming and resource-intensive. Establishing a predictive relationship between milling parameters and PSD outcomes would enable more efficient process design and reduce experimental burden.

## Literature gap analysis

### What we searched

Literature search queries included: "ball milling particle size prediction," "milling parameters particle size distribution ML," "mechanomilling PSD modeling," and "ball milling process optimization machine learning." Searches were performed on Semantic Scholar, arXiv, and OpenAlex. The literature search returned 5 papers, with only 1 directly addressing milling effects on particle properties.

### What is known

- [Influence of short time milling in R5(Si,Ge)4, R =Gd and Tb, magnetocaloric materials (2015)](http://arxiv.org/abs/1505.02573v1) — Demonstrates that milling time affects particle size and atomic structure in magnetocaloric materials, establishing empirical relationships between milling duration and particle morphology.

### What is NOT known

No published work has systematically modeled the relationship between ball milling process parameters (speed, time, ball-to-powder ratio) and final particle size distribution using machine learning. Existing studies report milling effects on specific material systems but do not provide generalizable predictive models. There is also no consolidated public dataset of ball milling experiments with standardized parameter reporting.

### Why this gap matters

Materials scientists and process engineers would benefit from a predictive tool to optimize milling conditions without extensive trial-and-error. Filling this gap could reduce development time for new materials, lower production costs, and enable more consistent particle size control in applications like catalysis, pharmaceuticals, and energy storage.

### How this project addresses the gap

This project will aggregate publicly available ball milling experimental data from materials science literature and databases, extract standardized features (milling parameters, material properties, resulting PSD), and train a machine learning model to predict PSD outcomes. The methodology directly produces the previously-unavailable predictive relationship between process inputs and particle size outputs.

## Expected results

The model will demonstrate measurable predictive accuracy (R² > 0.6) for particle size distribution outcomes given milling parameters and material properties. Success will be confirmed if the model outperforms baseline linear regression and if cross-validation shows consistent performance across different material classes. The level of evidence needed includes a minimum of 500 documented milling experiments from public sources.

## Methodology sketch

- **Data acquisition**: Query Materials Project, NIST Materials Data Repository, and arXiv for ball milling experiments with reported PSD data; use `wget`/`curl` to download CSV/JSON datasets (target: 500+ data points)
- **Feature engineering**: Extract milling parameters (speed in RPM, time in hours, ball-to-powder ratio), material properties (Young's modulus from Materials Project API, density from literature), and target PSD metrics (D10, D50, D90)
- **Data preprocessing**: Handle missing values via multiple imputation; normalize numerical features; encode categorical material types
- **Model selection**: Train Gaussian Process Regression (GPR) and Random Forest models using scikit-learn; limit to ≤1000 trees for Random Forest to fit 7GB RAM constraint
- **Training**: Use 5-fold cross-validation on GitHub Actions runner; limit each fold to ≤30 minutes runtime; total training ≤3 hours
- **Evaluation**: Compute R², RMSE, and MAE on held-out test set (20% of data); compare against linear regression baseline
- **Statistical testing**: Apply paired t-test on cross-validation scores to determine if ML models significantly outperform baseline (α = 0.05)
- **Visualization**: Generate partial dependence plots showing PSD response to individual milling parameters; save figures as PNG (≤10MB total)
- **Documentation**: Export model coefficients and feature importance rankings to JSON for interpretability
- **Scope validation**: Confirm all computations complete within 6-hour GHA job limit; if exceeded, reduce dataset size or simplify model complexity

## Duplicate-check

- Reviewed existing ideas: None in current corpus (first flesh-out attempt for this field).
- Closest match: None identified.
- Verdict: NOT a duplicate
