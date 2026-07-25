# Plant Defense Allocation Prediction Pipeline

This project implements a pipeline to predict plant defense allocation from publicly available transcriptomic data.

## Project Structure

- `src/`: Source code for the pipeline
 - `utils/`: Configuration, logging, schemas
 - `data/`: Data acquisition, preprocessing, QC
 - `analysis/`: Differential expression, feature engineering, modeling
- `tests/`: Test suite
 - `unit/`: Unit tests
 - `integration/`: Integration tests
- `data/`: Data directories
 - `raw/`: Raw FASTQ files from NCBI
 - `processed/`: Intermediate processed data
 - `traits/`: Defense trait data
 - `manifests/`: Data provenance manifests
 - `synthetic/`: Synthetic data for validation
- `scripts/`: CLI entry points
- `specs/`: Feature specifications

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Install system tools: `fastp`, `hisat2`, `featureCounts`
3. Run the pipeline: `python scripts/run_pipeline.py --mode synthetic`

## License

MIT License
