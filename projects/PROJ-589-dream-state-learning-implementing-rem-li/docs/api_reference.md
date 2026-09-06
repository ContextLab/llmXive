# API Reference: Dream-State Learning

## `code/config.py`

### `Config`
Central configuration class.

**Attributes**:
- `device`: str ("cpu" enforced).
- `seed`: int.
- `max_steps`: int.
- `dream_ratio`: int (Wake: Dream ratio).
- `warmup_steps`: int.
- `entropy_threshold`: float.
- `memory_limit_gb`: float.
- `max_wall_clock_hours`: float.
- `data_paths`: dict (paths to raw, results, logs).

## `code/data/loader.py`

### `load_glue_subset(subset_name: str)`
Downloads and loads a GLUE subset.

**Returns**: `Dataset` object.

**Raises**: `DataIntegrityError` if checksum fails.

### `load_superglue_subset(subset_name: str)`
Downloads and loads a SuperGLUE subset.

**Returns**: `Dataset` object.

**Raises**: `DataIntegrityError` if checksum fails.

## `code/data/augment.py`

### `apply_dae_mask(tokens: List[int], mask_rate: float)`
Applies DAE masking to a list of tokens.

**Returns**: Tuple of (masked_tokens, mask_indices).

### `create_dae_batch(batch: Dict[str, Any], config: Config)`
Creates a DAE batch from a standard batch.

**Returns**: Dict with "input_ids", "attention_mask", "labels".

## `code/models/trainer.py`

### `DreamScheduler`
Manages the Wake/Dream cycle.

**Methods**:
- `should_dream(step: int) -> bool`: Returns True if current step is a Dream phase.
- `reset()`: Resets the scheduler state.

### `Trainer`
Core training loop.

**Methods**:
- `train_step(batch: Dict)`: Performs one step (Wake or Dream).
- `run_training()`: Executes the full training loop.
- `check_entropy(logits: Tensor)`: Validates output entropy.

**Exceptions**:
- `MemoryLimitExceeded`: Raised if memory limit is exceeded.

## `code/eval/metrics.py`

### `wilcoxon_test(sample1: List[float], sample2: List[float])`
Performs Wilcoxon signed-rank test.

**Returns**: Tuple of (statistic, p-value).

### `calculate_few_shot_accuracy(model, dataset: Dataset)`
Calculates accuracy on a held-out dataset.

**Returns**: float.

## `code/eval/statistical_analysis.py`

### `analyze_model_performance(results: List[Dict])`
Aggregates results from multiple seeds.

**Returns**: Dict with mean accuracy, std dev, and p-value.

## `code/main.py`

### `run_single_seed_experiment(config: Config)`
Runs a single experiment.

### `run_temperature_sweep(config: Config)`
Runs the temperature sensitivity analysis.

### `main()`
Entry point. Parses arguments and dispatches to appropriate runner.

## `code/utils/memory_monitor.py`

### `MemoryMonitor`
Tracks memory usage.

**Methods**:
- `start()`: Begins monitoring.
- `stop()`: Stops monitoring.
- `get_peak_rss() -> int`: Returns peak RSS in KB.

### `enforce_memory_limit(limit_gb: float)`
Checks current memory and raises `MemoryLimitExceeded` if exceeded.

## `code/utils/exceptions.py`

### `DataIntegrityError`
Raised when data checksum verification fails.

### `TimeLimitExceeded`
Raised when the wall-clock time limit is exceeded.

### `MemoryLimitExceeded`
Raised when the memory limit is exceeded.
