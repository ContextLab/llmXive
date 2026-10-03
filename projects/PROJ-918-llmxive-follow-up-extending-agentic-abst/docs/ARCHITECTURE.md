# Architecture Documentation: llmXive Agentic Abstention Pipeline

## System Overview

The llmXive pipeline is a modular research framework designed to investigate agentic abstention. It follows a clear separation of concerns between data processing, model training, simulation, and analysis.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Data Layer │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │ Ingest │→ │ Features │→ │ Preprocess │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ │
│ ↓ ↓ ↓ │
│ Raw Benchmark Feature Matrix Clean Dataset │
└─────────────────────────────────────────────────────────────┘
 ↓
┌─────────────────────────────────────────────────────────────┐
│ Model Layer │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │ Oracle │ │ Train │ │ Evaluate │ │
│ │ Solver │ │ Meta-Critic│ │ Simulation │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ │
│ ↓ ↓ ↓ │
│ Ground Truth Trained Model Simulation Results │
└─────────────────────────────────────────────────────────────┘
 ↓
┌─────────────────────────────────────────────────────────────┐
│ Analysis Layer │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │ Stats │ │ Survival │ │ Sensitivity │ │
│ │ Tests │ │ Analysis │ │ Analysis │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ │
│ ↓ ↓ ↓ │
│ P-values, Kaplan-Meier Threshold │
│ Effect Sizes Curves Sensitivity │
└─────────────────────────────────────────────────────────────┘
 ↓
┌─────────────────────────────────────────────────────────────┐
│ Reporting Layer │
│ ┌─────────────┐ ┌─────────────┐ │
│ │ Baseline │ │ Statistical │ │
│ │ Comparison │ │ Report Gen │ │
│ └─────────────┘ └─────────────┘ │
│ ↓ ↓ │
│ JSON Metrics Markdown Report │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### Data Layer

#### `code/data/ingest.py`
- **Purpose**: Fetch and verify real benchmark data
- **Strategy**: Primary fetch from Hugging Face benchmark, fallback to synthetic simulator only if real data unavailable
- **Output**: Raw Parquet file with interaction trajectories
- **Key Functions**: `fetch_benchmark_data()`, `verify_data_integrity()`

#### `code/data/extract_features.py`
- **Purpose**: Transform raw trajectories into feature vectors
- **Features Extracted**:
 - Search count (number of tool calls)
 - Error frequency (ratio of failed attempts)
 - Token usage (cumulative tokens)
 - Turn number (interaction step)
 - Query-context embedding distance (semantic proxy)
- **Key Functions**: `extract_features()`, `compute_query_context_distance()`

#### `code/data/preprocess.py`
- **Purpose**: Clean and validate dataset
- **Logic**: Mean imputation for missing values, halt if >5% missing critical variables
- **Output**: Cleaned dataset and validation report
- **Key Functions**: `perform_mean_imputation()`, `validate_dataset()`

### Model Layer

#### `code/oracle/solver.py`
- **Purpose**: Generate ground truth abstention labels
- **Method**: Bounded exhaustive search with limited token budget
- **Output**: Binary labels indicating optimal abstention points
- **Key Functions**: `BoundedExhaustiveSolver`, `run_oracle_on_dataset()`

#### `code/models/train_meta_critic.py`
- **Purpose**: Train the Meta-Critic classifier
- **Algorithm**: XGBoost (CPU-optimized)
- **Input**: Feature matrix from preprocessing
- **Output**: Trained model and performance metrics
- **Key Functions**: `train_model()`, `evaluate_model()`

#### `code/simulation/simulation_framework.py`
- **Purpose**: Execute agent interaction loops
- **Modes**:
 - Full-context baseline (reference CONVOLVE)
 - Meta-Critic guided (abstention predictions)
- **Key Functions**: `run_simulation()`, `evaluate_state()`

### Analysis Layer

#### `code/analysis/statistical_tests.py`
- **Purpose**: Validate statistical significance
- **Tests**: Mann-Whitney U, Kolmogorov-Smirnov, VIF for collinearity
- **Output**: P-values, effect sizes, collinearity diagnostics
- **Key Functions**: `perform_mann_whitney_u_test()`, `calculate_cohens_d()`

#### `code/analysis/survival_analysis.py`
- **Purpose**: Analyze token consumption as survival data
- **Method**: Kaplan-Meier estimator, Log-Rank test
- **Output**: Survival curves, hazard ratios
- **Key Functions**: `perform_kaplan_meier_analysis()`, `generate_survival_report()`

#### `code/analysis/sensitivity_analysis.py`
- **Purpose**: Evaluate decision threshold robustness
- **Method**: Sweep thresholds, calculate FP/FN rates
- **Output**: Sensitivity curves, optimal threshold recommendations
- **Key Functions**: `run_sensitivity_sweep()`, `plot_sensitivity_curve()`

### Reporting Layer

#### `code/analysis/generate_baseline_comparison.py`
- **Purpose**: Compare Meta-Critic vs. baseline performance
- **Metrics**: Token reduction %, latency, accuracy
- **Output**: JSON comparison file

#### `code/analysis/generate_statistical_report.py`
- **Purpose**: Compile all analysis into human-readable report
- **Content**: P-values, effect sizes, survival analysis, sensitivity plots
- **Output**: Markdown report with embedded figures

## Data Flow

1. **Ingestion**: Raw benchmark data → `data/raw/`
2. **Feature Extraction**: Raw data → Feature matrix → `data/processed/features.parquet`
3. **Preprocessing**: Feature matrix → Cleaned matrix → `data/processed/features_clean.parquet`
4. **Label Generation**: Oracle solver → Ground truth labels → `data/processed/labels.parquet`
5. **Training**: Cleaned data + Labels → Trained model → `models/`
6. **Simulation**: Model + Baseline → Simulation results → `data/results/`
7. **Analysis**: Simulation results → Statistical insights → `data/results/`
8. **Reporting**: All results → Final report → `data/results/statistical_report.md`

## Configuration Management

All configurable parameters are centralized in `code/config.py`:
- File paths
- Random seeds
- Hyperparameters
- Simulation settings

Configuration can be loaded from:
- `config.yaml` file
- Environment variables
- Command-line arguments

## Logging Strategy

- Centralized logging via `code/logging_config.py`
- Log levels: DEBUG, INFO, WARNING, ERROR
- Output: Console and file (`logs/pipeline.log`)
- Special attention to abstention events for auditability

## Error Handling

- **Data Fetch Failures**: Explicit error messages, no silent fallbacks
- **Validation Failures**: Halt execution with detailed reports
- **Model Training Errors**: Clear exception messages with suggested fixes
- **Simulation Errors**: Graceful degradation with partial results logging

## Scalability Considerations

- **CPU-Only Design**: Optimized for free CI environments
- **Memory Constraints**: Streaming support for large datasets
- **Time Limits**: Training constrained to <6 hours on 2-core CPU
- **Parallelization**: Independent tasks can run in parallel (e.g., US1, US2, US3)

## Security and Privacy

- No full semantic context text stored in processed features
- Data integrity verified via checksums
- Reproducible experiments via fixed random seeds
