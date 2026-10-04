# llmXive: Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

## Project Overview

This project investigates whether topological properties of structural brain networks (derived from diffusion MRI) predict the prevalence, stability, and switching speed of recurrent activity patterns (derived from fMRI).

**Important**: This study is **associational** in nature. We do not claim causal relationships. All findings should be interpreted as statistical associations between structural connectivity and dynamic functional states.

## Quickstart

See `docs/quickstart.md` for detailed instructions on:
- Environment setup
- Data fetching (HCP OpenNeuro)
- Running the full pipeline
- Generating reports

## Project Structure

```
.
├── code/ # Source code
│ ├── config.py # Configuration and hyperparameters
│ ├── main.py # Main pipeline orchestrator
│ ├── preprocess/ # Data loading and preprocessing
│ │ ├── loader.py # HCP data loading utilities
│ │ ├── structural.py # Structural graph metric calculation
│ │ └── functional.py # Dynamic functional state extraction
│ ├── analysis/ # Statistical analysis
│ │ ├── correlation.py # Structure-function correlation
│ │ ├── robustness.py # Sensitivity analysis
│ │ ├── tractography_sensitivity.py
│ │ └── tractography_correlation_sensitivity.py
│ └── reports/ # Report generation
│ ├── generate_report.py
│ └── validate_report.py
├── data/ # Data storage
│ ├── raw/ # Raw HCP data (downloaded)
│ ├── processed/ # Processed metrics and results
│ └── logs/ # Execution logs
├── contracts/ # Schema definitions
├── tests/ # Test suite
├── docs/ # Documentation
│ ├── quickstart.md
│ └── README.md # This file
├── requirements.txt # Python dependencies
└── pyproject.toml # Project configuration
```

## Key Features

### 1. Structural Graph Metrics (US1)
- Global efficiency
- Average clustering coefficient
- Modularity
- Sensitivity analysis across graph density thresholds (0.10, 0.15, 0.20)

### 2. Dynamic Functional States (US1)
- Sliding-window correlation (window_length=30 TR, step=1 TR)
- Leave-One-Out (LOO) K-Means centroid generation for statistical independence
- State assignment and metric calculation (dwell time, visited states)

### 3. Structure-Function Correlation (US2)
- Normality testing (Shapiro-Wilk)
- Conditional correlation (Pearson vs Spearman)
- Benjamini-Hochberg FDR correction (q=0.05)

### 4. Robustness Analysis (US3)
- Window length sensitivity (20, 25, 30, 35 TR)
- Graph density sensitivity
- Tractography confidence threshold sensitivity (0.0, 0.2, 0.4, 0.6, 0.8)

### 5. Tractography Noise Sensitivity (Reviewer Revision)
- Addresses false-positive rates in diffusion MRI tractography (Yeh et al., 2018) [UNRESOLVED-CLAIM: c_86395701 — status=not_enough_info]
- Varies tractography confidence thresholds to assess robustness
- Explicitly reports if findings vanish at high confidence thresholds

## Data Sources

- **HCP OpenNeuro**: Raw dMRI and fMRI data fetched programmatically
- No synthetic or placeholder data is used

## Dependencies

See `requirements.txt` for the complete list:
- nilearn
- networkx
- scikit-learn
- pandas
- numpy
- scipy
- statsmodels
- pyyaml

## Running the Pipeline

1. **Setup**: `python code/setup_directory_structure.py`
2. **Fetch Data**: Follow instructions in `docs/quickstart.md`
3. **Run Pipeline**: `python code/main.py`
4. **Generate Report**: `python code/reports/generate_report.py`
5. **Validate Report**: `python code/reports/validate_report.py`

## Configuration

Key hyperparameters are defined in `code/config.py`:
- `WINDOW_LENGTH_BASELINE = 30` (TRs)
- `WINDOW_LENGTH_VALIDATION = [20, 25, 30, 35]` (TRs)
- `K_MEANS_K = 5`
- `DENSITY_THRESHOLD_BASELINE = 0.15`
- `DENSITY_THRESHOLD_VARIATIONS = [0.10, 0.15, 0.20]`
- `TRACTOGRAPHY_CONFIDENCE_THRESHOLDS = [0.0, 0.2, 0.4, 0.6, 0.8]`

## Testing

Run the test suite:
```bash
pytest tests/
```

Key test modules:
- `tests/unit/test_structural.py` - Graph metric calculations
- `tests/unit/test_functional.py` - LOO K-Means independence
- `tests/unit/test_correlation.py` - Normality and FDR correction
- `tests/unit/test_tractography.py` - Confidence thresholding
- `tests/integration/test_single_subject.py` - End-to-end pipeline

## Methodological Notes

### Leave-One-Out (LOO) Independence
To ensure statistical independence, centroids for subject `i` are computed exclusively from subjects `j != i`. This deviates from a "common set" approach to satisfy Constitution Principle VI.

### Associational Framing
All reports explicitly use "associational" language. No causal claims are made. See `code/reports/audit_associational_language.py` for automated compliance checking.

### Tractography False-Positive Sensitivity
Per reviewer concern (john-von-neumann-simulated), we perform a sensitivity analysis varying tractography confidence thresholds. If findings vanish at high confidence thresholds, the report explicitly states that original findings may be driven by tractography artifacts.

## License

This project is part of the llmXive automated science pipeline.

## Contributing

1. Create a feature branch
2. Implement changes
3. Run tests
4. Submit a pull request

## Contact

For questions, refer to the project maintainers or open an issue.
