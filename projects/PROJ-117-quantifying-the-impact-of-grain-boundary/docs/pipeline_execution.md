# Pipeline Execution Guide

This document describes the execution order, dependencies, and validation steps for the grain boundary diffusivity pipeline.

## Execution Order

The pipeline executes in the following sequential order:

```
1. T009: Download raw data
2. T010: Parse geometry
3. T011: Preprocess and validate
4. T016: Run diagnostics
5. T012: Train model
6. T017: Validate model
7. T021: Generate interpretability reports
```

## Dependencies

### Phase Dependencies
- **Phase 1 (Setup)**: No dependencies
- **Phase 2 (Foundational)**: Depends on Phase 1
- **Phase 3 (US1)**: Depends on Phase 2
- **Phase 4 (US2)**: Depends on Phase 3 (requires model artifact)
- **Phase 5 (US3)**: Depends on Phase 3 (requires model artifact)

### Task Dependencies
- T010 requires output from T009
- T011 requires output from T010
- T016 requires output from T011
- T012 requires output from T016
- T017 requires output from T012
- T021 requires output from T012

## Execution Commands

### Single Step Execution

```bash
# Step 1: Download
python code/download.py

# Step 2: Parse
python code/geometry_parser.py

# Step 3: Preprocess
python code/preprocess.py

# Step 4: Diagnostics
python code/diagnostics.py

# Step 5: Train
python code/train.py

# Step 6: Validate
python code/validate.py

# Step 7: Interpret
python code/interpret.py
```

### Full Pipeline Execution

```bash
# Run all steps sequentially
python code/download.py && \
python code/geometry_parser.py && \
python code/preprocess.py && \
python code/diagnostics.py && \
python code/train.py && \
python code/validate.py && \
python code/interpret.py
```

## Validation Steps

### After Each Step

Verify output artifacts exist:

```bash
# After T009
ls -la data/raw/
grep "checksum" data/metadata.yaml

# After T010
ls -la data/processed/parsed_geometry.parquet

# After T011
ls -la data/processed/cleaned_dataset.parquet
python -c "import pandas as pd; df = pd.read_parquet('data/processed/cleaned_dataset.parquet'); print(f'Records: {len(df)}')"

# After T016
ls -la artifacts/reports/collinearity_diagnostic.json

# After T012
ls -la models/best_model.json
ls -la artifacts/reports/training_metrics.json

# After T017
ls -la artifacts/reports/validation_report.json

# After T021
ls -la artifacts/figures/
ls -la artifacts/reports/threshold-variation-table.csv
```

### Error Handling

#### Data Insufficiency
If fewer than 500 valid records are found:
```
Data Insufficiency: {count} < 500. Missing features: {feature_list}
```
Exit code: 1

#### API Failures
If API keys are missing or invalid:
```
ValueError: API key not found for {service}
```
Exit code: 1

#### Memory Errors
If memory limit exceeded:
```
MemoryError: Insufficient memory for operation
```
Exit code: 1

## Parallel Execution Opportunities

The following tasks can run in parallel (marked [P] in tasks.md):
- T013 (Tests for geometry_parser)
- T014 (Tests for preprocess)
- T018 (Tests for diagnostics)
- T019 (Tests for validate)
- T023 (Tests for interpret)

## Performance Monitoring

### Resource Limits
- **RAM**: <7GB
- **CPU**: 2 cores (GitHub Actions free tier)
- **Time**: <6 hours total

### Monitoring Commands

```bash
# Monitor memory usage
/usr/bin/time -v python code/train.py 2>&1 | grep "Maximum resident set size"

# Monitor execution time
time python code/download.py
```

## Troubleshooting

### Common Issues

1. **Missing Output Files**
 - Check that previous step completed successfully
 - Verify file paths in `tasks.md` match actual output paths

2. **Data Insufficiency Errors**
 - Verify API keys are valid
 - Check search keywords match available data
 - Consider expanding search parameters

3. **Import Errors**
 - Ensure all dependencies are installed: `pip install -r requirements.txt`
 - Verify Python version is 3.9+

4. **Memory Errors**
 - Use streaming mode for large datasets
 - Reduce batch sizes if applicable
 - Close other applications to free memory

## State Management

After successful pipeline execution, update `state.yaml`:
```bash
python code/update_state.py
```

This computes SHA-256 hashes for all artifacts and updates the state file.
