"""
Robustness Analysis Script (T026)

Re-runs the feature extraction and modeling pipeline with alternative parameters
to test the stability of results against the primary analysis:
1. Shorter time windows (2s instead of 4s) for Welch's PSD.
2. Skipping ICA cleaning (using data pre-T010b or re-running preprocessing without ICA).

Outputs:
- data/processed/robustness_features.csv: Features extracted with 2s windows (no ICA).
- data/processed/robustness_model_results.json: Model metrics (R2, RMSE) for robustness check.
- data/processed/robustness_report.csv: Comparison of primary vs robustness metrics.
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
import mne
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_path, get_band_freqs, get_all_band_names, get_filter_params, ensure_dirs, get_seed
from utils.eeg_helpers import bandpass_filter, notch_filter, reject_channels_by_variance
# Note: We intentionally do NOT import apply_ica from eeg_helpers for the robustness run
# to simulate the "without ICA" condition. We rely on the base preprocessing (T010) 
# which applies bandpass/notch/variance rejection but stops before ICA if we re-run logic,
# OR we assume the input data is the raw/pre-baseline state. 
# Given the pipeline flow, T010 produces data with ICA removed in T010b.
# To do "without ICA", we must re-load the raw data and apply T010 logic manually 
# (skipping ICA) or use the pre-ICA intermediate if stored. 
# Since the spec implies re-running the pipeline, we will re-implement the 
# preprocessing steps (Bandpass, Notch, Variance) without ICA here.

# We will also need to re-extract features with 2s windows.
# We will need to re-run a simple model to compare R2.

def load_raw_eeg_data(subject_id: int, data_dir: Path) -> Optional[mne.io.BaseRaw]:
    """
    Loads raw EEG data for a subject from PhysioNet structure.
    This bypasses the preprocessed files to allow re-applying filters without ICA.
    """
    # PhysioNet EEG Motor Movement/Imagery structure:
    # sub-<id>/eeg/sub-<id>_task-<task>_run-<run>_eeg.edf
    # We look for the first available run (usually 1 or 2)
    subj_dir = data_dir / f"sub-{subject_id:03d}" / "eeg"
    if not subj_dir.exists():
        return None
    
    edf_files = list(subj_dir.glob("*.edf"))
    if not edf_files:
        # Try .vhdr if converted, but PhysioNet is usually .edf
        edf_files = list(subj_dir.glob("*.vhdr"))
    
    if not edf_files:
        return None

    # Pick the first run (usually task-rest or similar)
    # We assume the first file is the one we want for this robustness check
    try:
        raw = mne.io.read_raw_edf(str(edf_files[0]), preload=True, verbose=False)
        # Standardize montage if needed (PhysioNet often has standard 64/128)
        # We'll rely on the montage embedded or standard 10-20 if available
        # For robustness, we just need the data.
        return raw
    except Exception:
        try:
            raw = mne.io.read_raw_brainvision(str(edf_files[0]), preload=True, verbose=False)
            return raw
        except Exception:
            return None

def preprocess_without_ica(raw: mne.io.BaseRaw, params: Dict[str, Any]) -> mne.io.BaseRaw:
    """
    Applies Bandpass, Notch, and Variance Rejection (T010 logic) but SKIPS ICA (T010b).
    """
    # 1. Bandpass (1-40Hz)
    raw = bandpass_filter(raw, params['low_cut'], params['high_cut'])
    
    # 2. Notch (50Hz or 60Hz)
    raw = notch_filter(raw, params['notch_freq'])
    
    # 3. Variance Rejection
    # We need to detect bad channels and drop them
    # eeg_helpers.reject_channels_by_variance expects a raw object
    # It returns a new raw object with bads dropped
    raw_clean = reject_channels_by_variance(raw, threshold_sd=params['variance_threshold_sd'])
    
    return raw_clean

def compute_welch_psd_2s(raw: mne.io.BaseRaw, window_sec: float = 2.0) -> Dict[str, Any]:
    """
    Computes Welch's PSD with 2-second windows (instead of 4s).
    Returns average PSD per band per channel.
    """
    sfreq = raw.info['sfreq']
    data = raw.get_data()
    ch_names = raw.ch_names
    n_channels = len(ch_names)
    
    # Welch parameters
    nperseg = int(window_sec * sfreq)
    noverlap = int(nperseg * 0.5) # 50% overlap as per T012 deferred logic (2s overlap for 4s, so 1s for 2s? 
    # T012 said "4-second windows with [deferred] overlap (2s)". 
    # If we use 2s windows, a logical overlap is 1s (50%) or 0s. 
    # Let's stick to 50% overlap relative to window size.
    
    psds = []
    
    for i in range(n_channels):
        f, Pxx = mne.time_frequency.psd_welch(
            raw, 
            fmin=1.0, 
            fmax=40.0, 
            n_per_seg=nperseg, 
            n_overlap=noverlap,
            verbose=False
        )
        psds.append(Pxx[i]) # Shape: (n_freqs,)
    
    # psds is now (n_channels, n_freqs)
    psds = np.array(psds)
    
    return {
        'f': f,
        'psd': psds,
        'ch_names': ch_names
    }

def aggregate_band_power_robust(psd_data: Dict[str, Any], band_freqs: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
    """
    Aggregates PSD into band powers (mean power in frequency range).
    """
    f = psd_data['f']
    psd = psd_data['psd'] # (n_channels, n_freqs)
    ch_names = psd_data['ch_names']
    
    band_powers = {}
    
    for band_name, (f_min, f_max) in band_freqs.items():
        # Find indices
        idx = np.where((f >= f_min) & (f <= f_max))[0]
        if len(idx) == 0:
            continue
        
        # Mean power across frequencies for all channels
        # Then average across channels? Or keep per channel?
        # T012 aggregated to one row per participant. So we average across channels too.
        band_power = np.mean(psd[:, idx])
        band_powers[band_name] = band_power
        
    # Also compute total power for relative calculation
    all_idx = np.where((f >= 1.0) & (f <= 40.0))[0]
    total_power = np.mean(psd[:, all_idx])
    band_powers['total_power'] = total_power
    
    return band_powers

def run_robustness_pipeline():
    """
    Main execution flow for T026.
    1. Load raw data.
    2. Preprocess WITHOUT ICA.
    3. Extract features with 2s windows.
    4. Load behavioral data (median RT) from existing processed files (T013).
    5. Merge and run a simple Linear Regression (sklearn) to get R2.
    6. Compare with primary results (if available) and save report.
    """
    print("Starting Robustness Analysis (T026)...")
    
    # Paths
    raw_data_dir = get_path('raw_data')
    proc_data_dir = get_path('processed_data')
    ensure_dirs([proc_data_dir])
    
    # Load config
    band_freqs = get_band_freqs()
    filter_params = get_filter_params()
    seed = get_seed()
    np.random.seed(seed)
    
    # 1. Identify subjects with behavioral data
    # We assume T013 produced data/processed/behavioral_metrics.csv
    behavioral_path = get_path('behavioral_metrics')
    if not behavioral_path.exists():
        print(f"Error: Behavioral metrics not found at {behavioral_path}. Cannot run robustness.")
        return
    
    behavioral_df = pd.read_csv(behavioral_path)
    subject_ids = behavioral_df['participant_id'].unique()
    
    robustness_features = []
    
    print(f"Processing {len(subject_ids)} subjects for robustness check (No ICA, 2s windows)...")
    
    for subj_id in subject_ids:
        # Load Raw
        raw = load_raw_eeg_data(subj_id, raw_data_dir)
        if raw is None:
            continue
        
        # Preprocess WITHOUT ICA
        try:
            raw_clean = preprocess_without_ica(raw, filter_params)
        except Exception as e:
            print(f"Skipping {subj_id} due to preprocessing error: {e}")
            continue
        
        # Check if we have enough channels left
        if len(raw_clean.ch_names) < 4: # Arbitrary minimum
            continue
        
        # Extract Features (2s windows)
        try:
            psd_data = compute_welch_psd_2s(raw_clean, window_sec=2.0)
            band_powers = aggregate_band_power_robust(psd_data, band_freqs)
            
            # Add subject ID
            row = {'participant_id': subj_id}
            row.update(band_powers)
            robustness_features.append(row)
        except Exception as e:
            print(f"Skipping {subj_id} due to feature extraction error: {e}")
            continue
    
    if not robustness_features:
        print("No features extracted for robustness analysis.")
        return
    
    features_df = pd.DataFrame(robustness_features)
    output_features_path = proc_data_dir / "robustness_features.csv"
    features_df.to_csv(output_features_path, index=False)
    print(f"Saved robustness features to {output_features_path}")
    
    # 2. Merge with Behavioral Data
    # Merge on participant_id
    merged_df = pd.merge(features_df, behavioral_df[['participant_id', 'median_rt']], on='participant_id', how='inner')
    
    if len(merged_df) < 5:
        print("Insufficient data points for modeling after merge.")
        return
    
    # 3. Simple Linear Regression (R2)
    # We use the same bands as primary: delta, theta, alpha, low_beta, high_beta, gamma
    bands = get_all_band_names()
    # Ensure we have these columns
    available_bands = [b for b in bands if b in merged_df.columns]
    if not available_bands:
        print("No band power columns found.")
        return
    
    X = merged_df[available_bands].values
    y = merged_df['median_rt'].values
    
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import train_test_split
    
    # Split 80/20 to match primary (T017)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=seed)
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    from sklearn.metrics import r2_score, mean_squared_error
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    robust_results = {
        "window_size_sec": 2.0,
        "ica_applied": False,
        "r2": float(r2),
        "rmse": float(rmse),
        "n_subjects": len(merged_df),
        "bands_used": available_bands
    }
    
    results_path = proc_data_dir / "robustness_model_results.json"
    with open(results_path, 'w') as f:
        json.dump(robust_results, f, indent=2)
    print(f"Saved robustness model results to {results_path}")
    
    # 4. Compare with Primary Results (if available)
    # Primary results are in data/processed/model_results.json (T017/T019)
    primary_results_path = get_path('model_results')
    comparison_data = []
    
    if primary_results_path.exists():
        try:
            with open(primary_results_path, 'r') as f:
                primary_res = json.load(f)
            # primary_res might be a list or dict. T019 says "save_results" -> model_results.json
            # Assuming it's a dict or list of dicts. Let's handle both.
            if isinstance(primary_res, list):
                primary_res = primary_res[0] if primary_res else {}
            
            p_r2 = primary_res.get('r2', None)
            p_rmse = primary_res.get('rmse', None)
            p_window = primary_res.get('window_size_sec', 4.0)
            p_ica = primary_res.get('ica_applied', True)
            
            comparison_data.append({
                "analysis": "primary",
                "window_sec": p_window,
                "ica": p_ica,
                "r2": p_r2,
                "rmse": p_rmse
            })
        except Exception as e:
            print(f"Could not load primary results for comparison: {e}")
    
    comparison_data.append({
        "analysis": "robustness",
        "window_sec": 2.0,
        "ica": False,
        "r2": r2,
        "rmse": rmse
    })
    
    comp_df = pd.DataFrame(comparison_data)
    report_path = proc_data_dir / "robustness_report.csv"
    comp_df.to_csv(report_path, index=False)
    print(f"Saved robustness report to {report_path}")
    
    print("Robustness Analysis (T026) completed successfully.")

def main():
    run_robustness_pipeline()

if __name__ == "__main__":
    main()
