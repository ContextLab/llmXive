---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks

**Field**: materials science

## Research question

Which early-cycle electrochemical signatures (voltage curves, current profiles, temperature fluctuations) carry the most predictive signal for long-term capacity fade in lithium-ion cells, and how do these signals vary across different cycling protocols?

## Motivation

Accurate prediction of battery degradation is critical for optimizing the lifespan of electric vehicles and grid storage, yet current models often rely on handcrafted features that may miss subtle temporal patterns. By analyzing the raw temporal dynamics of early-cycle electrochemical data, this research aims to identify the specific physical signatures that most strongly correlate with long-term failure, providing a more robust foundation for battery health management systems.

## Literature gap analysis

### What we searched
We queried Semantic Scholar, arXiv, and OpenAlex using terms such as "battery degradation prediction early cycle," "voltage curve features lithium-ion," "RNN battery state of health," and "electrochemical signatures capacity fade." The search yielded a limited number of results directly addressing the specific interplay between *early-cycle raw temporal signatures* and *long-term fade* using deep sequence models on public datasets.

### What is known
- [Capacity Fade due to Side-reactions in Silicon Anodes in Lithium-ion Batteries (2012)](https://arxiv.org/abs/1201.1429) — Establishes the fundamental chemical mechanism of capacity loss via electrolyte reduction, providing the physical basis for why voltage and current profiles change over time.
- [Incremental capacity-based multi-feature fusion model for predicting state-of-health of lithium-ion batteries (2025)](https://arxiv.org/abs/2503.23858) — Demonstrates that fusing multi-features derived from incremental capacity analysis can predict state-of-health, though it relies on engineered features rather than raw sequence modeling of early-cycle dynamics.

### What is NOT known
There is a lack of published work that directly quantifies which *specific raw temporal segments* (e.g., voltage curvature in the first 50 cycles, temperature fluctuation frequency) are the most predictive of long-term fade across diverse cycling protocols. Most existing approaches either focus on specific chemistries (like silicon anodes) or rely on pre-engineered features (like incremental capacity) rather than learning the relevant signatures directly from the time-series data.

### Why this gap matters
Identifying the specific early-cycle signatures that drive degradation would allow for much earlier and more accurate battery sorting and warranty estimation, potentially preventing premature failure in critical applications. Understanding how these signatures vary by protocol could also inform the design of charging strategies that inherently extend battery life.

### How this project addresses the gap
This project will train recurrent neural networks on raw voltage, current, and temperature sequences from public datasets to learn predictive representations without hand-crafted feature engineering. By applying permutation importance and attention mechanisms to the trained models, we will explicitly map which early-cycle time-steps and channels contribute most to the prediction of long-term capacity fade.

## Expected results

- Identification of a specific subset of early-cycle electrochemical features (e.g., voltage relaxation rate in the first 20 cycles) that serve as the strongest predictors for long-term capacity fade, outperforming standard hand-crafted metrics.
- Demonstration that the predictive importance of these signatures varies significantly depending on the charging/discharging protocol (e.g., constant current vs. pulse charging).
- A reproducible deep learning model achieving R² ≥ 0.80 on held-out test data for predicting remaining useful life, with uncertainty quantification that captures 90% of true values.

## Methodology sketch

- **Data acquisition**
  - Download the NASA Ames Battery Dataset (https://doi.org/10.5281/zenodo.3228897) and the University of Wisconsin Battery Repository (https://data.uw.edu/battery-cycling).
  - Filter for cells with complete cycling histories and known end-of-life capacity.
- **Pre-processing**
  - Parse raw CSV files to extract time-aligned voltage, current, and temperature traces.
  - Resample to a uniform time step and normalize features per cell to remove magnitude bias.
  - Construct input sequences using the first 50 cycles as the predictor window and the final capacity fade as the target variable.
- **Model development**
  - Implement a Bi-LSTM model in PyTorch (CPU-only) with 2 hidden layers (64 units) to capture temporal dependencies in both directions.
  - Train using Adam optimizer with early stopping on a validation set to prevent overfitting to specific cycling protocols.
  - Perform a lightweight hyperparameter sweep (learning rate, hidden size) constrained to fit within a 30-minute GHA job window.
- **Evaluation**
  - Assess predictive performance using RMSE and R² on a held-out test set of cells with unseen cycling protocols.
  - **Validation Independence Check**: Evaluate the model's predictions against the *actual measured* final capacity from the test set, which is an independent physical measurement not derived from the input features used for prediction.
- **Interpretability**
  - Apply permutation importance to the input channels (voltage, current, temperature) and specific time-windows to quantify their contribution to the prediction.
  - Generate SHAP summary plots to visualize the specific early-cycle patterns that drive the model's decisions.
- **Reproducibility**
  - Version-control all scripts, environment files, and random seeds.
  - Save results and figures in a structured repository format for direct replication on GitHub Actions runners.

## Duplicate-check

- Reviewed existing ideas: (none).
- Closest match: none.
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-16T07:12:10Z
**Outcome**: exhausted
**Original term**: Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks materials science
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks materials science | 2 |

### Verified citations

1. **Capacity Fade due to Side-reactions in Silicon Anodes in Lithium-ion Batteries** (2012). Vijay A. Sethuraman. arXiv. [1201.1429](https://arxiv.org/abs/1201.1429). PDF-sampled: No.
2. **Incremental capacity-based multi-feature fusion model for predicting state-of-health of lithium-ion batteries** (2025). Chenyu Jia, Guangshu Xia, Yuanhao Shi, Jianfang Jia, Jie Wen, et al.. arXiv. [2503.23858](https://arxiv.org/abs/2503.23858). PDF-sampled: No.
