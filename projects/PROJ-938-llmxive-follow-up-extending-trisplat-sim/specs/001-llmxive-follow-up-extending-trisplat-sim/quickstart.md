# Quickstart Guide: Extending TriSplat for CPU-only Edge Robotics

## Prerequisites
- Python 3.11+
- pip
- 8GB+ RAM (recommended)
- RealEstate10K dataset access (automated via `datasets` library)

## Installation

1. **Clone and setup**:
 ```bash
 cd projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r code/requirements.txt
 ```

2. **Verify environment**:
 ```bash
 python code/cli.py --help
 ```

## Running the Pipeline

### Single Scene Reconstruction (US1)
```bash
python code/cli.py --views 3 --seed 42
```

### Batch Processing with Sparsity Analysis (US1 + US2)
```bash
python code/cli.py --views 2,3,4,5 --update-state --seed 42
```

### Full Benchmarking (US3)
```bash
python code/experiments/run_batch.py --views 2,3,4,5 --tolerance 0.15 --timeout 21600
```

## Output Artifacts

- `data/processed/threshold_result.json` - Sparsity threshold analysis
- `data/processed/benchmark_tradeoff.csv` - Latency vs. fidelity metrics
- `data/processed/benchmark_tradeoff_plot.png` - Trade-off visualization
- `state/projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim.yaml` - Artifact hashes

## Troubleshooting

- **Dataset fetch failure**: Ensure internet connectivity; no synthetic fallback
- **CPU affinity error**: Run with elevated permissions or disable affinity enforcement
- **Timeout exceeded**: Increase `--timeout` or reduce scene count

## Next Steps
- Review `plan.md` for project roadmap
- Run `python code/cli.py --update-state` after batch completion
- Validate contracts: `python code/utils/validate_contracts.py`
