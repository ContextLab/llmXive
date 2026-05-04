---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Alloying on Magnetic Properties via Public Data

**Field**: materials science

## Research question

Can supervised machine learning models trained on public compositional and structural data accurately predict the saturation magnetization and Curie temperature of bulk alloy systems?

## Motivation

Experimental determination of magnetic properties is resource-intensive and slow, creating a bottleneck in permanent magnet discovery. A data-driven surrogate model could screen thousands of hypothetical alloy compositions in silico, prioritizing only the most promising candidates for synthesis and reducing material development costs.

## Related work

- [Data-driven materials science: status, challenges and perspectives (2019)](http://arxiv.org/abs/1907.05644v2) — Establishes the paradigm of using large datasets to extract knowledge for property prediction without traditional experiments.
- [Contraction and expansion effects on the substitution-defect properties of thirteen alloying elements in bcc Fe (2010)](http://arxiv.org/abs/1008.3001v1) — Provides specific evidence of how alloying elements alter fundamental properties in iron-based systems, a key target for this model.
- [Charting the complete elastic properties of inorganic crystalline compounds (2015)](https://doi.org/10.1038/sdata.2015.9) — Demonstrates the feasibility of mapping crystal structure and composition to physical properties using public databases.

## Expected results

We expect to achieve an R-squared value > 0.8 for saturation magnetization predictions on a held-out test set of known alloys. Feature importance analysis will identify specific elemental descriptors (e.g., atomic radius, valence electron count) that most strongly correlate with magnetic performance.

## Methodology sketch

- **Data Acquisition**: Query the Materials Project API (https://materialsproject.org/dashboard) to download properties for a subset of < 5,000 magnetic compounds (Fe, Co, Ni-based) to fit within the 14 GB SSD limit.
- **Data Cleaning**: Filter for entries with valid experimental or DFT-calculated magnetic moments and remove entries with missing composition data.
- **Feature Engineering**: Convert chemical formulas into numerical descriptors (elemental fractions, weighted averages of atomic radius, electronegativity, and valence) using `pymatgen` or `matminer`.
- **Model Training**: Train Random Forest and Gradient Boosting Regressors using `scikit-learn` on the CPU-only GHA runner; tune hyperparameters via GridSearchCV with 5-fold cross-validation.
- **Evaluation**: Assess performance using Mean Squared Error (MSE) and R-squared metrics; apply a t-test to compare model residuals against a baseline linear regression.
- **Reproducibility**: Store processed dataset and trained model weights as artifacts; log all random seeds to ensure deterministic runs within the 6-hour job limit.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: None.
- Verdict: NOT a duplicate
