# llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation

**Project ID**: PROJ-860-llmxive-follow-up-extending-dragmesh-2-p

## Overview

This project implements a virtual tactile zero-shot adaptation pipeline for robotic manipulation.
It estimates object stiffness ($k_{est}$) from torque/velocity derivatives, adapts reward schedules
dynamically, and validates performance on novel high-friction objects using a Generalized Linear
Mixed Model (GLMM).

## Installation

1. **Clone and Setup**:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p
 ```

2. **Install Dependencies**:
 Ensure you have Python 3.9+ and install the required packages:
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: `pybullet` is CPU-only. CUDA/GPU acceleration is explicitly disabled per FR-004.*

## Usage

The pipeline is orchestrated via `code/run_benchmark.py`, but individual components can be run manually.

### 1. Data Preparation

Download the DragMesh-2 dataset and verify integrity:
```bash
python code/data_loader.py
python code/verify_manifest.py
```

Generate novel object geometries for zero-shot evaluation:
```bash
python code/generator.py --count 50 --seed 42 --high-friction-count 25 --friction-min 0.0 --friction-max 2.5 --output data/generated/
```

### 2. Training

Train the adaptive policy on the base dataset (excluding high-friction objects):
```bash
python code/train.py --epochs 100 --batch-size 32
```
*Configuration constants logged: `epsilon=1e-4`, `filter_window=5`.*

### 3. Evaluation

Evaluate both adaptive and static policies on novel objects:
```bash
python code/evaluate.py --policy adaptive --policy static
```
Output: `data/results/eval_logs.csv`

### 4. Analysis

Aggregate results and perform GLMM statistical analysis:
```bash
python code/aggregate.py
python code/glmm_analysis.py
python code/analysis.py
```
Output: `data/results/analysis_glmm.json`, `data/results/analysis_validation.json`

### 5. Benchmarking

Run the full end-to-end benchmark with memory profiling:
```bash
python code/run_benchmark.py --output data/results/benchmark_metrics.json
```
*Enforces limits: Wall-clock < 6h, Memory < 7GB.*

## Expected Outputs

After a successful run, the following artifacts will be generated:

| File Path | Description |
|:--- |:--- |
| `data/raw/dataset_manifest.jsonl` | DragMesh-2 manifest |
| `data/generated/` | Generated novel object geometries (URDF/XML) |
| `data/results/eval_logs.csv` | Per-trial evaluation results |
| `data/results/aggregated.csv` | Aggregated success rates |
| `data/results/glmm_summary.json` | GLMM model summary and Odds Ratios |
| `data/results/analysis_validation.json` | Pass/Fail status for SC-001 and SC-005 |
| `data/results/benchmark_metrics.json` | Performance metrics (time, memory) |
| `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml` | Project state and checksums |

## Validation

- **Citation Validation**:
 ```bash
 python code/validate_citations.py
 ```
 Output: `data/results/citations_validation.log`

- **Reproducibility Audit**:
 ```bash
 python code/audit_reproducibility.py
 ```

## Architecture

- **Estimator**: `code/estimator.py` - VirtualTactileEstimator with moving average filter (window=5) and epsilon clamping.
- **Scheduler**: `code/scheduler.py` - AdaptiveRewardScheduler adjusting weights based on $k_{est}$.
- **Environment**: `code/environment.py` - CPU-only PyBullet physics simulation.
- **Generator**: `code/generator.py` - NovelObjectSet for randomized geometries.
- **Analysis**: `code/glmm_analysis.py` - GLMM fitting using `statsmodels`.

## License

Research use only.
