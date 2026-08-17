# Cross-Modal Comparison of Neural Prediction Error Signals

## Project Overview

This project implements an automated scientific pipeline to compare neural prediction error signals across auditory and visual modalities. It processes real EEG data from OpenNeuro datasets, extracts prediction error metrics (peak latency, mean amplitude), performs source localization, and conducts statistical comparisons.

## ⚠️ CRITICAL DATA POLICY: REAL DATA ONLY

**This project operates under a strict "Real Data Only" constitution.**

- **Mandatory Source**: All data must originate from **OpenNeuro** datasets:
 - **Auditory Modality**: `ds000246`
 - **Visual Modality**: `ds000117`
- **Prohibition**: **SYNTHETIC DATA GENERATION IS STRICTLY PROHIBITED.**
 - No mock data, no simulated signals, and no placeholder datasets are permitted.
 - If the pipeline cannot fetch or validate real data from OpenNeuro, it **MUST fail loudly** and halt execution.
 - There are no fallback mechanisms to synthetic data.
- **Verification**: All data artifacts are validated for sampling rate (≥500 Hz) and trial counts (≥100 oddball, ≥300 standard) immediately upon ingestion. [UNRESOLVED-CLAIM: c_01858454 — status=not_enough_info]

## Installation

1. **Clone the repository**
2. **Create and activate a virtual environment**:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```
3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
4. **Configure environment** (optional):
 ```bash
 cp.env.example.env
 # Edit.env with your settings if necessary
 ```

## Usage

See `docs/quickstart.md` for detailed execution steps.

## Data Sources

| Modality | Dataset ID | Source | Description |
|:--- |:--- |:--- |:--- |
| Auditory | `ds000246` | OpenNeuro | Auditory oddball paradigm |
| Visual | `ds000117` | OpenNeuro | Visual oddball paradigm |

## Compliance

This project adheres to the **llmXive Constitution**, specifically:
- **Principle VII (Validation Independence)**: Using split-half reliability as a proxy where behavioral measures are unavailable in passive paradigms (pending amendment ratification).
- **Real Data Constraint**: No synthetic data generation is permitted; all results must be derived from actual neurophysiological measurements.