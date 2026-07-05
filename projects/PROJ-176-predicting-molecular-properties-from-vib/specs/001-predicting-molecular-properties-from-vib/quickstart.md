# Quickstart: Predicting Molecular Properties from Vibrational Spectra

## Prerequisites

- Python 3.11+
- Git
- Sufficient free disk space (for raw data + processed artifacts)
- Sufficient RAM (recommended for smooth processing)

## Installation

1. **Clone the repository** (or navigate to the project root).
   ```bash
   cd projects/PROJ-176-predicting-molecular-properties-from-vib
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins `torch` to a CPU-only version to ensure compatibility with GitHub Actions free-tier runners.*

## Data Download & Preprocessing

Run the ingestion pipeline to download raw data, align datasets, and generate the preprocessed tensor file.

```bash
python code/main.py --step download
python code/main.py --step preprocess
```

- **Output**: `data/processed/aligned_dataset.npz`
- **Expected Time**: 10-20 minutes (depends on network speed).
- **Verification**: The script will print the number of molecules successfully aligned and report any selection bias detected.

## Training the Model

Train the 1-D CNN on the preprocessed data. This step runs on CPU.

```bash
python code/main.py --step train
```

- **Output**: `models/checkpoint_best.pt`, `runs/` (TensorBoard logs).
- **Expected Time**: 1-3 hours (depending on batch size and epochs).
- **Monitoring**: Use `tensorboard --logdir=runs` to view loss curves.
- **Timeout**: The process will automatically terminate if it exceeds a predefined time limit.

## Evaluation

Evaluate the trained model on the held-out test set.

```bash
python code/main.py --step evaluate --checkpoint models/checkpoint_best.pt
```

- **Output**: `results/evaluation_metrics.json`.
- **Content**: MAE, R², TOST p-values, and Hotelling's T² results for dipole, polarizability, and HOMO-LUMO gap.

## Independent Validation (Optional)

If an independent validation dataset is available (e.g., `data/external/val_dataset.npz`), run:

```bash
python code/main.py --step validate --checkpoint models/checkpoint_best.pt --data data/external/val_dataset.npz
```

If no external dataset is available, the `validate` step will automatically run a Domain Shift Simulation.

## Testing

Run the unit and integration tests to verify data alignment, model shape, and statistical outputs.

```bash
pytest tests/ -v
```

## Troubleshooting

- **Memory Error**: Reduce `BATCH_SIZE` in `code/models/trainer.py`.
- **CUDA Error**: Ensure `torch` is the CPU version. Do not install `torch` with `+cu118` or similar.
- **Data Mismatch**: If the alignment count is 0, verify that both raw datasets contain the `InChIKey` column.
- **Timeout**: If the process is killed, check the `timeout` logs in `logs/` to see if the 6-hour limit was reached.