# PROJ-249: The Impact of Digital Decluttering on Cognitive Performance and Well-being

## Overview
This project implements a scientific study pipeline to investigate the effects of digital decluttering on cognitive performance (SART, Ospan) and well-being (PSS-10, PANAS). The pipeline handles data collection, compliance logging, statistical analysis (bootstrapping, Wilcoxon fallback), and reporting.

## Project Structure
```
PROJ-249-the-impact-of-digital-decluttering-on-co/
├── code/ # Core implementation
│ ├── analysis/ # Statistical analysis (bootstrap, effect sizes, etc.)
│ ├── compliance/ # Compliance logging and validation
│ ├── config/ # Environment configuration
│ ├── pipeline/ # Data processing pipelines
│ ├── scoring/ # Psychometric scoring (SART, Ospan, PSS-10, PANAS)
│ ├── setup/ # Project setup utilities
│ ├── utils/ # Utility functions (random seeds, etc.)
│ ├── validation/ # Data validation and instrument checks
│ ├── viz/ # Visualization generation
│ └── report/ # Report generation
├── data/
│ ├── raw/ # Raw data (synthetic or collected)
│ ├── processed/ # Processed and merged data
│ └── compliance/ # Compliance logs
├── results/ # Analysis results and reports
├── tests/ # Unit and contract tests
├── docs/ # Documentation
├── requirements.txt # Python dependencies
├── README.md # This file
└── quickstart.md # Quick start guide
```

## Key Modules

### Scoring (`code/scoring/`)
- `sart.py`: Sustained Attention to Response Task scoring
- `ospan.py`: Operation Span task scoring
- `questionnaires.py`: PSS-10 and PANAS questionnaire scoring
- `id_generator.py`: Pseudonymous participant ID generation

### Analysis (`code/analysis/`)
- `bootstrap_ci.py`: Bootstrap confidence interval calculation
- `change_scores.py`: Pre-post change score calculation
- `effect_sizes.py`: Cohen's d and confidence intervals
- `holm_bonferroni.py`: Multiple comparison correction
- `power_simulation.py`: Monte Carlo power analysis
- `statistical_summary.py`: Aggregate statistical results
- `wilcoxon_fallback.py`: Fallback test if bootstrap fails

### Compliance (`code/compliance/`)
- `parse_logs.py`: Parse daily compliance logs
- `rules_engine.py`: Check compliance rules (≤30 min social media, no news)
- `flag_non_compliant.py`: Flag non-compliant days

### Pipeline (`code/pipeline/`)
- `merge_data.py`: Merge baseline and post-intervention data
- `aggregate_compliance.py`: Aggregate compliance scores

### Validation (`code/validation/`)
- `synthetic_baseline.py`: Generate synthetic baseline data for testing
- `validate_instruments.py`: Validate scoring logic
- `validate_success_criteria.py`: Check results against success criteria

### Visualization (`code/viz/`)
- `generate_plots.py`: Create boxplots and change score distributions

## Dependencies
See `requirements.txt` for the full list. Key packages:
- pandas, numpy, scipy, scikit-learn
- matplotlib, seaborn
- pytest, pyyaml

## Running the Pipeline
See `quickstart.md` for step-by-step instructions.

## API Documentation
Each module in `code/` is documented with docstrings. Use `pydoc` or IDE tooltips to explore.
