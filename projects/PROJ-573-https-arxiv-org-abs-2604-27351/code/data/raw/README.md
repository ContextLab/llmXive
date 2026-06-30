# Raw Dataset Storage

This directory contains raw dataset files downloaded from external sources.

## Downloaded Datasets

- **UCI_HAR**: Human Activity Recognition dataset (time-series)
- **DROP**: Reading Comprehension dataset (text)
- **MUST**: Multi-modal understanding dataset (text/tabular)

## Download Instructions

Datasets are downloaded automatically by running:
```bash
python code/src/data/download.py
```

## Storage Policy

- Files in this directory are NOT committed to version control
- Add large dataset files to `.gitignore`
- Use checksums for integrity verification
- Regular cleanup of unused datasets recommended
