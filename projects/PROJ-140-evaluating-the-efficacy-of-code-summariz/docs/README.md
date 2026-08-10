# Reproducibility Package for Code Summarization Bug Localization Study

This package contains the scripts and anonymized data required to reproduce the statistical analysis of the code summarization study.

## Prerequisites

- Python 3.8+
- Dependencies listed in `requirements.txt`

## Instructions

1. Extract the package:
 ```bash
 tar -xzf reproducibility_package_v1.0.tar.gz
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Run the analysis:
 ```bash
 python code/analysis/run_statistics.py
 ```

4. Verify results match `data/analysis_results/results.csv`.

## Data Exclusions

- `data/consent/` has been explicitly excluded to protect participant privacy (Constitution Principle VI).
- Raw source code from Defects4J is excluded; only stratified ground truth is included.

## License

MIT License
