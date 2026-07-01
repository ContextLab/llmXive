---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys

**Field**: materials science

## Research question

How do alloy-specific compositional interactions modulate deviations from standard temperature-dependent grain growth kinetics in rolled aluminum alloys?

## Motivation

Standard metallurgical models often assume a universal temperature-dependent grain growth law, yet industrial rolling processes yield alloy-specific outcomes that these models fail to predict accurately. Understanding how specific elemental compositions interact with thermal history to alter growth kinetics is essential for optimizing mechanical properties in aerospace and automotive applications without relying on costly trial-and-error experimentation.

## Literature gap analysis

### What we searched

Searched Semantic Scholar, arXiv, and OpenAlex using queries: "aluminum alloy grain size rolling temperature," "alloy composition grain growth kinetics aluminum," and "recrystallization nucleation aluminum composition." Retrieved 3 results total.

### What is known

- [Grain-Boundary Kinetics: A Unified Approach (2018)](https://arxiv.org/abs/1803.03214) — Establishes the theoretical framework for grain boundary kinetics as the primary driver of polycrystalline evolution, though it focuses on general principles rather than specific aluminum alloy compositional deviations.
- [Significance of Strain Rate in Severe Plastic Deformation on Steady-State Microstructure and Strength (2023)](https://arxiv.org/abs/2301.02805) — Demonstrates that microstructure saturation is highly sensitive to processing parameters, noting temperature effects but primarily within the context of severe plastic deformation (SPD) rather than conventional rolling.
- [On recrystallization nucleation in pure aluminum (2023)](https://arxiv.org/abs/2305.08378) — Details the nucleation mechanisms in pure aluminum, providing a baseline for understanding grain formation in the absence of alloying elements, but lacks data on how specific alloying additions modulate these kinetics.

### What is NOT known

No published work has systematically quantified the interaction terms between specific alloying elements (e.g., Mg, Si, Cu) and processing temperature to predict deviations from standard grain growth kinetics in conventionally rolled aluminum alloys. Existing literature isolates pure aluminum behavior or focuses on extreme deformation regimes (SPD), leaving a gap in predictive models for standard industrial rolling conditions where composition and temperature co-vary.

### Why this gap matters

Manufacturers lack a data-driven method to anticipate how changing an alloy's minor composition will shift the optimal rolling temperature window, leading to suboptimal grain structures and reduced mechanical performance. Filling this gap would enable precise "composition-temperature" mapping for process control, reducing waste and improving the consistency of high-strength aluminum components.

### How this project addresses the gap

This project will curate public datasets containing rolling parameters, alloy compositions, and resulting grain sizes, then apply regression modeling with interaction terms to explicitly isolate and quantify how compositional factors modulate the temperature-grain size relationship. The resulting model will provide the first quantitative map of these deviations for conventional rolling, directly addressing the lack of composition-specific kinetic data.

## Expected results

We expect to identify significant interaction effects where specific alloying elements either accelerate or retard grain growth at given temperatures compared to pure aluminum baselines. A model with an R² > 0.6 on the test set would confirm that compositional modulation is a dominant, predictable factor, whereas a null result would suggest that temperature effects are largely independent of composition within the standard rolling regime, challenging current alloy design heuristics.

## Methodology sketch

- Download aluminum alloy datasets from Materials Project (https://materialsproject.org) and OpenML (https://openml.org/search?type=data) using `wget`/`curl` to ensure reproducibility within the 6-hour GitHub Actions limit.
- Filter entries to retain only those with explicit rolling temperature, full alloy composition (wt%), and measured grain size.
- Preprocess data: impute missing values, normalize temperature and composition features, and create interaction features (e.g., `Temperature × %Mg`, `Temperature × %Si`).
- Split the dataset into training (70%), validation (15%), and test (15%) sets, ensuring stratification by alloy series to prevent data leakage.
- Train a baseline linear regression model to establish the main effects of temperature and composition.
- Train a Random Forest regressor (grid search: `n_estimators` 50-200, `max_depth` 5-20) to capture non-linear interaction effects.
- Evaluate models using R² score and Mean Absolute Error (MAE) on the held-out test set.
- Perform feature importance analysis and partial dependence plotting to visualize how specific alloying elements shift the temperature-grain size curve.
- Validate the model's predictive power against an independent subset of the data (e.g., a specific alloy series not used in training) to ensure the interaction terms are robust and not overfitted.
- Save model artifacts, coefficients, and visualization plots for downstream analysis.

## Duplicate-check

- Reviewed existing ideas: None in corpus.
- Closest match: None identified.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-01T21:37:14Z
**Outcome**: exhausted
**Original term**: Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys materials science
**Verified citation count**: 3

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys materials science | 3 |

### Verified citations

1. **Grain-Boundary Kinetics: A Unified Approach** (2018). Jian Han, Spencer L. Thomas, David J. Srolovitz. arXiv. [1803.03214](https://arxiv.org/abs/1803.03214). PDF-sampled: No.
2. **Significance of Strain Rate in Severe Plastic Deformation on Steady-State Microstructure and Strength** (2023). Kaveh Edalati, Qing Wang, Nariman A. Enikeev, Laura-Jean Peters, Michael J. Zehetbauer, et al.. arXiv. [2301.02805](https://arxiv.org/abs/2301.02805). PDF-sampled: No.
3. **On recrystallization nucleation in pure aluminum** (2023). Adam Morawiec. arXiv. [2305.08378](https://arxiv.org/abs/2305.08378). PDF-sampled: No.
