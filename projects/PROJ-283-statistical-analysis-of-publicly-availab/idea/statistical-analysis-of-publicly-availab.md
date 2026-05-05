---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction

**Field**: statistics

## Research question

Do deviations from Elo-based expected win probabilities in chess games correlate with observable game features (e.g., opening choice, average move time, material imbalance), and can these deviations identify systematic biases in the Elo rating system?

## Motivation

The Elo rating system is the de facto standard for ranking chess players, yet it assumes a fixed logistic relationship between rating difference and win probability. This project addresses the gap in understanding whether game-level features systematically predict outcome deviations from Elo expectations, which could inform more accurate rating models and reveal strategic factors the Elo system overlooks.

## Related work

- [Searching for the GOAT of tennis win prediction](https://doi.org/10.1515/jqas-2015-0059) — Demonstrates how sports forecasting models can be extended beyond basic rating systems to incorporate additional features, providing an analogous framework for chess outcome prediction.

*Note: Chess-specific literature search returned limited results; this tennis paper is cited as an analogous sports prediction framework.*

## Expected results

We expect to find measurable deviations from Elo-predicted win probabilities that correlate with specific game features (e.g., certain openings, time management patterns). A statistically significant model (p < 0.01) predicting outcome deviations would indicate systematic biases in the Elo system. Evidence will be quantified through regression coefficients, model fit statistics (R², AIC), and cross-validation performance.

## Methodology sketch

- Download Lichess game database (publicly available at https://database.lichess.org/) — select a subset of ~100,000 games with complete rating and move-time data (fits within 7GB RAM).
- Parse game files (PGN format) using Python's `python-chess` library to extract features: opening ECO code, average move time per player, material imbalance at move 10, number of captures, pawn structure complexity.
- Compute expected win probability for each game using standard Elo logistic formula: P = 1 / (1 + 10^((R2-R1)/400)).
- Calculate outcome deviation: actual result (1/0.5/0) minus expected probability.
- Fit multiple regression models (linear, logistic, ridge) with game features as predictors and outcome deviation as target variable.
- Perform k-fold cross-validation (k=5) to assess generalizability and avoid overfitting.
- Apply statistical significance tests (t-tests on coefficients, F-test for model fit) using Python's `statsmodels` library.
- Generate diagnostic plots: residual plots, feature importance rankings, predicted vs. actual deviation scatterplots.
- All computation completed within 6-hour GHA job using `pandas`, `scikit-learn`, and `matplotlib` (no GPU required).

## Duplicate-check

- Reviewed existing ideas: none provided in input.
- Closest match: N/A — no existing ideas to compare.
- Verdict: NOT a duplicate
