# Architecture Documentation: Dream-State Learning

## System Overview

The Dream-State Learning system implements a biologically-inspired training paradigm for language models. It alternates between two distinct phases:

1. **Wake Phase**: Standard supervised learning on real data
2. **Dream Phase**: Denoising autoencoder reconstruction of masked inputs

This cycle mimics the REM sleep process in biological systems, where memory consolidation occurs through replay and restructuring.

## Component Architecture

### Data Layer

#### `code/data/loader.py`
- Downloads GLUE/SuperGLUE datasets via Hugging Face `datasets` library
- Implements SHA-256 checksum verification for data integrity
- Raises `DataIntegrityError` on checksum mismatch (fails loudly, no synthetic fallback)
- Supports streaming for large datasets to manage memory

#### `code/data/augment.py`
- Implements Denoising Autoencoder (DAE) masking logic
- Random token masking consistent with BERT-style masking
- Configurable mask rate (default: 15%)
- Provides `apply_dae_mask`, `create_dae_batch`, and `calculate_mask_statistics`

### Model Layer

#### `code/models/trainer.py`
Core training engine implementing the Wake/Dream cycle:

- **DreamScheduler**: Manages the 4:1 Wake/Dream ratio via step counter modulo
- **Trainer**: Orchestrates the training loop with:
 - Wake phase: Cross-entropy loss on real data
 - Dream phase: DAE reconstruction loss on masked inputs
 - Warm-up protocol: Skips dream phase for first N steps
 - Entropy check: Detects low-entropy outputs (<0.5 bits), triggers retry
 - Memory monitoring integration: Aborts on OOM, saves checkpoint

#### `code/models/__init__.py`
- Initializes DistilBERT/TinyLlama models
- CPU-optimized, default precision
- Loads model configuration from `code/config.py`

### Evaluation Layer

#### `code/eval/metrics.py`
- Calculates few-shot accuracy on held-out subsets
- Implements Wilcoxon signed-rank test (`scipy.stats.wilcoxon`)
- Computes accuracy differences and p-values across multiple seeds

#### `code/eval/statistical_analysis.py`
- Loads accuracy results from multiple seed runs
- Performs statistical significance testing
- Generates analysis reports with interpretation

#### `code/eval/reporting.py`
- Saves comparison reports to `data/results/comparison_report.json`
- Loads and displays previous reports
- Generates human-readable interpretations

#### `code/eval/sensitivity_report.py`
- Loads temperature sweep results
- Computes variance metrics across hyperparameters
- Generates sensitivity analysis reports

### Utility Layer

#### `code/utils/logger.py`
- Structured JSON logging to `data/logs/`
- Event logging for phase transitions, entropy metrics, warm-up status
- Custom `JsonFormatter` for machine-readable logs

#### `code/utils/memory_monitor.py`
- Tracks peak RSS via `/proc/self/status`
- Enforces hard memory limits (7GB default)
- Raises `MemoryLimitExceeded` on violation
- Integrates with training loop for OOM protection

#### `code/utils/exceptions.py`
- Defines custom exceptions:
 - `DataIntegrityError`: For checksum failures
 - `TimeLimitExceeded`: For wall-clock violations
 - `MemoryLimitExceeded`: For memory violations

### Orchestration Layer

#### `code/main.py`
Main entry point that:
- Parses command-line arguments
- Orchestrates single-seed experiments
- Runs temperature sweeps (grid search)
- Manages baseline comparisons
- Enforces time limits (5-hour wall-clock)
- Coordinates memory monitoring

#### `code/config.py`
Central configuration for:
- Hyperparameters (mask rate, temperature, entropy threshold)
- Paths (data directories, output locations)
- Seed management
- CPU-only device enforcement
- Resource limits (memory, time)

## Data Flow

1. **Input**: GLUE/SuperGLUE dataset subsets
2. **Loading**: `loader.py` downloads and verifies data
3. **Augmentation**: `augment.py` applies DAE masking for dream phase
4. **Training**: `trainer.py` alternates Wake/Dream phases
5. **Evaluation**: `metrics.py` computes accuracy and statistical tests
6. **Reporting**: `reporting.py` saves results to JSON

## Key Design Decisions

### 1. Wake/Dream Ratio (4:1)
- Mimics biological REM sleep cycles
- Implemented via `DreamScheduler.step % 5` check
- Configurable via `config.py`

### 2. Entropy Threshold (0.5 bits)
- Prevents model collapse to low-diversity outputs
- Calculated as sum(-p*log2(p)) over output distribution
- Triggers retry up to 3 times before discarding batch

### 3. Warm-up Protocol
- Skips dream phase for first 10 steps
- Prevents instability during initial weight updates
- Raises `RuntimeError` if dream phase triggers prematurely

### 4. Statistical Testing
- Uses Wilcoxon signed-rank test (non-parametric)
- Accounts for unequal variance across seeds
- Significance level α=0.05

### 5. Resource Constraints
- Hard memory limit: 7GB (GitHub Actions free tier)
- Hard time limit: 5 hours
- CPU-only execution (no GPU dependencies)

## Error Handling

### Fail-Loudly Philosophy
- Data checksum failures: Raise `DataIntegrityError` immediately
- Memory violations: Raise `MemoryLimitExceeded`, save checkpoint, abort
- Time violations: Raise `TimeLimitExceeded`, save checkpoint, abort
- No synthetic fallbacks: Real data only, fail if unavailable

### Checkpointing
- Automatic checkpoint on OOM or time limit
- Saved to `data/checkpoints/`
- Can resume training from checkpoint

## Extensibility

### Adding New Datasets
1. Add dataset name to `loader.py` subset list
2. Define checksum in `config.py`
3. Update `get_available_subsets()`

### Modifying Hyperparameters
1. Edit `config.py` for new defaults
2. Use `--override` flags in `main.py` for runtime changes

### Custom Evaluation Metrics
1. Extend `metrics.py` with new function
2. Update `statistical_analysis.py` to include in report

## Testing Strategy

### Unit Tests
- `tests/unit/test_trainer.py`: Warm-up, entropy, DreamScheduler
- `tests/unit/test_metrics.py`: Wilcoxon test, accuracy calculation
- `tests/unit/test_memory_monitor.py`: Memory limit enforcement

### Integration Tests
- `tests/integration/test_training_loop.py`: Multi-step Wake/Dream cycle
- `tests/integration/test_evaluation.py`: End-to-end evaluation
- `tests/integration/test_resource_limits.py`: Time/memory limits

### Contract Tests
- `tests/contract/`: Schema validation for config and result files

## Performance Considerations

### Memory Management
- Streaming datasets for large files
- Batch size optimization for CPU constraints
- Peak RSS monitoring to prevent OOM

### Time Optimization
- Efficient data loading with caching
- Minimal overhead in phase transitions
- Parallel seed runs where possible

### CPU Optimization
- DistilBERT/TinyLlama models (smaller than full BERT)
- Default precision (no 8-bit quantization)
- Batch processing for throughput

## Future Work

- Implement structural remodeling (beyond data augmentation)
- Explore different dream phase mechanisms
- Add biological cost modeling (energy/compute trade-offs)
- Extend to multi-modal inputs
- Investigate long-term consolidation metrics
