# Architecture Documentation

## High-Level Design

The project follows a linear pipeline architecture with clear separation of concerns:

1. **Data Acquisition Layer**: Downloads and validates raw datasets
2. **Generation Layer**: Produces code samples using LLMs
3. **Analysis Layer**: Computes metrics from generated code
4. **Statistical Layer**: Performs hypothesis testing
5. **Reporting Layer**: Generates visualizations and documentation

## Module Responsibilities

### `code/download_data.py`
- Downloads HumanEval dataset from HuggingFace
- Verifies SHA256 checksums
- Performs stratified sampling based on human pass-rate quartiles
- Outputs: `data/raw/humaneval.json`

### `code/generate_code.py`
- Loads `Salesforce/codegen-mono-350M` model
- Generates code completions for HumanEval tasks
- Implements 3-retry logic for failed generations
- Supports sensitivity analysis with CodeLlama models
- Outputs: `data/generated/code_samples.json`

### `code/analyze_metrics.py`
- Computes Cyclomatic Complexity via `radon`
- Computes Halstead Volume via `radon`
- Executes pytest for pass rate determination
- Executes pytest --cov for branch coverage
- Handles execution failures gracefully (records `[deferred]`)
- Outputs: `data/analysis/metrics.json`

### `code/statistical_tests.py`
- Wilcoxon Signed-Rank Test for continuous metrics
- McNemar's Test for binary pass rates
- Fisher's Exact Test for exploratory unpaired checks
- Permutation Test for paired coverage data
- A priori and post-hoc power analysis
- Outputs: `data/analysis/statistical_results.json`

### `code/report_generator.py`
- Generates histograms and boxplots via `matplotlib`
- Compiles Jinja2 template into Markdown report
- Includes sensitivity analysis comparisons
- Outputs: `results_report.md`, `results/figures/*.png`

### `code/utils.py`
- Centralized logging with task ID tracking
- SHA256 checksum computation and verification
- Utility functions for directory management

### `code/artifact_manager.py`
- Tracks artifact hashes in `state/artifact_hashes.yaml`
- Ensures data integrity across pipeline runs
- Implements versioned artifact storage

## Data Flow

```
[HumanEval] → download_data.py → [Raw Data]
 ↓
 stratified_sample()
 ↓
 [Sampled Tasks]
 ↓
 generate_code.py
 ↓
 [Generated Code]
 ↓
 analyze_metrics.py
 ↓
 [Metrics JSON]
 ↓
 statistical_tests.py
 ↓
 [Statistical Results]
 ↓
 report_generator.py
 ↓
 [Final Report + Figures]
```

## State Management

The `state/` directory tracks:
- `artifact_hashes.yaml`: SHA256 hashes of all outputs
- `citations.yaml`: Reference validation state
- `model_availability.json`: CodeLlama availability status
- `metrics_versions.yaml`: Versioned metrics file index
- `collision_log.json`: Merge conflict resolution log

## Error Handling Strategy

- **Data Download**: Fails loudly if verified source is unreachable (no synthetic fallback)
- **Code Generation**: Logs failures to `errors.log`, marks samples as missing
- **Metric Analysis**: Records `[deferred]` for failed executions, continues processing
- **Statistical Tests**: Handles zero-variance cases, logs warnings

## Parallelization Opportunities

- **Phase 1 (Setup)**: All tasks can run in parallel
- **Phase 2 (Foundational)**: Independent utilities can be parallelized
- **User Stories**: Once foundation is complete, US1, US2, US3 can run in parallel
- **Within US1**: Code generation for different tasks can be parallelized

## Dependencies

See `code/requirements.txt` for pinned dependencies:
- `datasets`: HuggingFace dataset loading
- `transformers`: Model loading and inference
- `radon`: Code metric analysis
- `pytest`: Test execution
- `coverage`: Branch coverage measurement
- `scipy`: Statistical tests
- `matplotlib`: Visualization
- `jinja2`: Report templating
- `pyyaml`: State management
