# Quickstart Guide: llmXive Follow-up

This guide walks you through setting up and running the **llmXive Follow-up** pipeline to benchmark how coding agents explore repositories.

## Prerequisites

- Python 3.9+
- pip
- Git
- 2-core CPU / 7GB RAM minimum (CPU-only execution)

## 1. Setup Environment

Clone the repository and install dependencies:

```bash
git clone
cd llmxive-follow-up
pip install -r requirements.txt
```

**Note**: Ensure `datasets` and `matplotlib` are installed. No CUDA/GPU required.

## 2. Project Structure

The project follows this directory layout:

```
.
├── code/ # Source code
│ ├── config.py # Configuration
│ ├── utils/ # Utilities (hashing, validation)
│ ├── data/ # Data processing scripts
│ ├── agent/ # Agent logic (baseline, iterative)
│ ├── metrics/ # Metrics calculation
│ └── analysis/ # Statistical analysis & reporting
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── curated/ # Curated hard instances & synthetic issues
│ └── results/ # Agent logs and metrics
├── tests/ # Unit and contract tests
├── contracts/ # JSON schemas for data validation
├── paper/ # Draft paper
└── docs/ # Documentation
```

## 3. Configuration

Edit `code/config.py` to set:

- `HARD_INSTANCE_PERCENTILE`: Percentile threshold for "hard" instances (default: 20)
- `VALIDATION_SAMPLE_SIZE`: Number of samples for manual validation (default: 20)
- `MAX_TURNS`: Maximum turns for iterative agent (default: 3)
- `CPU_ONLY`: Force CPU execution (default: True)

```python
# code/config.py
HARD_INSTANCE_PERCENTILE: int = 20
VALIDATION_SAMPLE_SIZE: int = 20
MAX_TURNS: int = 3
CPU_ONLY: bool = True
```

## 4. Data Curation (User Story 1)

Download the SWE-Explore benchmark and curate a "hard" subset:

```bash
# Step 1: Download dataset
python -m code.data.download

# Step 2: Derive ground truth from solution patches
python -m code.data.derive_gt

# Step 3: Filter hard instances and generate synthetic issues
python -m code.data.curate

# Step 4: Validate curated data
python -m code.data.validate_hard

# Step 5: Hash curated artifacts
python -m code.data.hash_curated
```

**Outputs**:
- `data/curated/hard_subset.jsonl`
- `data/curated/synthetic_issues.jsonl`
- `data/curated/validation_report.md`

## 5. Agent Execution (User Story 2)

Run the Static Multi-Query Baseline and Iterative Agent:

```bash
# Run both baseline and iterative agents on curated data
python -m code.main --mode both --issues all

# Optional: Run turn-limit sweep (N=20 issues, 4 turns)
python -m code.agent.sweep_turns
```

**Outputs**:
- `data/results/agent_logs/baseline_logs.jsonl`
- `data/results/agent_logs/iterative_logs.jsonl`
- `data/results/paired_metrics.json`
- `data/results/sweep_results.json` (if sweep enabled)

## 6. Statistical Analysis (User Story 3)

Compute metrics and run statistical tests:

```bash
# Generate final metrics with Wilcoxon/Bonferroni correction
python -m code.analysis.generate_final_metrics

# Generate plots
python -m code.analysis.plots

# Generate paper draft
python -m code.analysis.report_generator
```

**Outputs**:
- `data/results/final_metrics.json`
- `figures/*.png` (coverage histograms, survival curves)
- `paper/draft.md`

## 7. Validation & Testing

Run the test suite:

```bash
# Contract tests (schema validation)
pytest tests/contract/

# Unit tests
pytest tests/unit/
```

## 8. Hashing & Integrity

All data artifacts are hashed for reproducibility:

```bash
# Hash curated data
python -m code.data.hash_curated

# Hash final metrics
python -m code.analysis.hash_final_metrics
```

Check `data/manifest.json` and `data/results/manifest.json` for SHA256 hashes.

## 9. Troubleshooting

- **ImportError: No module named 'datasets'**: Run `pip install datasets`
- **Memory Error**: Reduce `VALIDATION_SAMPLE_SIZE` or `HARD_INSTANCE_PERCENTILE`
- **AST Parse Error**: Synthetic issues must be syntactically valid; check `data/curated/validation_report.md`
- **Timeout**: The runtime monitor (T039) will abort non-critical sweeps if >5.5 hours

## 10. Next Steps

- Review `paper/draft.md` for associational findings
- Extend with new synthetic mutation strategies
- Add more agent policies to the baseline

For detailed design docs, see `specs/001-iterative-exploration-benchmark/`.
