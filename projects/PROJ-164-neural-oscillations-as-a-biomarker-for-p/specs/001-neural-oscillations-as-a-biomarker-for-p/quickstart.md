# Quickstart: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

## Prerequisites

* Python 3.10 or higher
* `pip` package manager
* Internet access (for dataset download)

## Installation

1. **Clone the Repository**  
   ```bash
   git clone <repo-url>
   cd projects/PROJ-164-neural-oscillations-as-a-biomarker-for-p
   ```

2. **Create Virtual Environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**  
   ```bash
   pip install -r requirements.txt
   ```
   *Dependencies include: `mne`, `scikit-learn`, `numpy`, `pandas`, `statsmodels`, `pyyaml`.*

## Running the Pipeline

The pipeline automatically detects data availability and selects the appropriate mode.

```bash
python code/main.py
```

### Expected Outcomes

| Scenario | Log Message | Generated Files |
|----------|-------------|-----------------|
| **Paired dataset found** | `Primary Mode` – preprocessing, modeling, validation run. | `output/artifacts/*`, `output/reports/final_report.md` |
| **No paired dataset** | `Hypothesis Unanswerable: No single-source paired dataset found` (exact required phrase). | `pre_registration.yaml`, `verified_eeg_source.json`, `verified_tdcs_source.json`, `output/reports/final_report.md` |
| **Underpowered** | `Underpowered: Minimum N required = 64, actual N = X` | Same as above, with `power_analysis.json` indicating status. |

### Troubleshooting

* **MemoryError** – The script automatically downsamples epochs if RAM usage approaches 7 GB. You can also manually lower `MAX_EPOCHS` in `code/config.py`.
* **Dataset Not Found / Incompatible** – The pipeline uses the **raw EDF BIDS** version of the PhysioNet Motor Movement/Imagery dataset (`https://physionet.org/content/eegmmidb/1.0.0/`). If the download fails, verify internet connectivity and that the URL is reachable. This source provides **raw voltage recordings** required for the MNE preprocessing pipeline.
* **Hypothesis Unanswerable** – This log entry is **required by the specification** and indicates that no single‑source paired EEG + tDCS dataset exists in the public domain. It does **not** imply the scientific hypothesis is false; it merely reflects data scarcity (classified internally as Data Insufficiency).
* **Generalization Unanswerable** – If the pipeline cannot locate an independent paired dataset for the generalization check, it will log this message. This satisfies the constitutional requirement to attempt a generalization evaluation.

## Next Steps

If you later discover a public dataset that contains both raw EEG and tDCS outcomes, place it under `data/raw/` and re‑run the pipeline; it will automatically switch to **Primary Mode** and perform the full analysis.