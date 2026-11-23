# Modular Runners Package

This directory contains refactored, class-based orchestration scripts for the llmXive pipeline.
These modules replace the monolithic scripts in `code/` to improve testability and maintainability.

## Structure

- `correlation_runner.py`: Implements the T017 correlation analysis pipeline.
- `router_inference_runner.py`: Implements the T029 dynamic router inference pipeline.
- `__init__.py`: Exports runner classes.

## Usage

### Running Correlation Analysis

```bash
cd code
python runners/correlation_runner.py
```

This script:
1. Loads prompts from `data/processed/diverse_prompts.csv`.
2. Computes semantic entropy for each prompt.
3. Runs DiT generation to capture activation variances.
4. Computes Pearson correlation between entropy and variance.
5. Saves results to `data/processed/correlation_results.json`.

### Running Router Inference

```bash
cd code
python runners/router_inference_runner.py
```

This script:
1. Loads test prompts.
2. Computes entropy.
3. Loads pre-computed rotation matrices from `data/processed/clustering_report.json`.
4. Selects matrices dynamically based on entropy.
5. Generates images using the W2A4 engine with dynamic quantization.
6. Saves metrics and results to `data/processed/router_inference_results.json`.

## Programmatic Usage

You can also import and use these runners in other scripts:

```python
from runners.correlation_runner import CorrelationRunner
from config import Config

config = Config()
runner = CorrelationRunner(config)
stats = runner.run()
print(f"Correlation: {stats['correlation']}, p-value: {stats['p_value']}")
```

## Dependencies

Ensure all project dependencies are installed:
```bash
pip install -r requirements.txt
```

## Notes

- These runners rely on the GPU offload mechanism (T041) if running on CPU without GPU capabilities.
- Real data sources are used; no synthetic fallbacks are implemented.
- Error handling is strict: failures are logged and raise exceptions to halt execution.
