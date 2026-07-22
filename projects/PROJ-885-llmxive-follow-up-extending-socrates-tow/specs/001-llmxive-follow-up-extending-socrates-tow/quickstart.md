# Quickstart Guide: Dynamic Socio-Cognitive State Injection

## Overview

This guide validates the end-to-end reproducibility of the **llmXive** pipeline for generating conflict trajectories, executing mediation experiments, and analyzing consensus gap closure.

## Prerequisites

- Python 3.11+
- pip installed
- 8GB+ RAM (for CPU-only inference)
- No GPU required (CPU-only enforced)

## Installation

1. **Clone the repository**
 ```bash
 git clone <repo-url>
 cd llmxive-follow-up-extending-socrates-tow
 ```

2. **Create a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install -r requirements.txt
 ```
 > **Note**: `bitsandbytes` and `flash-attn` are explicitly excluded to ensure CPU-only execution.

## Execution Workflow

The pipeline is executed in the following order:

1. **Generate Trajectories** (US1)
 ```bash
 python -m code.data.generator
 ```
 *Outputs*: `data/processed/trajectories.json`, `data/processed/generation_stats.json`, `data/processed/classifier_training_data.json`

2. **Train Classifier** (US1/US2)
 ```bash
 python -m code.models.classifier
 ```
 *Outputs*: `data/processed/classifier.pkl` (embedded in training data logic or separate)

3. **Run Experiments** (US2)
 ```bash
 python -m code.experiments.runner
 ```
 *Outputs*: `data/processed/experiment_logs.json`

4. **Compute Metrics & Statistics** (US3)
 ```bash
 python -m code.analysis.metrics
 python -m code.analysis.stats
 ```
 *Outputs*: `data/results/statistical_report.json`, `data/results/perf_report.json`

5. **Power Analysis** (T049)
 ```bash
 python -m code.analysis.power_analysis
 ```
 *Outputs*: `data/results/power_analysis_report.json`

## Validation (T044)

To verify end-to-end reproducibility and data integrity, run the validation script:

```bash
python -m code.analysis.quickstart_validator
```

This script:
- Verifies all required directories exist.
- Checks that all core modules import correctly.
- Validates the existence and schema of generated data artifacts.
- Performs a dry-run of the statistical analysis pipeline.
- Generates a `data/results/quickstart_validation_report.json`.

## Expected Outputs

Upon successful completion, the following files should exist:

- `data/processed/trajectories.json`
- `data/processed/experiment_logs.json`
- `data/results/statistical_report.json`
- `data/results/quickstart_validation_report.json`

## Troubleshooting

- **Memory Errors**: Ensure no GPU libraries are installed. The system will log a warning if a GPU is detected but will force CPU usage.
- **Import Errors**: Verify `requirements.txt` was installed completely.
- **Missing Data**: Re-run the generation and experiment scripts if data files are missing.
