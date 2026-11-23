# The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

## Project Overview

This research project investigates the impact of gamified habit-tracking applications on long-term behavioral adherence. Using a longitudinal dataset of user interactions, we analyze the relationship between gamification status, personality traits (specifically Conscientiousness), and habit adherence over time.

The study employs mixed-effects logistic regression, survival analysis, and robustness validation (bootstrapping) to determine if gamification significantly improves adherence, particularly for users with varying levels of conscientiousness.

## Research Questions

1. Does gamification status significantly predict habit adherence?
2. Does Conscientiousness moderate the effect of gamification on adherence?
3. What is the survival rate (time to dropout) for gamified vs. non-gamified users?
4. Are the findings robust across different adherence thresholds and bootstrap iterations?

## Project Structure

```
PROJ-138-the-effects-of-gamified-habit-tracking-o/
├── code/
│ ├── analysis/ # Statistical modeling, survival analysis, robustness checks
│ ├── data/ # Data ingestion, validation, aggregation, models
│ ├── reports/ # Report generation and visualization
│ ├── utils/ # Configuration, logging, versioning
│ ├── scripts/ # Pipeline orchestration scripts
│ └── tests/ # Unit and integration tests
├── data/
│ ├── raw/ # Raw input data (synthetic or real)
│ ├── processed/ # Aggregated and cleaned data
│ ├── consent/ # Consent documentation
│ └── reports/ # Final analysis reports
├── contracts/ # Data schemas and validation contracts
├── logs/ # Pipeline execution logs
├── README.md # This file
├── quickstart.md # Execution instructions
├── requirements.txt # Python dependencies
└── state.yaml # Artifact versioning and hashes
```

## Dependencies

This project requires Python 3.11+. Install dependencies using:

```bash
pip install -r requirements.txt
```

Key dependencies include:
- `pandas`, `numpy`: Data manipulation
- `statsmodels`: Mixed-effects modeling
- `lifelines`: Survival analysis
- `pingouin`: Statistical tests (Cronbach's alpha)
- `scikit-learn`: VIF calculation
- `matplotlib`, `seaborn`: Visualization

## Quick Start

To run the full analysis pipeline, refer to the [quickstart.md](quickstart.md) guide.

```bash
bash quickstart.sh
```

This will:
1. Generate synthetic data (if real data is not present)
2. Validate consent and schema
3. Aggregate daily logs into weekly bins
4. Fit mixed-effects and survival models
5. Run robustness checks
6. Generate the final HTML report

## License

This research project is for educational and scientific purposes.
