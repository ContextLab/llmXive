# Analyzing the Prevalence of Unmaintained Dependencies in Popular NPM Packages

This project implements an automated pipeline to analyze the relationship between dependency maintenance status (measured by age since last release) and security vulnerability counts in popular NPM packages.

## Research Questions

1. Is there a statistically significant correlation between dependency age and vulnerability count?
2. How does this correlation vary across different package categories (frameworks, data, utilities, etc.)?
3. What is the prevalence of unmaintained dependencies in the top NPM packages?

## Methodology

### Data Collection
- Fetch top N packages by weekly download count from NPM registry
- Extract dependency trees (direct and transitive)
- Query GitHub API for last commit/release dates
- Query NPM Audit API for vulnerability counts

### Analysis
- Calculate dependency age in days from last release date
- Compute Spearman rank correlation between age and vulnerability count
- Stratify analysis by package category
- Perform sensitivity analysis on maintenance thresholds

### Quality Controls
- Fail loudly on API errors (no synthetic data fallback)
- Cache all API responses for reproducibility
- Track API success/failure rates
- Validate data integrity at each stage

## Project Structure

```
code/
├── src/
│ ├── models/ # Data models (Pydantic)
│ ├── services/ # API clients (NPM, GitHub, Audit)
│ ├── analysis/ # Statistical analysis modules
│ ├── cli/ # Command-line interfaces
│ ├── utils/ # Utility functions (backoff, cache, etc.)
│ └── config/ # Configuration management
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── data/
│ ├── raw/ # Cached API responses
│ └── processed/ # Analysis outputs
└── docs/
 ├── quickstart.md # Getting started guide
 └── report.md # Generated analysis report
```

## Quick Start

See [docs/quickstart.md](docs/quickstart.md) for detailed setup and execution instructions.

## Key Features

- **Real Data Only**: All analysis is based on actual API measurements; no synthetic data generation
- **Reproducible**: All API responses are cached with checksums for auditability
- **Robust**: Implements exponential backoff and rate limiting for API reliability
- **Comprehensive**: Covers data collection, statistical analysis, stratification, and reporting

## Requirements

- Python 3.11+
- Dependencies listed in `requirements.txt`

## License

This project is part of the llmXive automated science pipeline.
