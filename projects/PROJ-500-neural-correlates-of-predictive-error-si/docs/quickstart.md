# Quick Start Guide

This guide provides step-by-step instructions to run the full pipeline from data ingestion to statistical modeling.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- At least 7GB available RAM
- Network access for dataset download

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PROJ-500-neural-correlates-of-predictive-error-si
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables:
```bash
export DATA_DIR="./data"
export SEED=42
export RAM_LIMIT=7
```

## Running the Pipeline

The pipeline consists of sequential phases. Execute them in order:

### Phase 0: Dataset Validation

```bash
python code/src/data/ingest.py
```

This generates `data/validation_report.json` and determines the analysis mode.

### Phase 3: Data Ingestion and Preprocessing

```bash
python code/setup_project.py
python code/src/data/preprocess.py
```

This downloads raw EEG data, applies filtering/ICA, epochs the data, and generates:
- `data/excluded_subjects.csv` (underpowered subjects)
- Cleaned epoch data

### Phase 4: MMN Calculation and Alignment

```bash
python code/src/data/align.py
python code/src/data/clean.py
python code/src/data/finalize.py
```

This produces:
- `data/accuracy_blocks.csv` (10-trial behavioral blocks)
- `data/interim_lagged_mmns.csv` (lagged MMN-accuracy pairs)
- `data/aligned_data.csv` (final merged dataset)

### Phase 5: Statistical Modeling

```bash
python code/src/analysis/model.py
```

This fits the LME model and generates:
- `analysis/results/model_output.json` (coefficients, p-values, permutation results)

## Verification

Run the test suite to verify all components:

```bash
pytest code/tests/ -v
```

Key tests to check:
- `tests/contract/test_schemas.py`: Schema validation
- `tests/integration/test_alignment.py`: Lagged alignment logic
- `tests/unit/test_t031_permutation_test.py`: Permutation test implementation

## Expected Outputs

After successful execution, verify these files exist:

```
data/
├── validation_report.json
├── excluded_subjects.csv
├── accuracy_blocks.csv
├── interim_lagged_mmns.csv
└── aligned_data.csv

analysis/
└── results/
 └── model_output.json
```

## Troubleshooting

### Memory Errors
If you encounter memory issues, ensure:
- `RAM_LIMIT` environment variable is set correctly
- Streaming is enabled for large datasets
- Raw files are deleted post-processing

### Missing Data
The pipeline will fail loudly if real data cannot be fetched. Check:
- Network connectivity
- OpenNeuro/HuggingFace availability
- Dataset ID validity in metadata

### Schema Validation Failures
If contract tests fail:
- Verify `contracts/*.schema.yaml` files are up to date
- Check that all required columns exist in output CSVs
- Ensure no NaN values in critical columns

## Performance Benchmarks

On a 2-core CPU with 8GB RAM:
- Data ingestion: ~2 hours (depending on dataset size)
- Preprocessing: ~1.5 hours
- Alignment: ~30 minutes
- Modeling: ~1 hour
- **Total**: ~5 hours (within 6-hour constraint)

## Next Steps

After running the pipeline:
1. Review `analysis/results/model_output.json` for significant effects
2. Examine `data/aligned_data.csv` for data quality
3. Run sensitivity analysis via `src/analysis/robustness.py`
4. Generate visualizations (future task)
