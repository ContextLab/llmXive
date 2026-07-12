# Data Model Specification: Latent-Space Jailbreak Detection

**Project**: PROJ-835-llmxive-follow-up-extending-a-survey-of
**Version**: 1.0.0
**Date**: 2024-05-21
**Status**: Draft (Approved for Implementation)

---

## 1. Overview

This document defines the data schemas, storage formats, and structural constraints for the LlmXive follow-up research pipeline. It serves as the contract between the data extraction phase (US1), model training phase (US2), and evaluation phase (US3).

All data artifacts must conform to the schemas defined below to ensure reproducibility and automated validation.

---

## 2. Directory Structure

All data artifacts are stored relative to the project root (`code/../data/`):

```text
data/
├── raw/ # Raw audio files downloaded from source (WAV/FLAC)
│ ├── jailbreak/ # Malicious prompts
│ └── benign/ # Benign prompts
├── processed/ # Pre-processed audio (normalized, trimmed)
│ └── *.npy # Normalized audio waveforms (1D arrays)
├── embeddings/ # Model latent-space embeddings
│ ├── train/ # Training split embeddings
│ ├── test/ # Test split embeddings
│ └── labels.json # Corresponding labels for splits
└── models/ # Trained model artifacts (pickle/pt)
```

---

## 3. Data Schemas

### 3.1. Raw Audio Dataset (`data/raw`)

**Source**: `audio_bench/jailbreak_v1` (via `datasets` library)
**Format**: `.wav` (16kHz, mono, 16-bit PCM)
**Directory Organization**:
- `data/raw/jailbreak/`: Contains audio files for malicious prompts.
- `data/raw/benign/`: Contains audio files for benign prompts.

**File Naming Convention**:
- `<uuid>.wav`
- Example: `a1b2c3d4-e5f6-7890-abcd-ef1234567890.wav`

**Metadata**:
- Labels are inferred from the directory name (`jailbreak` = 1, `benign` = 0).
- A manifest file `data/raw/manifest.json` is generated post-download to track checksums and source hashes.

**Manifest Schema (`data/raw/manifest.json`)**:
```json
{
 "source": "audio_bench/jailbreak_v1",
 "download_date": "ISO-8601",
 "checksums": {
 "sha256": "<hash>"
 },
 "counts": {
 "jailbreak": 1234,
 "benign": 5678
 },
 "files": [
 {
 "filename": "uuid.wav",
 "label": 1,
 "duration_seconds": 4.5,
 "checksum": "<hash>"
 }
 ]
}
```

---

### 3.2. Processed Audio (`data/processed`)

**Format**: NumPy `.npy` (1D float32 array)
**Sampling Rate**: 16,000 Hz (fixed)
**Normalization**: Min-Max scaled to [-1.0, 1.0] or Z-score normalized (configurable).
**Handling of Corrupted Data**: Files that fail loading are skipped and logged; no placeholder data is inserted.

**Schema**:
- Array shape: `(n_samples,)`
- Data type: `float32`
- No NaN or Inf values allowed.

---

### 3.3. Embeddings (`data/embeddings`)

**Source**: `distil-whisper/distil-large-v2` (or fallback `openai/whisper-distil-base`)
**Dimensions**: Fixed vector size (e.g., 768 or 1280 depending on model layer).
**Format**: NumPy `.npy` (2D array) or Parquet.

**File Organization**:
- `data/embeddings/train/embeddings.npy`: Shape `(N_train, D)`
- `data/embeddings/test/embeddings.npy`: Shape `(N_test, D)`
- `data/embeddings/labels.json`: List of integers `[0, 1,...]`

**Embedding Schema (`labels.json`)**:
```json
[
 1,
 0,
 1,
...
]
```

**Embedding Matrix Constraints**:
- Must be contiguous in memory.
- No NaN/Inf values.
- Values must be finite floats.

---

### 3.4. Model Outputs (`data/models`)

**Format**: Pickle (`.pkl`) or Torch (`.pt`)
**Contents**:
- Trained Logistic Regression coefficients and intercept.
- Scaler parameters (if used).
- Training metadata (random seed, split ratio).

**Metadata Schema (`model_meta.json`)**:
```json
{
 "model_type": "LogisticRegression",
 "train_split_ratio": 0.8,
 "random_seed": 42,
 "metrics": {
 "accuracy": 0.95,
 "recall": 0.92,
 "fpr": 0.05,
 "auc_roc": 0.98
 },
 "statistical_test": {
 "name": "McNemar",
 "p_value": 0.012,
 "baseline": "random_guessing"
 }
}
```

---

## 4. Validation Rules

All data loading and processing scripts must enforce the following:

1. **Type Safety**: All numeric arrays must be `float32` or `float64`.
2. **Completeness**: No missing values (NaN) in embeddings or labels.
3. **Consistency**: Number of labels must match number of embedding rows.
4. **Integrity**: Checksums for raw data must match the manifest.
5. **Memory Limits**: Processing must not exceed 6.5 GB peak RAM (enforced by `utils/memory_monitor.py`).

---

## 5. Evolution & Amendments

Any changes to this data model must be documented in `results/methodology_notes.md` and require approval via the amendment process defined in `specs/001-llmxive-follow-up-extending-a-survey-of/amendment_report.md`.

**Current Status**: This document supersedes any informal schema descriptions in `research.md` or `plan.md`.