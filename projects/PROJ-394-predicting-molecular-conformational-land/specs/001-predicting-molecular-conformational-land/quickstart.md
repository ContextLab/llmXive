# Quickstart: Predicting Molecular Conformational Landscapes with Variational Autoencoders

## Prerequisites

*   Python 3.11+
*   Conda or Virtualenv
*   `xtb` (GFN2-xTB) installed in system path or via conda.
*   Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-394-predicting-molecular-conformational-land
    ```

2.  **Create Environment**:
    ```bash
    conda create -n conformer-vae python=3.11
    conda activate conformer-vae
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: Ensure `xtb` is installed separately (e.g., `conda install -c conda-forge xtb`).*

## Data Setup

1.  **Download ZINC15**:
    ```bash
    python code/data/download_zinc.py
    ```
    *This fetches the parquet file from the verified HuggingFace URL and computes the checksum.*

2.  **Generate Conformers & Energies** (Test Set):
    ```bash
    python code/data/energy_calc.py --split test
    ```
    *This runs ETKDG and GFN-xTB for the test set (multiple conformers per molecule). May take several hours.*

3.  **Generate Conformers & Energies** (Training Set):
    ```bash
    python code/data/energy_calc.py --split train
    ```
    *This runs ETKDG and GFN-xTB for the training set (multiple conformers per molecule). May take several hours.*

## Training

1.  **Train VAE**:
    ```bash
    python code/train.py --epochs 50 --batch-size 32
    ```
    *Output: `code/models/vae_checkpoint.pt`*

2.  **Train Linear Head**:
    ```bash
    python code/train.py --mode head --epochs 50
    ```
    *Output: `code/models/linear_head.pt`*

## Evaluation

1.  **Run Full Pipeline**:
    ```bash
    python code/evaluate.py
    ```
    *Output: `data/processed/metrics.json` containing Spearman ρ, p-values, baseline comparisons, ablation results, and `workflow_success_rate`.*

2.  **Check Results**:
    *   Open `data/processed/metrics.json` to verify SC-001 (ρ ≥ 0.5) and SC-002 (Baseline ρ ≤ 0.3).

## Troubleshooting

*   **xtb not found**: Ensure `xtb` is in your PATH or installed via conda.
*   **CUDA Error**: The code is designed for CPU only. If you see CUDA errors, ensure `torch` is installed with CPU support only (or set `CUDA_VISIBLE_DEVICES=""`).
*   **Memory Error**: Reduce `--batch-size` in `train.py`.
*   **Timeout**: If the pipeline exceeds 6 hours, reduce the number of conformers in `energy_calc.py` or the number of molecules in the test set.