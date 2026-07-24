import os
import sys
import time
import json
import tracemalloc
import argparse
from pathlib import Path

# Import existing pipeline components
from preprocess import load_config, stream_eeg_files, apply_bandpass_filter, apply_notch_filter, reject_artifacts, process_eeg_stream, save_processed_data
from features import load_config as load_features_config, calculate_lzc, calculate_permutation_entropy, process_eeg_segments, save_metrics_to_csv

# Ensure logs directory exists before any logging attempts
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def profile_function(func, *args, **kwargs):
    """Profile a function's memory usage using tracemalloc."""
    tracemalloc.start()
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return {
        "result": result,
        "peak_memory_mb": peak / 1024 / 1024,
        "wall_time_s": end_time - start_time
    }

def profile_preprocessing_pipeline():
    """Profile the entire preprocessing pipeline for memory usage."""
    print("Starting preprocessing pipeline memory profile...")
    
    # Ensure directories exist
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    
    config = load_config()
    n_participants = config.get("n_threshold", 30)
    
    # Generate synthetic data if real data is insufficient
    # This is required by T026 verification: "If the available real dataset is smaller than N=30, generate synthetic EEG data"
    raw_data_dir = Path("data/raw")
    existing_files = list(raw_data_dir.glob("*.fif"))
    
    if len(existing_files) < n_participants:
        print(f"Generating synthetic EEG data for {n_participants} participants (real data insufficient)...")
        _generate_synthetic_eeg_data(n_participants, raw_data_dir, config)
    
    tracemalloc.start()
    start_time = time.time()
    
    try:
        # Run the actual preprocessing pipeline
        # We call the main logic directly without the main() wrapper to control execution
        process_eeg_stream(
            raw_dir=raw_data_dir,
            processed_dir=Path("data/processed"),
            config=config
        )
        
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        profile_report = {
            "stage": "preprocessing",
            "peak_memory_mb": peak / 1024 / 1024,
            "wall_time_s": end_time - start_time,
            "participants_processed": n_participants,
            "status": "success"
        }
        
        # Save report
        report_path = Path("profile_report.json")
        with open(report_path, "w") as f:
            json.dump(profile_report, f, indent=2)
        
        print(f"Preprocessing profile complete. Peak memory: {profile_report['peak_memory_mb']:.2f} MB")
        return profile_report
        
    except Exception as e:
        tracemalloc.stop()
        print(f"Preprocessing profile failed: {str(e)}")
        return {
            "stage": "preprocessing",
            "status": "failed",
            "error": str(e)
        }

def profile_feature_extraction_pipeline():
    """Profile the feature extraction pipeline for memory usage."""
    print("Starting feature extraction pipeline memory profile...")
    
    # Ensure directories exist
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    
    config = load_features_config()
    n_participants = config.get("n_threshold", 30)
    
    # Check if preprocessed data exists
    processed_data_dir = Path("data/processed")
    cleaned_eeg = processed_data_dir / "cleaned_eeg.fif"
    
    if not cleaned_eeg.exists():
        print("Preprocessed data not found. Running preprocessing first...")
        profile_preprocessing_pipeline()
    
    tracemalloc.start()
    start_time = time.time()
    
    try:
        # Run feature extraction
        save_metrics_to_csv(
            processed_dir=processed_data_dir,
            output_dir=processed_data_dir,
            config=config
        )
        
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        profile_report = {
            "stage": "feature_extraction",
            "peak_memory_mb": peak / 1024 / 1024,
            "wall_time_s": end_time - start_time,
            "participants_processed": n_participants,
            "status": "success"
        }
        
        # Append to existing report or create new
        report_path = Path("profile_report.json")
        if report_path.exists():
            with open(report_path, "r") as f:
                existing_report = json.load(f)
                if isinstance(existing_report, dict) and "stages" not in existing_report:
                    existing_report = {"stages": [existing_report]}
                if "stages" not in existing_report:
                    existing_report["stages"] = []
                existing_report["stages"].append(profile_report)
        else:
            existing_report = {"stages": [profile_report]}
        
        with open(report_path, "w") as f:
            json.dump(existing_report, f, indent=2)
        
        print(f"Feature extraction profile complete. Peak memory: {profile_report['peak_memory_mb']:.2f} MB")
        return profile_report
        
    except Exception as e:
        tracemalloc.stop()
        print(f"Feature extraction profile failed: {str(e)}")
        return {
            "stage": "feature_extraction",
            "status": "failed",
            "error": str(e)
        }

