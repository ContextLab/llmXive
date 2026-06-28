# Quickstart Guide: Evaluating the Impact of Code Duplication on LLM Code Understanding

This guide provides step-by-step instructions for setting up and running the complete
research pipeline. All commands assume you are in the project root directory:
`projects/PROJ-261-evaluating-the-impact-of-code-duplication/`

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- At least 8GB RAM for model inference (7GB limit enforced)
- Internet connection for dataset download (500MB subset)
- Git (for version control)

## Installation

1. **Clone and navigate to the project** (if not already done):
 ```bash
 cd projects/PROJ-261-evaluating-the-impact-of-code-duplication/
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

 Required packages (see `requirements.txt`):
 - `datasets` - HuggingFace dataset streaming
 - `transformers` - Model loading and inference
 - `bitsandbytes` - 8-bit quantization
 - `scipy` - Statistical correlation analysis
 - `matplotlib` - Visualization generation
 - `pytest` - Testing framework

4. **Install development tools** (optional, for linting):
 ```bash
 pip install black flake8 isort
 pre-commit install
 ```

## Configuration

All configuration parameters are defined in `code/config.py`. Key parameters include:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `RANDOM_SEED` | 42 | Random seed for reproducibility |
| `MEMORY_LIMIT_MB` | 7000 | Maximum memory usage in MB |
| `MAX_RUNTIME_SECONDS` | 86400 | Maximum runtime (24 hours) |
| `MIN_VALID_SEGMENTS` | 1000 | Minimum valid code segments required |
| `CORRELATION_METHOD` | spearman | Correlation method (spearman/pearson) |
| `SIGNIFICANCE_THRESHOLD` | 0.05 | P-value threshold for significance |
| `FIGURE_FORMAT` | png | Output figure format (png/pdf) |
| `FIGURE_DPI` | 300 | Figure resolution |
| `CHECKSUM_ALGORITHM` | sha256 | Checksum algorithm for artifacts |
| `DATASET_NAME` | codeparrot/github-code | HuggingFace dataset name |
| `MODEL_NAME` | Salesforce/codegen-350M-mono | Model for perplexity computation |
| `QUANTIZATION_BITS` | 8 | Model quantization bits |
| `STREAMING_ENABLED` | true | Enable dataset streaming |
| `PII_SCAN_ENABLED` | true | Enable PII pattern scanning |
| `CLONE_THRESHOLDS` | [0.7, 0.8, 0.9] | Clone detection thresholds for sensitivity analysis |

To modify configuration, edit `code/config.py` directly. Changes will be reflected
across all pipeline components.

## Running the Pipeline

The pipeline executes in six stages. Each stage produces intermediate outputs that
feed into the next stage.

### Stage 1: Data Download (T018)

```bash
python code/data_loader.py
```

**Output**: `data/raw/github-code-sample.csv` (500MB subset from codeparrot/github-code)

**Notes**:
- Uses streaming mode to minimize memory usage
- Handles network interruptions and rate limiting automatically
- May take 5-15 minutes depending on connection speed

### Stage 2: PII Scanning (T017)

```bash
python code/pii_scanner.py
```

**Output**: `data/pii_findings.csv` (if PII detected)

**Notes**:
- Scans all files under `data/` including `raw/`, `processed/`, and `analysis/`
- Logs any PII patterns found per Constitution Principle III

### Stage 3: Clone Detection (T019)

```bash
python code/ast_cloner.py
```

**Output**: `data/processed/clone_metrics.csv`

**Notes**:
- Uses Python built-in `ast` module (no external dependencies)
- Computes clone density for each code segment
- Logs parse failures to `data/parse_failures.csv`

### Stage 4: Model Perplexity (T020)

```bash
python code/model_metrics.py
```

**Output**: `data/processed/perplexity_scores.csv`

**Notes**:
- Loads `Salesforce/codegen-350M-mono` in 8-bit quantization
- Validates against NaN/infinite values
- Memory monitoring enforced (7GB limit)

### Stage 5: Bug Detection & Correlation (T031, T032)

```bash
python code/bug_detection.py
python code/correlation_analysis.py
```

**Output**:
- `data/analysis/bug_detection_results.csv`
- `data/analysis/correlation_results.csv`

**Notes**:
- HumanEval subset (50 problems) for pass@1 accuracy
- Spearman correlation between duplication density, perplexity, and accuracy

### Stage 6: Visualization & Sensitivity Analysis (T040, T041)

```bash
python code/visualization.py
```

**Output**: `data/analysis/figures/` (PNG and PDF files)

**Notes**:
- Sensitivity analysis across thresholds 0.7, 0.8, 0.9
- Scatter plots with regression lines
- Publication-ready format

### Complete Pipeline

To run the entire pipeline end-to-end:

```bash
python code/main.py
```

This orchestrates all stages in the correct data flow order.

## Output Files

| File Path | Description |
|-----------|-------------|
| `data/raw/github-code-sample.csv` | Downloaded code corpus (500MB) |
| `data/processed/clone_metrics.csv` | Clone density per code segment |
| `data/processed/perplexity_scores.csv` | Model perplexity per segment |
| `data/analysis/bug_detection_results.csv` | HumanEval pass@1 accuracy |
| `data/analysis/correlation_results.csv` | Spearman correlations with p-values |
| `data/analysis/figures/` | Visualization outputs (scatter plots) |
| `data/parse_failures.csv` | Log of AST parsing failures |
| `data/pii_findings.csv` | PII pattern detection results |
| `data/checksum_manifest.json` | Artifact checksums for verification |

## Verification & Validation

### Running Tests

```bash
pytest tests/ -v
```

Test coverage includes:
- Unit tests for each component
- Integration tests for pipeline stages
- Contract tests for schema validation
- Edge case handling (syntax errors, NaN values, network failures)

### Checksum Verification

```bash
python code/checksum_manifest.py verify
```

Validates all artifact checksums against the manifest.

### Performance Validation

```bash
pytest tests/integration/test_performance.py -v
```

Verifies SC-001 (24-hour completion) and 500MB corpus requirement.

```bash
pytest tests/integration/test_segment_count_validation.py -v
```

Verifies SC-003 (1000+ valid segments processed).

## Reproducibility

This project enforces reproducibility per Constitution Principle I:

1. **Fixed random seeds**: All random operations use `RANDOM_SEED` from `config.py`
2. **Versioned dependencies**: All package versions pinned in `requirements.txt`
3. **Checksum tracking**: All outputs tracked in `data/checksum_manifest.json`
4. **Configuration documentation**: All parameters documented in `config.py`

To reproduce results from a previous run:
1. Ensure same Python version (3.11+)
2. Install exact dependencies: `pip install -r requirements.txt`
3. Use same configuration in `code/config.py`
4. Verify checksums match: `python code/checksum_manifest.py verify`

## Research Question

This project investigates the correlation between code duplication density and
LLM code understanding metrics (perplexity and bug detection accuracy). Key
distinctions:

- **Syntactic duplication**: Copy-paste patterns detectable via AST analysis
- **Semantic duplication**: Functionally equivalent but syntactically different code

The pipeline focuses on syntactic duplication (AST clone density) and its
relationship to model perplexity and HumanEval pass@1 accuracy.

## Troubleshooting

### Out of Memory Errors

The pipeline enforces a 7GB memory limit. If you encounter OOM errors:
- Close other applications
- Reduce batch size in `code/model_metrics.py`
- Verify `MEMORY_LIMIT_MB` in `code/config.py`

### Network Issues During Download

The data loader handles interruptions automatically. For persistent issues:
- Check HuggingFace API status
- Verify internet connection stability
- Consider downloading the dataset manually from HuggingFace

### Parse Failures

Parse failures are logged to `data/parse_failures.csv`. Common causes:
- Non-Python files in corpus
- Syntax errors in code
- Encoding issues

## Constitution Check Traceability

See `tasks.md` for the complete mapping of Constitution Check principles to
task IDs:

| Principle | Task IDs |
|-----------|----------|
| I. Reproducibility | T002, T006, T043 |
| II. Verified Accuracy | T029, T030, T034, T035 |
| III. Data Hygiene | T014, T017, T025, T036, T044 |
| IV. Single Source of Truth | T021, T025, T036, T044 |
| V. Versioning Discipline | T025, T036, T044 |
| VI. Statistical Correlation Integrity | T032, T034, T035 |
| VII. Clone Detection Consistency | T019, T040 |

## Support

For issues or questions:
1. Check existing test failures: `pytest tests/ -v`
2. Review logs in `data/` directory
3. Consult `research.md` for literature review and methodology
4. Review `data-model.md` for entity definitions and data flow

## License

See project root LICENSE file for terms.