# llmXive: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Overview

This project investigates the relationship between dietary fiber intake and gut microbiome composition using data from the American Gut Project (AGP) and the UK Biobank (UKBB). The pipeline performs data ingestion, harmonization, compositional transformation (CLR), and statistical correlation analysis (MaAsLin2, Spearman) with cross-cohort validation.

## Project Structure

```
code/
├── src/
│ ├── main.py # Main entry point
│ ├── utils/
│ │ ├── logger.py # Logging configuration
│ │ └── power_analysis.py # Statistical power calculations
│ ├── ingestion/
│ │ ├── agp_loader.py # AGP data ingestion
│ │ ├── ukbb_loader.py # UKBB data ingestion
│ │ └── harmonizer.py # Data harmonization
│ ├── preprocessing/
│ │ ├── id_generator.py # Sample ID generation
│ │ ├── covariate_handler.py # MICE imputation
│ │ └── clr_transform.py # CLR transformation
│ └── analysis/
│ ├── correlation_maaslin2.py
│ └── validation_cross_cohort.py
├── tests/
│ ├── contract/ # Schema contract tests
│ ├── integration/ # Integration tests
│ └── unit/ # Unit tests
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed data
└── requirements.txt

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Run the pipeline:
 ```bash
 python src/main.py
 ```

## Usage

### Data Ingestion
Download and harmonize data from AGP and UKBB:
```bash
python src/ingestion/run_ingestion_pipeline.py
```

### Preprocessing
Apply CLR transformation:
```bash
python src/preprocessing/clr_transform.py --input data/processed/merged_harmonized.tsv --output data/processed/clr_transformed.tsv
```

### Analysis
Run correlation analysis:
```bash
python src/analysis/correlation_maaslin2.py --input data/processed/clr_transformed.tsv --output data/processed/results/association_results.tsv
```

## Testing

Run all tests:
```bash
pytest
```

Run specific test suites:
```bash
pytest tests/unit/
pytest tests/contract/
pytest tests/integration/
```

## License

This project is licensed under the terms specified in the LICENSE file.

## Contact

For questions, please contact the project maintainers.
