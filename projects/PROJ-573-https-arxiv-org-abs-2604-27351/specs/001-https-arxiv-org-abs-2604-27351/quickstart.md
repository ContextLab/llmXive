# Quickstart: Heterogeneous Scientific Foundation Model Collaboration Benchmark

## Prerequisites

- Python 3.11 or higher
- Multiple CPU cores minimum
- Sufficient RAM minimum
- Sufficient free disk space
- Network access to HuggingFace datasets

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/<org>/heterogeneous-collaboration-benchmark.git
cd heterogeneous-collaboration-benchmark
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt** pins all dependencies:

```
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
pyyaml>=6.0
datasets>=2.14.0
scipy>=1.11.0
matplotlib>=3.7.0
reportlab>=4.0.0
requests>=2.31.0
pytest>=7.4.0
```

## Running the Benchmark

### Full Benchmark (User Story 1)

```bash
python src/benchmark/run_benchmark.py --config default.yaml
```

**Expected output**:
- `results.csv` - Task-level results
- `summary.pdf` - Statistical summary report
- Execution time: ≤4 hours on reference hardware

### Single Task Execution (User Story 2)

```bash
python src/benchmark/run_task.py --task-id 3 --add-modality image
```

**Expected output**:
- Task result logged to `results.csv`
- Modality embedding combined with other modalities

### Unified Mode (User Story 3)

```bash
python src/benchmark/run_benchmark.py --config default.yaml --mode unified
```

**Expected output**:
- All modalities converted to text
- Single LLM processes concatenated text
- Results comparable to heterogeneous mode

## Configuration

### Default Configuration (default.yaml)

```yaml
benchmark:
  tasks: 20
  seeds: 5
  timeout_per_task: 300  # seconds (5 minutes)

datasets:
  max_total_size_mb: 5120  # 5 GB
  retry_count: 3

models:
  max_model_size_mb: 1024  # 1 GB
  cpu_only: true

statistics:
  alpha: 0.05
  bootstrap_resamples: 1000
```

### Adding New Modality (User Story 2)

1. Create `src/benchmark/config/modalities/image.yaml`:

```yaml
modality: image
model:
  hf_identifier: "microsoft/resnet-50"
  size_mb: to be determined
  cpu_compatible: true
```

2. Run task with new modality:

```bash
python src/benchmark/run_task.py --task-id 3 --add-modality image
```

## Output Files

| File | Description |
|------|-------------|
| `results.csv` | Task-level metrics (F1, MAPE, inference time) |
| `summary.pdf` | Statistical report with t-test, bootstrap CI |
| `data/checksums.yaml` | Dataset integrity checksums |
| `logs/benchmark.log` | Execution logs with seeds/versions |

## Troubleshooting

### Dataset Download Fails

- System retries up to 3 times (FR-010)
- Check network connectivity
- Verify URL in `data/checksums.yaml`

### Inference Timeout

- Task aborted and recorded as failure (FR-013)
- Check model size <1 GB
- Reduce task complexity if needed

### Missing Modality

- System logs warning and proceeds (FR-012)
- Missing modality contribution recorded as zero
- Check task configuration for required modalities

## Validation

### Run Contract Tests

```bash
pytest tests/contract/ -v
```

### Verify Reproducibility

```bash
# Run with different seeds
python src/benchmark/run_benchmark.py --seed 42
python src/benchmark/run_benchmark.py --seed 123

# Compare results (should be within 95% CI)
```

## Next Steps

1. Review `data-model.md` for entity definitions
2. Review `contracts/*.schema.yaml` for validation rules
3. Review `research.md` for dataset and methodology details
4. Proceed to implementation phase
