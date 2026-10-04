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
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: `requirements.txt` pins `torch` to a CPU-only version to ensure compatibility with GitHub Actions free-tier runners.*

## Data Download & Preprocessing

Run the ingestion pipeline to download raw data, align datasets, and generate the preprocessed tensor file.

```bash
python code/main.py download
python code/main.py preprocess
```

- **Output**: `data/preprocessed/aligned_dataset.npz`
- **Expected Time**: 10-20 minutes (depends on network speed).
- **Verification**: The script will print the number of molecules successfully aligned and report any selection bias detected.

### Data Download Details

The `download` step fetches data from the following verified sources:
- **QM9**: Downloaded via the `datasets` library (Hugging Face) or direct URL as defined in `code/data/download.py`.
- **IR-Spectra**: Downloaded from the specified external repository.

### Preprocessing Steps

The `preprocess` step performs the following transformations:
1. **Alignment**: Inner join of QM9 and IR-spectra datasets on `InChIKey`.
2. **Interpolation**: Spectra are interpolated to a fixed grid covering the mid-infrared region (400–4000 cm⁻¹) with 1 cm⁻¹ spacing.
3. **Smoothing**: Gaussian smoothing applied with $\sigma = 2 \text{ cm}^{-1}$.
4. **Normalization**: Unit area normalization applied to spectra.
5. **Filtering**: Molecules missing dipole, polarizability, or HOMO-LUMO gap are removed.
6. **Audit**: Coverage audit (KS-test) performed to detect selection bias.

## Training the Model

Train the 1-D CNN on the preprocessed data. This step runs on CPU.

```bash
python code/main.py train
```

- **Output**: `models/checkpoint_best.pt`, `runs/` (TensorBoard logs).
- **Expected Time**: 1-3 hours (depending on batch size and epochs).
- **Monitoring**: Use `tensorboard --logdir=runs` to view loss curves.
- **Timeout**: The process will automatically terminate if it exceeds a predefined time limit (6 hours).

### Hyperparameters

The following hyperparameters are used during model training:

| Parameter | Value | Description |
|:--- |:--- |:--- |
| **Learning Rate** | `1e-3` | Initial learning rate for Adam optimizer |
| **Patience** | `10` | Early stopping patience (monitoring `val_loss`) |
| **Kernel Size (Block 1)** | `9` | First convolutional block kernel size |
| **Kernel Size (Block 2)** | `7` | Second convolutional block kernel size |
| **Kernel Size (Block 3)** | `5` | Third convolutional block kernel size |
| **Filters (All Blocks)** | `64` | Number of filters in each convolutional block |
| **Optimizer** | `Adam` | Optimizer type |
| **Device** | `CPU` | Execution device (CUDA explicitly disabled) |
| **Smoothing $\sigma$** | `2` | Gaussian smoothing standard deviation ($cm^{-1}$) |
| **Wavenumber Range** | `400–4000` | Mid-infrared region (cm⁻¹) |
| **Grid Spacing** | `1` | Interpolation step size (cm⁻¹) |

## Evaluation

Evaluate the trained model on the held-out test set.

```bash
python code/main.py evaluate --checkpoint models/checkpoint_best.pt
```

- **Output**: `results/evaluation_metrics.json`.
- **Content**: MAE, R², TOST p-values, and Hotelling's T² results for dipole, polarizability, and HOMO-LUMO gap.
- **Validation**: Includes paired-sample t-tests to check for systematic bias (p < 0.01 threshold).

## Independent Validation (Optional)

If an independent validation dataset is available (e.g., `data/external/val_dataset.npz`), run:

```bash
python code/main.py validate --checkpoint models/checkpoint_best.pt --data data/external/val_dataset.npz
```

If no external dataset is available, the `validate` step will automatically run a Domain Shift Simulation (fallback) or fail loudly if real data is strictly required by configuration.

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
- **Missing External Data**: If validation fails due to missing data, ensure `data/external/` contains the required `.npz` file or adjust configuration to allow synthetic fallback.