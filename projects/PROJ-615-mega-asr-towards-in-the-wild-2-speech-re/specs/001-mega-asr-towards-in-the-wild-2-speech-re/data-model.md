# Data Model: Mega-ASR Reproduction & Validation

## 1. Overview

This document defines the data structures used for input, processing, and output in the Mega-ASR reproduction pipeline. The data flow is designed to be streaming-compatible to adhere to the 7GB RAM constraint.

## 2. Entity Definitions

### 2.1 AudioSample
Represents a single entry in the benchmark dataset. This is the primary input unit.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `id` | `string` | Unique identifier for the sample (optional, generated if missing). | Derived from filename or Parquet index. |
| `audio_path` | `string` | File path or URL to the audio file (WAV/MP3). | Dataset (Parquet/JSONL). |
| `ground_truth` | `string` | The reference transcription text. | Dataset (Parquet/JSONL). |
| `distortion_type` | `string` | Type of acoustic distortion (e.g., "reverberation", "noise"). | Dataset (Parquet/JSONL). |
| `benchmark` | `string` | The benchmark name (e.g., "VOiCES", "NOIZEUS"). | Derived from dataset source. |

### 2.2 Prediction
Represents the output of the inference engine for a single `AudioSample`.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `sample_id` | `string` | Reference to the `AudioSample.id`. | Input `AudioSample`. |
| `transcription` | `string` | The generated text by the ASR model. | Model Output. |
| `confidence` | `float` | (Optional) Model confidence score. | Model Output (if available). |
| `inference_time_ms` | `integer` | Time taken to process this sample in milliseconds. | System Timer. |

### 2.3 MetricReport
Aggregated evaluation result.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `benchmark_name` | `string` | Name of the benchmark evaluated. | Input Configuration. |
| `total_samples` | `integer` | Number of samples processed. | Count. |
| `wer` | `float` | Word Error Rate (0.0 to 1.0+). | Calculated (Prediction vs Ground Truth). |
| `sample_type` | `string` | "Full" or "Sampled". | Input Configuration. |
| `timestamp` | `string` | ISO 8601 timestamp of the run. | System Clock. |
| `wer_ci_lower` | `float` | Lower bound of 95% Confidence Interval for WER. | Calculated (Bootstrap). |
| `wer_ci_upper` | `float` | Upper bound of 95% Confidence Interval for WER. | Calculated (Bootstrap). |

## 3. Data Flow

1.  **Ingestion**: `data_loader.py` reads from Parquet/JSONL in chunks (batch size = 50).
2.  **Validation**: Checks for `audio_path` and `ground_truth`. Checks if `audio_path` resolves to an accessible file. Drops invalid rows with a warning.
3.  **Inference**: `inference.py` processes the batch, generating `Prediction` objects.
4.  **Output**: Predictions are written to `results/sample_predictions.jsonl` immediately.
5.  **Evaluation**: `evaluation.py` reads the predictions and original ground truth to compute `MetricReport` including confidence intervals.

## 4. Constraints

- **Streaming**: No single entity list (e.g., a list of all `AudioSample` objects) shall be held in memory.
- **Serialization**: All intermediate artifacts must be written to disk (JSONL) to free RAM.
- **Encoding**: All text fields must be UTF-8 encoded.
