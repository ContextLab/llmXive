# The Impact of Incidental Music on Autobiographical Memory Retrieval

## Overview

This project implements an automated scientific pipeline to analyze the relationship between incidental music exposure during adolescence and the vividness/valence of autobiographical memories associated with those tracks.

The pipeline ingests data from the Million Song Dataset (MSD) and the Autobiographical Memory Test (AMT), performs fuzzy matching of memory cues to track titles, computes exposure scores, and fits linear mixed-effects models to test the hypothesis that adolescent exposure predicts memory vividness.

## Prerequisites

- Python 3.11+
- pip
- System dependencies: `build-essential` (for some packages)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PROJ-200-the-impact-of-incidental-music-on-autobi
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Project Structure

```
.
├── code/ # Core implementation
│ ├── data_ingestion.py # Download and filter raw data
│ ├── cue_matching.py # Fuzzy matching of cues to tracks
│ ├── aggregation.py # Aggregate metrics to User-Track level
│ ├── modeling.py # Statistical modeling (MixedLM)
│ ├── main.py # Pipeline orchestration
│ ├── config.py # Configuration and constants
│ └── utils.py # Logging and utilities
├── data/
│ ├── raw/ # Raw downloaded datasets (MSD, AMT)
│ ├── processed/ # Intermediate derived datasets
│ └── final/ # Final analysis results and plots
├── contracts/ # Data schemas
├── tests/ # Unit and integration tests
├── state.yaml # Artifact checksum tracking
└── README.md # This file
```

## Quick Start

To run the full pipeline from raw data ingestion to final results:

```bash
python -m code.main
```

This will:
1. Download/verify datasets (if not present).
2. Filter and compute exposure scores.
3. Match AMT cues to MSD tracks.
4. Aggregate data to User-Track pairs.
5. Fit mixed-effects models and run sensitivity/permutation tests.
6. Generate diagnostic plots and summary tables.

See `quickstart.md` for detailed step-by-step validation.

## Configuration

Configuration is managed in `code/config.py`. Key parameters include:
- `MATCH_RATE_THRESHOLD`: Minimum required cue match rate.
- `LEVENSHTEIN_THRESHOLD`: Maximum allowed edit distance for matching.
- `MIN_LISTENS`: Minimum total listens for a track to be included.
- `ADOLESCENT_WINDOW_START`: Start of adolescence relative to birth year.
- `ADOLESCENT_WINDOW_END`: End of adolescence relative to birth year.

## Data Sources

- **Million Song Dataset (MSD)**: Used for track metadata and listen counts.
- **Autobiographical Memory Test (AMT)**: Used for free-text memory cues and ratings.

*Note: The pipeline requires real data sources. If the canonical URLs are unreachable, the process will fail loudly to prevent fabrication.*

## Output Artifacts

Upon successful completion, the following artifacts are generated in `data/`:

- `processed/ingested_cohort.parquet`: Filtered MSD data with exposure scores.
- `processed/user_track_pairs.parquet`: Aggregated user-track pairs with memory metrics.
- `final/regression_summary.csv`: Model coefficients, standard errors, and p-values.
- `final/sensitivity_analysis.csv`: Results across different matching thresholds.
- `final/permutation_results.csv`: Null distribution statistics.
- `final/plots/`: Diagnostic visualizations (residuals, QQ plots).

## Testing

Run unit tests:
```bash
pytest tests/unit/ -v
```

Run integration tests:
```bash
pytest tests/integration/ -v
```

## Contributing

1. Create a feature branch.
2. Implement changes with corresponding tests.
3. Ensure all existing tests pass.
4. Submit a pull request.

## License

[Insert License Here]
