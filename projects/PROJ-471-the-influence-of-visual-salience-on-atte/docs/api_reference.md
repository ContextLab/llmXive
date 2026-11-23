# API Reference

This document lists the public APIs exposed by the project modules.

## `code/config.py`
- `load_config()`: Loads YAML config.
- `get_paths()`: Returns `Paths` object.
- `get_hyperparams()`: Returns `Hyperparams` object.

## `code/ingestion/download_data.py`
- `fetch_dataset()`: Downloads dataset from Hugging Face.
- `validate_and_cache_images()`: Verifies checksums.

## `code/ingestion/salience_gen.py`
- `load_deepgaze_model()`: Loads DeepGaze II in CPU mode.
- `generate_salience_map()`: Generates map for an image.
- `process_image_with_monitoring()`: Runs generation with memory/CPU monitoring.

## `code/ingestion/fallback_heuristic.py`
- `run_gvs()`: Runs GBVS algorithm.
- `compute_contrast_map()`: Computes contrast-based salience.

## `code/processing/segmentation.py`
- `run_yolo_segmentation()`: Generates face masks.
- `generate_face_mask()`: Extracts face ROI.

## `code/processing/eye_tracking.py`
- `parse_raw_eye_tracking_file()`: Reads TSV files.
- `calculate_metrics()`: Computes dwell time, latency, etc.

## `code/analysis/lmm_fit.py`
- `fit_model_a()`: Fits random intercepts model.
- `fit_model_b()`: Fits random intercepts + slopes model.
- `check_power_gate()`: Verifies power > 0.8.

## `code/analysis/vif_calc.py`
- `calculate_vif()`: Computes Variance Inflation Factor.
- `write_vif_report()`: Saves VIF results.

## `code/analysis/robustness.py`
- `run_sensitivity_analysis()`: Compares Model A vs B.
- `compare_model_significance()`: Tests significance differences.

## `code/utils/logging.py`
- `get_logger()`: Returns configured logger.
- `setup_logging()`: Initializes logging infrastructure.

## `code/utils/versioning.py`
- `compute_sha256()`: Computes file hash.
- `register_artifact()`: Adds artifact to `state.yaml`.
