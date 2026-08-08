# Statistical Analysis of Publicly Available Stack Overflow Question Tags

This project performs statistical analysis on Stack Overflow data to quantify technology growth/decline, visualize time series decomposition, and cluster technologies via co-occurrence.

## Project Structure

```
.
├── code/ # Source code modules
│ ├── analysis/ # Statistical analysis modules
│ ├── data/ # Data download and preprocessing
│ ├── utils/ # Utility functions
│ ├── viz/ # Visualization modules
│ └── scripts/ # Runner scripts
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed analysis data
│ ├── taxonomy/ # Taxonomy and reference files
│ └── events/ # Event reference calendar
├── notebooks/ # Jupyter notebooks for exploration
├── tests/ # Test suites
├── specs/ # Project specifications
└── state/ # Project state tracking
```

## Prerequisites

- Python 3.9+
- pip package manager
- 14GB+ disk space for data processing
- 7GB+ RAM for processing

## Installation

1. Clone the repository
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Quick Start

See `quickstart.md` for step-by-step instructions to reproduce all results.

## Key Features

- **Trend Analysis**: Modified Mann-Kendall test with Theil-Sen slope estimation
- **Decomposition**: STL/Hodrick-Prescott decomposition with seasonality detection
- **Clustering**: Jaccard similarity-based hierarchical clustering
- **External Validation**: GitHub stars and NPM downloads correlation

## Data Sources

- Stack Overflow Developer Survey 2023
- Stack Exchange Data Dump (PostsTags)
- GitHub API (stars)
- NPM API (downloads)

## License

MIT License
