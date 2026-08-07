# Quick Start Guide: Non-Neural VLA Approximation Pipeline

## Prerequisites
- Python 3.9+
- pip
- System RAM ≥ 7GB
- No GPU required (CPU-only execution)

## Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
 Dependencies include: `datasets`, `scikit-learn`, `transformers`, `pybullet`, `pandas`, `numpy`, `scipy`, `pyyaml`.

## Directory Structure
The project uses the following structure:
- `code/`: Pipeline scripts and utilities
- `data/raw/`: Raw downloaded datasets
- `data/processed/`: Intermediate processed data (embeddings, clusters)
- `data/results/`: Final evaluation reports and logs
- `artifacts/models/`: Trained model weights and encoders

## Running the Pipeline

### Option 1: Full End-to-End Validation (Recommended)
Run the complete pipeline from ingestion to final report generation:
```bash
python code/09_run_final_validation.py --seed 42
```
This will:
1. Ingest and cluster the dataset.
2. Train DT and CGMM models.
3. Run inference and simulation.
4. Generate evaluation reports.
5. Verify all artifacts.

Output logs are saved to `data/results/final_validation.log`.

### Option 2: Individual Stages
You can run stages independently if needed:

**1. Ingestion & Clustering**
```bash
python code/01_ingest.py
python code/02_cluster.py
```

**2. Training**
```bash
python code/03_train.py
```

**3. Inference**
```bash
python code/04_inference.py
```

**4. Simulation & Evaluation**
```bash
python code/05_simulate.py
python code/06_evaluate.py
```

**5. Report Generation**
```bash
python code/08_generate_report.py
```

## Output Artifacts
Upon successful completion, verify the following files:
- `data/results/evaluation_report.md`: Final statistical comparison.
- `data/results/fidelity_metrics.json`: Trajectory fidelity scores.
- `data/results/simulation_logs.csv`: Detailed simulation outcomes.
- `artifacts/models/`: Trained models for each cluster.

## Troubleshooting
- **Memory Errors**: Ensure you are running on a machine with ≥7GB RAM. The pipeline uses streaming for large datasets.
- **Missing Data**: Ensure the HuggingFace dataset `Qwen-VLA/Hy-Embodied` is accessible.
- **Clustering Failures**: If K-Means fails, the pipeline automatically switches to HAC. Check `data/results/clustering_method_log.json`.
