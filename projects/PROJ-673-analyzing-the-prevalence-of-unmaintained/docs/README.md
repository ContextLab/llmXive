# Analyzing the Prevalence of Unmaintained Dependencies in Popular NPM Packages

This project implements an automated research pipeline to analyze the relationship between dependency age and vulnerability prevalence in popular NPM packages.

## Project Structure

```
.
├── code/
│ ├── src/
│ │ ├── analysis/ # Statistical analysis modules
│ │ ├── cli/ # Command-line interface scripts
│ │ ├── config/ # Configuration management
│ │ ├── models/ # Data models (Pydantic)
│ │ ├── services/ # API clients (NPM, GitHub, Audit)
│ │ └── utils/ # Utility functions
│ ├── tests/ # Unit and integration tests
│ └── setup_project_structure.py
├── data/
│ ├── raw/ # Cached API responses
│ └── processed/ # Processed data and results
├── docs/ # Documentation
├── figures/ # Generated visualizations
├── requirements.txt # Python dependencies
└── README.md
```

## Key Features

- **Automated Data Collection**: Fetches data from NPM, GitHub, and npm audit APIs
- **Dependency Resolution**: Recursively resolves direct and transitive dependencies
- **Age Calculation**: Computes dependency age based on last release date
- **Statistical Analysis**: Spearman correlation between age and vulnerability density
- **Stratified Analysis**: Categorizes packages and analyzes correlations per category
- **Sensitivity Analysis**: Tests robustness across different "unmaintained" thresholds
- **Comprehensive Reporting**: Generates detailed reports with visualizations

## Research Questions

1. Is there a correlation between dependency age and vulnerability prevalence?
2. Does this correlation vary by package category?
3. How robust are the findings across different definitions of "unmaintained"?

## Methodology

1. **Data Collection**: Retrieve top NPM packages by weekly downloads
2. **Dependency Extraction**: Flatten dependency trees (direct + transitive)
3. **Metadata Gathering**: Fetch last commit/release dates and vulnerability counts
4. **Age Calculation**: Compute days since last release (null if missing)
5. **Correlation Analysis**: Spearman rank correlation (age vs. vulnerability density)
6. **Stratification**: Group by package category (framework, data, utility, etc.)
7. **Visualization**: Generate scatter plots and histograms
8. **Reporting**: Compile findings into a comprehensive report

## Getting Started

See [quickstart.md](quickstart.md) for detailed instructions on running the pipeline.

## Dependencies

- Python 3.11+
- requests
- pandas
- scipy
- statsmodels
- matplotlib
- pyyaml
- pydantic

## License

This project is licensed under the MIT License.