def _generate_synthetic_eeg_data(n_participants, output_dir, config):
    """Generate synthetic EEG data for testing memory profiling when real data is insufficient.
    
    This is REQUIRED by T026 verification: 'If the available real dataset is smaller than N=30, 
    generate synthetic EEG data to reach N=30 participants for the purpose of this memory test.'
    
    IMPORTANT: This synthetic data is ONLY for MEMORY PROFILING verification, not for research results.
    The actual research pipeline will fail if real data is not available, as per the 'Real data only' constraint.
    """
    import numpy as np
    import mne
    
    sampling_rate = config.get("sampling_rate", 256)
    duration = config.get("segment_duration", 120)  # seconds
    n_channels = 19  # Standard EEG channels
    channel_names = [f'EEG {i:03d}' for i in range(n_channels)]
    
    info = mne.create_info(ch_names=channel_names, sfreq=sampling_rate, ch_types='eeg')
    
    for i in range(n_participants):
        participant_id = f"sub-{i:03d}"
        
        # Generate 120 seconds of synthetic EEG data
        # Using realistic amplitude ranges (10-100 µV)
        data = np.random.randn(n_channels, sampling_rate * duration) * 50  # 50 µV std dev
        
        # Add some realistic structure: alpha rhythm (8-12 Hz) for some channels
        time_vector = np.linspace(0, duration, sampling_rate * duration)
        for ch_idx, ch_name in enumerate(channel_names):
            if 'O' in ch_name or 'P' in ch_name:  # Occipital/parietal channels
                alpha = np.sin(2 * np.pi * 10 * time_vector) * 20  # 10 Hz alpha, 20 µV amplitude
                data[ch_idx] += alpha
        
        raw = mne.io.RawArray(data, info)
        raw.save(output_dir / f"{participant_id}_eeg.fif", overwrite=True)
        
    print(f"Generated {n_participants} synthetic EEG files in {output_dir}")

def main():
    """Main entry point for memory profiling."""
    parser = argparse.ArgumentParser(description="Profile memory usage of the EEG analysis pipeline")
    parser.add_argument("--stage", choices=["preprocessing", "features", "all"], default="all",
                      help="Which pipeline stage to profile")
    args = parser.parse_args()
    
    results = {}
    
    if args.stage in ["preprocessing", "all"]:
        results["preprocessing"] = profile_preprocessing_pipeline()
    
    if args.stage in ["features", "all"]:
        results["features"] = profile_feature_extraction_pipeline()
    
    # Final validation: check memory constraint (DC-001: peak memory ≤ 7 GB)
    max_memory_gb = 7.0
    failed_stages = []
    
    for stage, result in results.items():
        if result.get("status") == "success":
            peak_mb = result.get("peak_memory_mb", 0)
            peak_gb = peak_mb / 1024
            if peak_gb > max_memory_gb:
                failed_stages.append(f"{stage} ({peak_gb:.2f} GB > {max_memory_gb} GB)")
            else:
                print(f"✓ {stage}: {peak_gb:.2f} GB ≤ {max_memory_gb} GB (PASS)")
        else:
            failed_stages.append(f"{stage}: FAILED")
    
    if failed_stages:
        print(f"\n✗ Memory profiling FAILED for: {', '.join(failed_stages)}")
        sys.exit(1)
    else:
        print(f"\n✓ All stages passed memory constraint (≤ {max_memory_gb} GB)")
        sys.exit(0)

if __name__ == "__main__":
    main()
