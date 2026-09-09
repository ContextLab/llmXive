# API Reference: Dream-State Learning

This document provides a comprehensive reference for the public APIs in the
Dream-State Learning project.

## Configuration

### `code/config.py`

```python
from config import Config

# Access configuration values
config = Config()
mask_rate = config.MASK_RATE
warmup_steps = config.WARMUP_STEPS
```

**Public Attributes:**
- `MASK_RATE` (float): Token masking probability for dream phase (default: 0.15)
- `WARMUP_STEPS` (int): Minimum steps before dream phase (default: 10)
- `DREAM_RATIO` (int): Wake steps per dream step (default: 5)
- `ENTROPY_THRESHOLD` (float): Low-entropy detection threshold (default: 0.5)
- `MAX_WALL_CLOCK_HOURS` (float): Runtime limit (default: 5.5)
- `MEMORY_LIMIT_GB` (int): RAM limit (default: 8)
- `SEED` (int): Random seed for reproducibility
- `DEVICE` (str): Execution device ("cpu" only)

## Data Module

### `code/data/loader.py`

```python
from data.loader import (
 load_glue_subset,
 load_superglue_subset,
 compute_file_checksum,
 verify_dataset_integrity
)
```

**Functions:**
- `load_glue_subset(subset: str) -> Dataset`: Downloads and loads a GLUE subset
- `load_superglue_subset(subset: str) -> Dataset`: Downloads and loads a SuperGLUE subset
- `compute_file_checksum(filepath: str) -> str`: Computes SHA-256 checksum
- `verify_dataset_integrity() -> bool`: Verifies all cached datasets

**Exceptions:**
- `DataIntegrityError`: Raised when checksum verification fails

### `code/data/augment.py`

```python
from data.augment import (
 apply_dae_mask,
 create_dae_batch,
 calculate_mask_statistics
)
```

**Functions:**
- `apply_dae_mask(tokens: List[int], mask_rate: float = 0.15) -> List[int]`:
 Applies random token masking at specified rate
- `create_dae_batch(batch: Dict[str, Any]) -> Dict[str, Any]`:
 Creates a masked batch for dream phase training
- `calculate_mask_statistics(masked_tokens: List[int]) -> Dict[str, float]`:
 Computes masking statistics (mask count, rate, etc.)

## Models Module

### `code/models/trainer.py`

```python
from models.trainer import (
 DreamScheduler,
 Trainer,
 main
)
```

**Classes:**

#### `DreamScheduler`

Manages the wake-to-dream phase ratio.

```python
scheduler = DreamScheduler(wake_steps=5, warmup_steps=10)
is_dream = scheduler.should_run_dream(step_count)
```

**Methods:**
- `should_run_dream(step_count: int) -> bool`: Returns True if dream phase should run
- `reset()`: Resets the step counter

#### `Trainer`

Orchestrates the wake/dream training loop.

```python
trainer = Trainer(
 model=model,
 optimizer=optimizer,
 wake_dataloader=wake_loader,
 dream_dataloader=dream_loader,
 config=config
)
results = trainer.train(num_steps=100)
```

**Methods:**
- `train(num_steps: int) -> Dict[str, Any]`: Runs the training loop
- `wake_step(batch: Dict) -> float`: Executes one wake phase step
- `dream_step(batch: Dict) -> float`: Executes one dream phase step
- `check_entropy(logits: Tensor) -> float`: Computes entropy of outputs
- `save_checkpoint(path: str)`: Saves model checkpoint

**Exceptions:**
- `RuntimeError`: Raised if dream phase triggers before warm-up completes

## Evaluation Module

### `code/eval/metrics.py`

```python
from eval.metrics import (
 calculate_few_shot_accuracy,
 evaluate_on_holdout,
 wilcoxon_test
)
```

**Functions:**
- `calculate_few_shot_accuracy(model, dataset: Dataset) -> float`:
 Computes few-shot accuracy on a dataset
- `evaluate_on_holdout(model, holdout_data: Dataset) -> Dict[str, float]`:
 Evaluates model on held-out data
- `wilcoxon_test(results1: List[float], results2: List[float]) -> float`:
 Runs Wilcoxon signed-rank test

### `code/eval/statistical_analysis.py`

```python
from eval.statistical_analysis import (
 run_ttest_paired,
 compute_accuracy_difference,
 save_analysis_report
)
```

**Functions:**
- `run_ttest_paired(results1: List[float], results2: List[float]) -> Tuple[float, float]`:
 Runs paired t-test, returns (t-statistic, p-value)
- `compute_accuracy_difference(results1: List[float], results2: List[float]) -> float`:
 Computes mean accuracy difference
- `save_analysis_report(results: Dict[str, Any], path: str)`:
 Saves analysis results to JSON

