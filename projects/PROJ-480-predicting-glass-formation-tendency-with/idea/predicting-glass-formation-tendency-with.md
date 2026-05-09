---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting Glass Formation Tendency with Machine Learning on Public Data

**Field**: materials science

## Research question

How do atomic size mismatch and mixing enthalpy descriptors quantitatively predict critical casting thickness in multi-component metallic glass systems?

## Motivation

Predicting glass formation reduces the need for costly trial-and-error synthesis in metallic alloy development. While existing frameworks exist for specific ternary systems, there is limited aggregation of public data to validate these descriptors across broader metallic glass families.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv for "glass forming ability machine learning", "metallic glass prediction", and "materials science data ecosystem". Results returned included 1 direct match on glass-forming ability in ternary systems and 1 match on data ecosystems in materials science, with several tangential ML theory papers.

### What is known

- [A Machine Learning Framework for Predicting Glass-Forming Ability in Ternary Alloy Systems (2025)](http://arxiv.org/abs/2512.05895v2) — Establishes ML methods for GFA prediction but focuses primarily on ternary oxide systems rather than multi-component metallic alloys.
- [A Data Ecosystem to Support Machine Learning in Materials Science (2019)](http://arxiv.org/abs/1904.10423v2) — Outlines the infrastructure needs for data collection and dissemination but does not provide specific predictive models for glass formation.

### What is NOT known

There is no published work that explicitly aggregates public metallic glass datasets to test the generalizability of thermodynamic descriptors (like mixing enthalpy) across diverse multi-component systems using CPU-constrained environments. Most existing work remains siloed in specific alloy families or requires heavy computational resources.

### Why this gap matters

Filling this gap would enable rapid screening of metallic glass candidates on standard hardware, lowering the barrier for materials discovery in academic and small-industry settings where GPU clusters are unavailable.

### How this project addresses the gap

This project will curate a unified dataset from public repositories and train interpretable gradient boosting models to quantify descriptor importance, specifically targeting the multi-component metallic alloy regime not covered by the 2025 ternary oxide framework.

## Expected results

We expect to identify a subset of 3-5 atomic descriptors that correlate with critical casting thickness with >80% classification accuracy. This will demonstrate that public data aggregation can yield robust predictors without requiring proprietary datasets or heavy compute.

## Methodology sketch

- Download curated metallic glass composition data from the Materials Project API and Zenodo repositories (e.g., Glass Data Repository).
- Compute atomic descriptors (electronegativity, atomic radius, mixing enthalpy) for each composition using the `pymatgen` library.
- Split data into 80/20 train-test sets, ensuring no composition overlap between sets to prevent data leakage.
- Train a Gradient Boosting Classifier (XGBoost) on CPU to predict glass-forming ability (binary: glass vs. crystal).
- Perform 5-fold cross-validation to assess model stability and generalization error (RMSE/AUC).
- Extract feature importance scores to rank descriptors by their contribution to prediction.
- Visualize decision boundaries for top-performing descriptor pairs to interpret physical constraints.
- Validate findings against the 2025 ternary framework results to confirm domain-specific differences.
- Document all code and data processing steps in a reproducible GitHub Actions workflow.
- Estimate runtime to ensure completion within 6 hours on 2 CPU cores and 7GB RAM.

## Duplicate-check

- Reviewed existing ideas: None.
- Closest match: A Machine Learning Framework for Predicting Glass-Forming Ability in Ternary Alloy Systems (2025) (similarity sketch: shared GFA prediction goal, but differs in alloy type and data aggregation scope).
- Verdict: NOT a duplicate
