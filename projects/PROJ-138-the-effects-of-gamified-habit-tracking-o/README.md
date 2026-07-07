# The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

**Project ID**: PROJ-138-the-effects-of-gamified-habit-tracking-o

## Overview

This research project investigates the impact of gamified habit-tracking applications on long-term behavioral change. By analyzing longitudinal data from users who utilize gamified tools versus those who do not, we aim to quantify the effectiveness of gamification elements in sustaining adherence to behavioral goals.

The study employs a mixed-methods approach, combining:
- **Mixed-effects logistic regression** to model adherence probabilities while accounting for individual user variance.
- **Survival analysis (Kaplan-Meier and Cox Proportional Hazards)** to assess dropout rates and time-to-event.
- **Robustness validation** via bootstrapping and sensitivity analysis to ensure findings are stable across different adherence thresholds and sample variations.

## Key Research Questions

1. Does the use of gamified habit-tracking apps significantly improve long-term adherence compared to non-gamified methods?
2. How do personality traits (specifically Conscientiousness and Need for Achievement) moderate the effect of gamification?
3. What is the probability of dropout over time for different user segments?

## Project Structure

```text
.
├── code/
│ ├── analysis/ # Statistical modeling, survival analysis, robustness checks
│ ├── data/ # Data ingestion, validation, aggregation, synthetic generation
│ ├── reports/ # Report generation and visualization scripts
│ ├── utils/ # Configuration, logging, versioning, setup utilities
│ └── tests/ # Unit and integration tests for pipeline components
├── data/
│ ├── raw/ # Raw input data (synthetic or external)
│ ├── processed/ # Cleaned and aggregated data ready for analysis
│ └── consent/ # Consent records (real or synthetic verification)
├── data/consent/ # Consent artifacts
├── data/raw/ # Raw data storage
├── data/processed/ # Processed data storage
├── data/reports/ # Final analysis reports
├── specs/ # Feature specifications and user stories
├── tests/ # Test suite
├── requirements.txt # Python dependencies
├── README.md # Project overview
└── quickstart.md # Execution instructions
```

## Dependencies

This project requires Python 3.11+. Install dependencies via:

```bash
pip install -r requirements.txt
```

Key libraries include:
- `pandas`, `numpy`: Data manipulation
- `statsmodels`: Mixed-effects modeling
- `lifelines`: Survival analysis
- `pingouin`: Statistical tests (Cronbach's alpha)
- `scikit-learn`: Data preprocessing
- `matplotlib`, `seaborn`: Visualization

## Usage

See [`quickstart.md`](quickstart.md) for detailed execution steps, including:
- Synthetic data generation (if real data is unavailable)
- Consent verification procedures
- Running the full analysis pipeline
- Generating the final HTML report

## Disclaimer

**Findings are associational, not causal.** The data analyzed in this project is observational. While statistical controls are applied, causality cannot be definitively established without randomized controlled trials.

## License

This research code is provided for educational and scientific purposes.
