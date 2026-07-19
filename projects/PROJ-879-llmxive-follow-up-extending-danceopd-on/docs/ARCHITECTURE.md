# Architecture Documentation

## System Design

The llmXive pipeline is designed as a modular, stage-based system where each stage produces artifacts consumed by subsequent stages.

### Core Principles

1. **Separation of Concerns**: Each script handles a single responsibility
2. **Artifact-Driven**: Stages communicate via files, not in-memory objects
3. **Fail Fast**: Errors are raised immediately, not hidden
4. **Reproducibility**: All artifacts are versioned with checksums
5. **CPU-First**: Designed for CPU execution with GPU as optional acceleration

## Module Architecture

### Data Layer (`code/00_data_generation.py`)

**Responsibility**: Stream real data, run teacher inference, extract features

**Components**:
- `_data_streaming.py`: Stratified sampling from ImageNet/LAION
- `00_teacher_inference.py`: Load teacher, run inference, handle fallbacks
- `00_data_extraction.py`: Extract features, validate, stream to Parquet

**Inputs**:
- Hugging Face datasets (ImageNet-1K, LAION-400M)
- Teacher model weights (via `TEACHER_WEIGHTS_PATH`)

**Outputs**:
- `data/raw/imageNet_samples.parquet`
- `data/raw/laion_samples.parquet`
- `data/processed/teacher_routing_dataset.parquet`

### Model Layer (`code/01_train_trees.py`)

**Responsibility**: Train decision trees, evaluate routing consistency

**Components**:
- Data splitting (train/test)
- Tree training loop (max_depth 2-20)
- Accuracy evaluation
- Model serialization

**Inputs**:
- `data/processed/teacher_routing_dataset.parquet`

**Outputs**:
- `models/trained_trees/` (individual `.pkl` files)
- `data/results/tree_accuracy.csv`

### Evaluation Layer (`code/02_evaluate_fidelity.py`)

**Responsibility**: Generate images, compute metrics, perform statistical tests

**Components**:
- `models/inference.py`: Euler integrator, expert field simulation
- `utils/metrics.py`: CLIP score, FID calculation
- `utils/statistics.py`: Bootstrap, t-test, power analysis
- `02_evaluate_fidelity.py`: Main evaluation orchestration

**Inputs**:
- `data/processed/teacher_routing_dataset.parquet`
- `models/trained_trees/`

**Outputs**:
- `data/results/fidelity_metrics.csv`
- `data/results/statistical_tests.json`
- `data/results/fidelity_summary.md`
- `data/results/` (generated images)

### Utility Layer (`code/utils/`)

**Components**:
- `config.py`: Configuration management (seeds, paths, hyperparameters)
- `metrics.py`: Image similarity metrics (CLIP, FID)
- `statistics.py`: Statistical testing functions
- `check_weights.py`: Weight verification and checksumming
- `config.py`: Centralized configuration

**Dependencies**:
- `torch`, `transformers`, `torch-fidelity`, `scikit-learn`, `pandas`, `numpy`, `datasets`

## Data Flow

```
[ImageNet/LAION] --> [Streaming] --> [Teacher Inference] --> [Feature Extraction]
 |
 v
 [Parquet Dataset]
 |
 v
 [Tree Training]
 |
 v
 [Trained Decision Trees]
 |
 v
 [Fidelity Evaluation]
 |
 v
 [Statistical Analysis]
 |
 v
 [Final Report]
```

## Error Handling Strategy

1. **Data Fetching**: Fail immediately if real data cannot be fetched (no synthetic fallback)
2. **GPU Inference**: Abort if GPU unavailable and no verified fallback exists
3. **Timeout**: Hard 6-hour limit with partial result saving
4. **Statistical Power**: Stop if power < 0.8, save partial results
5. **Validation**: All artifacts validated against JSON schemas

## Scalability Considerations

- **Streaming**: Data is processed in chunks to stay within memory limits
- **Parallelism**: Independent stages can run in parallel (e.g., tree training for different depths)
- **Checkpointing**: Partial results saved at key points
- **Timeouts**: All long-running operations have hard limits

## Security and Integrity

- **Checksums**: All artifacts checksummed with SHA256
- **Manifests**: Weight files verified against manifest
- **Schemas**: Data validated against JSON schemas
- **Versioning**: All artifacts versioned with metadata
