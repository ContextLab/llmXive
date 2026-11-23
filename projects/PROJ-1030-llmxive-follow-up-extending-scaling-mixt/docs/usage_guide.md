# llmXive Usage Guide

This guide provides detailed instructions for using the llmXive pipeline, including configuration options, troubleshooting, and advanced usage patterns.

## Table of Contents

1. [Installation and Setup](#installation-and-setup)
2. [Running the Pipeline](#running-the-pipeline)
3. [Pipeline Stages](#pipeline-stages)
4. [Configuration Options](#configuration-options)
5. [Output Artifacts](#output-artifacts)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Usage](#advanced-usage)

## Installation and Setup

### System Requirements

- **Operating System**: Linux, macOS, or Windows (with WSL2 recommended)
- **Python**: 3.11 or higher
- **Memory**: Minimum 7GB RAM (16GB recommended for larger datasets)
- **Disk Space**: ~20GB for models, data, and artifacts
- **Network**: Broadband connection for initial data download (~5-10GB)

### Step-by-Step Installation

1. **Create and activate virtual environment**:
 ```bash
 python3.11 -m venv venv
 source venv/bin/activate # Linux/macOS
 # or
 venv\Scripts\activate # Windows
 ```

2. **Install dependencies**:
 ```bash
 pip install --upgrade pip
 pip install -r code/requirements.txt
 ```

3. **Initialize project structure**:
 ```bash
 python code/setup_project_structure.py
 ```
 This creates the following directory structure:
 ```
 code/
 data/raw/
 data/processed/
 data/external/
 tests/unit/
 tests/integration/
 docs/
 state/
 ```

4. **Set up pre-commit hooks**:
 ```bash
 python code/setup_precommit.py
 ```
 This configures `ruff` for linting and `black` for formatting.

5. **Configure environment variables** (optional):
 Create `data/.env` file:
 ```bash
 # HuggingFace token (required for some models)
 HF_TOKEN=your_token_here

 # Memory limits
 MAX_MEMORY_GB=7

 # Sampling configuration
 SAMPLE_SIZE=100
 ```

## Running the Pipeline

### Full Pipeline Execution

The simplest way to run the entire pipeline:

```bash
python code/main_pipeline.py
```

This command:
1. Downloads LingBot-Video weights (if not present)
2. Extracts features from video clips
3. Generates physical validity labels
4. Trains and evaluates a classifier
5. Generates all reports and artifacts
6. Updates the manifest with checksums

**Expected output**:
- Console progress logs
- `data/processed/` artifacts
- `state/manifest.yaml`
- `pipeline_run_summary.json`

### Running with Custom Parameters

```bash
python code/main_pipeline.py --sample-size 50 --max-memory 5 --verbose
```

Available options:
- `--sample-size`: Number of video clips to process (default: 100)
- `--max-memory`: Maximum memory usage in GB (default: 7)
- `--verbose`: Enable detailed logging
- `--resume`: Resume from last checkpoint if pipeline was interrupted

## Pipeline Stages

The pipeline consists of three main stages, each independently runnable:

### Stage 1: Feature Extraction

**Purpose**: Extract latent activation vectors and expert masks from LingBot-Video model.

**Input**: Video manifests from `data/raw/`
**Output**: `data/processed/features.npy`, `data/processed/extract.log`

**Running**:
```bash
python code/extract_features.py
```

**Key components**:
- Memory management via `code/utils/memory_manager.py`
- Frame subsampling and temporal chunking
- Streaming video loading to stay within memory limits
- Exponential backoff for download failures

**Configuration**:
- Adjust subsampling rate in `data/processed/chunking_config.json`
- Monitor memory usage in `data/processed/memory_log.json`

### Stage 2: Label Generation

**Purpose**: Generate ground-truth physical validity labels via 3D reconstruction and physics simulation.

**Input**: Extracted features, video clips
**Output**: `data/processed/labels.csv`, `data/processed/null_labels.csv`

**Running**:
```bash
python code/generate_labels.py
```

**Key components**:
- MonoDepth2 for monocular depth estimation
- 3D reconstruction from depth maps
- PyBullet physics simulation
- Synthetic perturbation for creating "invalid" class

**Configuration**:
- Confidence threshold for null label assignment (default: 0.9)
- Perturbation strength for invalid samples

### Stage 3: Classification

**Purpose**: Train lightweight classifier to predict physical validity.

**Input**: Features and labels
**Output**: `data/processed/classifier.pkl`, `data/processed/evaluation_metrics.json`

**Running**:
```bash
python code/classification/train_classifier.py
```

**Key components**:
- Data filtering (removing null labels)
- Sh MLP or Random Forest training
- SHAP-based feature importance analysis
- Baseline comparison (majority class predictor)

**Configuration**:
- Model type: `--model-type mlp` or `--model-type rf`
- Hyperparameter grid size: `--grid-size 5`

## Configuration Options

### Memory Management

The pipeline implements adaptive memory management:

- **Frame Subsampling**: Reduces frame count for short clips
- **Temporal Chunking**: Splits long clips into manageable segments
- **Peak Memory Limit**: Enforced at 7GB by default

Configuration file: `data/processed/chunking_config.json`

### Sampling Strategy

Stratified sampling based on action type ensures balanced representation:

```python
# code/utils/sampling_strategy.py
from utils.sampling_strategy import StratifiedSampler

sampler = StratifiedSampler(action_column='action_type', sample_size=100)
sample_list = sampler.generate_sample_list(video_manifest)
```

### Logging Configuration

All pipeline stages use structured logging:

- **Feature Extraction**: `data/processed/extract.log`
- **Label Generation**: `data/processed/labeling.log`
- **Classification**: `data/processed/classification.log`

Log levels: `INFO`, `WARNING`, `ERROR`

## Output Artifacts

### Data Artifacts

| File | Description | Format |
|------|-------------|--------|
| `features.npy` | Latent vectors and expert masks | NumPy (shape: [N, D]) |
| `labels.csv` | Physical validity labels | CSV |
| `null_labels.csv` | Excluded samples | CSV |
| `classifier.pkl` | Trained model | Pickle |
| `evaluation_metrics.json` | Performance metrics | JSON |
| `feature_importance.json` | SHAP values | JSON |
| `pipeline_run_summary.json` | Execution summary | JSON |

### Metadata Files

| File | Description |
|------|-------------|
| `data/processed/metadata.json` | Dataset statistics and configuration |
| `state/manifest.yaml` | SHA-256 checksums for all artifacts |
| `data/.checksums.json` | Artifact checksums for verification |

### Reports

| File | Description |
|------|-------------|
| `docs/results_report.md` | Final results with associational framing |
| `shap_interpretation.md` | Feature importance interpretation |
| `data/processed/filtering_report.json` | Data filtering statistics |

## Troubleshooting

### Common Issues

#### Memory Out-of-Bounds Errors

**Symptom**: `MemoryError` or OOM during feature extraction

**Solution**:
1. Reduce `--sample-size` parameter
2. Adjust `MAX_MEMORY_GB` in environment configuration
3. Check `data/processed/memory_log.json` for peak usage

#### Download Failures

**Symptom**: HuggingFace model download fails

**Solution**:
1. Verify internet connection
2. Set valid `HF_TOKEN` in `data/.env`
3. Retry with exponential backoff (automatic)

#### Low Confidence Labels

**Symptom**: High proportion of samples in `null_labels.csv`

**Solution**:
1. Check depth estimation quality in `data/processed/kinematic_filter_log.json`
2. Adjust confidence threshold (default: 0.9)
3. Verify video clip quality in `data/raw/`

#### Model Training Issues

**Symptom**: Poor classifier performance (F1 < 0.75)

**Solution**:
1. Check class balance in `data/processed/balance_report.json`
2. Increase `--sample-size` for more training data
3. Try different model types (MLP vs Random Forest)

### Debug Mode

Enable verbose logging for debugging:

```bash
python code/main_pipeline.py --verbose --debug
```

This provides:
- Detailed step-by-step progress
- Memory usage at each stage
- Full stack traces for errors

## Advanced Usage

### Custom Feature Extraction

Modify extraction parameters:

```python
from code.extract_features import ExtractionConfig

config = ExtractionConfig(
 model_name="lingbot-video",
 layers=["layer_5", "layer_10"],
 subsample_rate=0.5,
 chunk_size=16
)
```

### Custom Labeling Pipeline

Adjust physics simulation parameters:

```python
from code.labeling.reconstruct_3d import ReconstructionConfig

config = ReconstructionConfig(
 depth_model="monodepth2",
 confidence_threshold=0.85,
 perturbation_strength=0.2
)
```

### Batch Processing

Process multiple datasets:

```bash
for dataset in dataset1 dataset2 dataset3; do
 python code/main_pipeline.py --dataset $dataset
done
```

### Continuous Integration

Add pipeline to CI/CD:

```yaml
#.github/workflows/pipeline.yml
name: Pipeline Test
on: [push, pull_request]
jobs:
 run-pipeline:
 runs-on: ubuntu-latest
 steps:
 - uses: actions/checkout@v2
 - name: Setup Python
 uses: actions/setup-python@v2
 with:
 python-version: '3.11'
 - name: Install dependencies
 run: pip install -r code/requirements.txt
 - name: Run pipeline
 run: python code/main_pipeline.py --sample-size 10
```

### Reproducibility

Ensure reproducible results:

1. Set random seeds in configuration
2. Verify artifact checksums in `state/manifest.yaml`
3. Use `--resume` flag to continue interrupted runs
4. Document all configuration parameters

## Performance Optimization

### Memory Optimization

- Enable garbage collection between chunks
- Use `torch.no_grad()` for inference
- Stream video data instead of loading entirely

### Speed Optimization

- Parallelize independent tasks
- Use efficient data formats (NumPy, HDF5)
- Cache intermediate results

### Disk Usage

- Compress large artifacts
- Remove temporary files after processing
- Use symbolic links for shared models

## API Reference

### Core Modules

#### `code/extract_features.py`
```python
from extract_features import main, extract_activations, save_features
```

#### `code/generate_labels.py`
```python
from generate_labels import main, run_depth_inference, load_video_manifest
```

#### `code/classification/train_classifier.py`
```python
from classification.train_classifier import main, train_model, load_classifier
```

### Utility Functions

#### `code/utils/memory_manager.py`
```python
from utils.memory_manager import estimate_frame_memory, get_processing_plan
```

#### `code/utils/logging_config.py`
```python
from utils.logging_config import get_logger, fail_loudly
```

#### `code/utils/retry.py`
```python
from utils.retry import retry_with_backoff, retry_download
```

## Support and Contribution

For issues, questions, or contributions:
1. Check existing issues in the repository
2. Create a new issue with detailed description
3. Submit pull requests with tests and documentation

## License

[Insert license information]