### `code/eval/sensitivity_report.py`

```python
from eval.sensitivity_report import (
 generate_sensitivity_report,
 compute_variance_metrics
)
```

**Functions:**
- `compute_variance_metrics(accuracies: List[float]) -> Dict[str, float]`:
 Computes variance and standard deviation
- `generate_sensitivity_report(results: Dict[str, Any]) -> Dict[str, Any]`:
 Generates comprehensive sensitivity report

### `code/eval/reporting.py`

```python
from eval.reporting import (
 save_comparison_report,
 generate_interpretation,
 load_report
)
```

**Functions:**
- `save_comparison_report(results: Dict[str, Any], path: str)`:
 Saves experimental vs. baseline comparison
- `generate_interpretation(results: Dict[str, Any]) -> str`:
 Generates human-readable interpretation
- `load_report(path: str) -> Dict[str, Any]`:
 Loads a saved report from JSON

## Utilities Module

### `code/utils/logger.py`

```python
from utils.logger import (
 get_logger,
 log_event,
 JsonFormatter
)
```

**Functions:**
- `get_logger(name: str) -> logging.Logger`:
 Returns a configured logger instance
- `log_event(event_type: str, data: Dict[str, Any])`:
 Logs a structured event

**Classes:**
- `JsonFormatter`: Custom logging formatter for JSON output

### `code/utils/memory_monitor.py`

```python
from utils.memory_monitor import (
 MemoryMonitor,
 get_current_rss_kb,
 get_peak_rss,
 enforce_memory_limit
)
```

**Classes:**
- `MemoryMonitor`: Tracks peak memory usage

**Functions:**
- `get_current_rss_kb() -> int`: Returns current RSS in KB
- `get_peak_rss() -> float`: Returns peak RSS in GB
- `enforce_memory_limit(limit_gb: float)`: Raises MemoryLimitExceeded if exceeded

**Exceptions:**
- `MemoryLimitExceeded`: Raised when memory limit is exceeded

### `code/utils/exceptions.py`

```python
from utils.exceptions import (
 DataIntegrityError,
 TimeLimitExceeded
)
```

**Exceptions:**
- `DataIntegrityError`: Dataset checksum verification failure
- `TimeLimitExceeded`: Wall-clock time limit exceeded

## Main Entry Point

### `code/main.py`

```python
from main import (
 run_single_seed_experiment,
 run_temperature_sweep,
 aggregate_results,
 main
)
```

**Functions:**
- `run_single_seed_experiment(seed: int, config: Config) -> Dict[str, Any]`:
 Runs a complete experiment for a single seed
- `run_temperature_sweep(temperatures: List[float], seeds_per_temp: int) -> Dict[str, Any]`:
 Runs temperature sensitivity analysis
- `aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]`:
 Aggregates results from multiple runs
- `main()`: CLI entry point

**CLI Arguments:**
- `--glue_subset`: GLUE dataset subset (e.g., "mrpc")
- `--seeds`: Number of seeds to run
- `--temperature_sweep`: Enable temperature sensitivity analysis
- `--temperatures`: Comma-separated temperature values
- `--warmup_steps`: Override warm-up steps
- `--dream_ratio`: Override dream ratio

## Scripts

### `code/scripts/validate_quickstart.py`

```python
from scripts.validate_quickstart import main
```

**Usage:**
```bash
python scripts/validate_quickstart.py
```

Validates the entire pipeline:
- Directory structure
- Dependencies
- Data loader
- Model loading
- Metrics computation
- End-to-end minimal run

### `code/scripts/generate_final_report.py`

```python
from scripts.generate_final_report import main
```

**Usage:**
```bash
python scripts/generate_final_report.py
```

Generates a comprehensive final report from all seed results.

### `code/scripts/cleanup_and_refactor.py`

```python
from scripts.cleanup_and_refactor import main
```

**Usage:**
```bash
python scripts/cleanup_and_refactor.py
```

Performs code cleanup:
- Import consolidation
- Whitespace normalization
- Type hint standardization
- Docstring standardization

## Error Handling

All functions may raise:
- `RuntimeError`: General runtime errors
- `ValueError`: Invalid input values
- `FileNotFoundError`: Missing files or datasets
- `DataIntegrityError`: Checksum verification failure
- `TimeLimitExceeded`: Runtime limit exceeded
- `MemoryLimitExceeded`: Memory limit exceeded

## Logging

All modules use the centralized logger from `utils.logger`. Log files are
saved to `data/logs/` with timestamps and structured JSON format.

Example log entry:
```json
{
 "timestamp": "2024-01-15T10:30:00Z",
 "event": "phase_transition",
 "data": {
 "from_phase": "wake",
 "to_phase": "dream",
 "step": 15
 }
}
```