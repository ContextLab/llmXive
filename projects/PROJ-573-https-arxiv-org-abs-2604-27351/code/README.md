# llmXive: Heterogeneous Scientific Foundation Model Collaboration Benchmark

A research benchmark for evaluating heterogeneous scientific foundation models across time-series, tabular, and text modalities.

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd llmXive
python setup_project.py

# Activate environment
source.venv/bin/activate # Linux/Mac
.venv\\Scripts\\activate # Windows

# Run benchmark
python src/benchmark/run_benchmark.py --config default.yaml
```

## Project Structure

- `src/` - Source code
- `tests/` - Test suite
- `data/` - Datasets and processed data
- `state/` - Runtime state and artifacts
- `contracts/` - Schema contracts
- `docs/` - Documentation

## Requirements

- Python 3.11+
- CPU-tractable models (<1GB weights)
- No GPU/CUDA dependencies

## License

MIT
