---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys

**Field**: materials science

## Research question

How does processing temperature during rolling affect the final grain size distribution of aluminum alloys, and can this relationship be quantified using existing materials datasets?

## Motivation

Grain size is a critical determinant of mechanical properties in aluminum alloys used for aerospace and automotive applications. Current metallurgical models rely on simplified assumptions about temperature-dependent grain growth that may not capture alloy-specific behavior. Establishing a data-driven relationship between processing temperature and grain size would enable more precise manufacturing control without requiring costly experimental validation.

## Literature gap analysis

### What we searched

Searched Semantic Scholar, arXiv, and OpenAlex using queries: "aluminum alloy grain size rolling temperature," "processing temperature grain growth aluminum," and "severe plastic deformation aluminum grain structure." Retrieved 2 results total.

### What is known

- [Nanomaterials by severe plastic deformation: review of historical developments and recent advances (2022)](https://doi.org/10.1080/21663831.2022.2029779) — Establishes that severe plastic deformation techniques can produce ultrafine-grained materials, though focused on SPD methods rather than conventional rolling processes.

### What is NOT known

No published work has systematically quantified the temperature-grain size relationship specifically for conventionally rolled aluminum alloys using machine learning on public datasets. Existing literature focuses on either SPD nanomaterials or specific alloy systems (e.g., Ti-based biomedical alloys) without addressing the generalizable temperature-dependent grain growth mechanisms in rolled aluminum.

### Why this gap matters

Manufacturing engineers need predictive models to optimize rolling parameters for desired material properties without trial-and-error experimentation. Filling this gap would enable computational materials design for aluminum alloy processing, potentially reducing production costs and improving quality control in aerospace and automotive industries.

### How this project addresses the gap

This project will download existing aluminum alloy composition and processing parameter datasets, extract temperature and grain size measurements, and train regression models to quantify the temperature-grain size relationship. The methodology directly produces the previously-unavailable data-driven mapping between processing temperature and grain size distribution.

## Expected results

A regression model achieving R² > 0.6 would indicate temperature is a significant predictor of grain size, confirming established metallurgical theory with quantitative precision. An R² < 0.3 would suggest additional factors (alloy composition, strain rate, cooling rate) dominate grain size determination, challenging simplified temperature-only models. Either outcome provides actionable insight for process optimization.

## Methodology sketch

- Download aluminum alloy datasets from Materials Project (https://materialsproject.org) and OpenML (https://openml.org/search?type=data) using wget/curl
- Filter for entries containing rolling temperature, alloy composition, and measured grain size
- Preprocess data: handle missing values, normalize temperature and composition features, encode categorical alloy types
- Split data into training (70%), validation (15%), and test (15%) sets
- Train baseline linear regression model to establish minimum performance threshold
- Train random forest regression with hyperparameter grid search (n_estimators: 50-200, max_depth: 5-20)
- Evaluate models using R² score, mean absolute error, and residual analysis on test set
- Extract feature importance to identify whether temperature dominates or is secondary to composition effects
- Generate partial dependence plots showing grain size vs. temperature across alloy types
- Save final model coefficients and plots as artifacts for reproducibility

## Duplicate-check

- Reviewed existing ideas: None in corpus.
- Closest match: None identified.
- Verdict: NOT a duplicate
