# llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

This project implements a discrete world model stack for physical AI, focusing on
quantization effects, stability analysis, and CPU-only training of the Kairos architecture.
It extends the foundational work of "Kairos" by introducing discrete state vectors,
noise injection, and rigorous statistical validation of information density thresholds.

## Quickstart

1. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Initialize Project Structure**:
 ```bash
 bash scripts/scaffold_project.sh
 ```

3. **Run Power Analysis** (to determine sample size N):
 ```bash
 python code/analysis/power_analysis.py
 ```

4. **Execute Data Pipeline** (Download, Derive, Noise, Quantize):
 ```bash
 python code/main.py
 ```

5. **Train and Evaluate** (CPU-only):
 ```bash
 python code/models/baseline_trainer.py
 python code/analysis/run_baseline.py
 ```

## Project Structure

- `code/`: Source code for data processing, model training, and analysis.
- `data/`: Raw and processed datasets (HDF5, JSON).
- `results/`: Analysis outputs, metrics, and visualization figures.
- `tests/`: Unit, integration, and contract tests.
- `specs/`: Design documents and user stories.

## Key Features

- **Discrete Quantization**: Configurable bit-depths (4, 6, 8, 16) for state vectors.
- **Noise Injection**: Gaussian noise modeling telemetry instability.
- **CPU-Only Training**: Optimized for environments without GPU access.
- **Statistical Rigor**: Linear Mixed-Effects Models (LMM) for stability validation.

## Verification

To verify the project setup, ensure the following files exist:
- `code/config.py`
- `data/raw/libero_subset.h5` (after running download)
- `results/power_analysis_report.json` (after running power analysis)

## License

This project is part of the llmXive research initiative.