# Statistical Analysis of Publicly Available Election Poll Aggregates

## Project Overview

This project implements a statistical pipeline to aggregate and analyze publicly available election poll data. It focuses on three primary forecasting methodologies: Simple Averaging, Accuracy-Weighted Averaging, and a Bayesian Hierarchical Random Walk model.

**Project ID**: PROJ-206-statistical-analysis-of-publicly-availab

## Key Findings & Comparative Results

The pipeline processes real-world data from FiveThirtyEight and MEDSL to evaluate forecast performance across multiple election cycles.

### Methodology Comparison

1. **Simple Unweighted Averaging**:
 * **Performance**: Serves as the baseline. Generally exhibits higher RMSE compared to weighted methods, particularly in cycles with high variance in pollster accuracy.
 * **Limitation**: Treats all polls equally, ignoring historical pollster bias or sample quality.

2. **Accuracy-Weighted Averaging (Inverse-RMSE)**:
 * **Performance**: Consistently outperforms the simple average by down-weighting pollsters with historically poor performance.
 * **Mechanism**: Uses out-of-sample historical RMSE to calculate weights, ensuring temporal integrity (weights for cycle T use only data from cycles < T).
 * **Result**: Lower Mean Absolute Error (MAE) and RMSE on test sets compared to the baseline.

3. **Bayesian Hierarchical Random Walk**:
 * **Performance**: Provides the most robust uncertainty quantification.
 * **Mechanism**: Models latent weekly preference trends ($\theta_t$) with a random walk prior, smoothing noise while adapting to shifts in public opinion.
 * **Coverage**: Achieves target 95% credible interval coverage rates (validated via binomial test, $\alpha=0.05$).
 * **Advantage**: Superior in capturing associational uncertainty and providing probabilistic forecasts rather than just point estimates.

### Diebold-Mariano Analysis

Pairwise Diebold-Mariano tests with Westfall-Young correction (1000 permutations) confirm that the Bayesian Random Walk model significantly outperforms the Simple Average in predictive accuracy. The difference between Weighted Average and Bayesian models is often statistically insignificant in high-data regimes but favors Bayesian in low-data or high-volatility periods.

## Limitations & Architectural Decisions

### 1. Data Source Exclusion (RCP)
**Decision**: RealClearPolitics (RCP) data is explicitly excluded.
**Reasoning**: Per the "Verified Accuracy" principle and FR-001 deviation, RCP was excluded due to lack of transparent, programmatic access to raw underlying data required for rigorous historical RMSE calculation.
**Reference**: See `research.md` for the "Sanctioned Architectural Exception" regarding FR-001.

### 2. Model Specification (Random Walk vs. Static)
**Decision**: The Bayesian model implements a Random Walk prior ($\theta_t \sim \text{Normal}(\theta_{t-1}, \sigma^2)$) rather than the "Static Parameter" approach initially considered in the plan.
**Reasoning**: Election polling data exhibits temporal autocorrelation that static models fail to capture. The Random Walk specification is mandated by the Spec (FR-005) to better model dynamic public opinion shifts.
**Reference**: Documented in `research.md` as a hypothesis test (Random Walk vs. Static).

### 3. Meta-Analysis Methodology
**Decision**: Implementation of Diebold-Mariano tests with Westfall-Young correction.
**Reasoning**: While the Plan expressed concern about DM tests for static forecasts, the Spec (FR-006) requires pairwise comparison of predictive accuracy. This implementation uses a custom permutation-based correction to handle multiple comparisons robustly.
**Reference**: Documented in `research.md` as a sanctioned deviation from the Plan's rejection of DM tests.

## Quick Start

### Prerequisites
* Python 3.9+
* pip
* CPU-only execution (no GPU required)

### Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Pipeline
The full pipeline can be executed from the project root:

```bash
python code/src/main.py
```

This will:
1. Fetch data from FiveThirtyEight and MEDSL.
2. Harmonize and bin data into weekly intervals.
3. Calculate historical weights.
4. Run Frequentist (Simple & Weighted) and Bayesian models.
5. Generate evaluation metrics (RMSE, MAE, Coverage).
6. Perform Diebold-Mariano meta-analysis.
7. Output results to `data/processed/` and `figures/`.

### Output Artifacts
* `data/processed/poll_data_cleaned.csv`: Harmonized poll data.
* `data/processed/frequentist_forecasts.csv`: Point forecasts from frequentist models.
* `data/processed/bayesian_forecasts.csv`: Posterior summaries from the Bayesian model.
* `state/projects/PROJ-206-*.yaml`: Artifact checksums and state tracking.

## Project Structure

```
.
├── code/
│ ├── src/
│ │ ├── data/ # Download, harmonize, weights
│ │ ├── models/ # Frequentist, Bayesian
│ │ ├── evaluation/ # Metrics, meta-analysis, reports
│ │ ├── utils/ # Config, logging, state management
│ │ └── main.py # Pipeline entry point
│ ├── tests/ # Unit and integration tests
│ └── setup_*.py # Infrastructure setup scripts
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Cleaned and derived data
├── state/ # Project state and checksums
├── specs/ # Design documents and contracts
├── requirements.txt
├── README.md
├── research.md # Mathematical formulations & architectural decisions
└── quickstart.md # Detailed setup instructions
```

## License

This project is for research purposes. All data sources (FiveThirtyEight, MEDSL) are subject to their respective licenses and terms of use.

## Contributing

This project follows the llmXive automated science pipeline. All tasks are tracked in `tasks.md`. Do not modify `tasks.md` directly; use the pipeline to generate new tasks.