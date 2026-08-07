# Data Model: 001-garment-text-fidelity

## 1. Conceptual Overview

The data model tracks the flow from raw image samples to stratified inference results. The core entities are `GarmentFeatureClass`, `FidelityScore`, and `InferenceLog`.

### Key Entities

1.  **GarmentFeatureClass**: Enum (`COLOR`, `PATTERN`, `TEXTURE`). Represents the semantic attribute being tested, derived from DeepFashion2 metadata and verified by MobileCLIP.
2.  **TextPrompt**: String. The natural language description generated from DeepFashion2 attributes (e.g., "A person wearing a plaid shirt").
3.  **FidelityScore**: Float. The result of LPIPS or SSIM comparison.
4.  **InferenceLog**: Structured record of a single sample's processing (latency, scores).

## 2. Logical Schema

### Input Data (Streaming)
*   `image_id`: String (Unique identifier from DeepFashion2).
*   `frame_index`: Integer (Always 0 for static images).
*   `feature_class`: String (Derived from DeepFashion2 metadata: `COLOR` | `PATTERN` | `TEXTURE`).
*   `text_prompt`: String (Generated from metadata).
*   `ground_truth_frame`: Image tensor (from dataset).
*   `visual_confirmed`: Boolean (True if MobileCLIP verifies prompt-image alignment).

### Intermediate Results (Batched)
*   `generated_frame`: Image tensor (output of model).
*   `latency_ms`: Float.

### Output Aggregates
*   `mean_lpips`: Float (per feature class).
*   `mean_ssim`: Float (per feature class).
*   `p_value`: Float (ANOVA result).
*   `latency_pass`: Boolean (True if <= 50ms).

## 3. Physical Data Layout

```text
data/
├── raw/
│   └── deepfashion2_stream/       # (Virtual stream, not stored)
├── processed/
│   ├── benchmark_subset.jsonl # (samples with metadata-derived tags + visual confirmation)
│   └── inference_results/
│       ├── batch_001.json
│       ├── batch_002.json
│       └── ...
└── reports/
    ├── fidelity_report.json   # Aggregated scores per class
    ├── stats_report.json      # ANOVA results
    └── latency_report.json    # Per-sample latency logs
```

## 4. Data Lineage & Hygiene

1.  **Source**: DeepFashion2 (Hugging Face).
2.  **Transformation**: `stratifier.py` derives `feature_class` and `text_prompt` from metadata.
3.  **Verification**: `stratifier.py` uses MobileCLIP to set `visual_confirmed`.
4.  **Processing**: `runner.py` generates frames and computes metrics.
5.  **Aggregation**: `stats.py` computes ANOVA.
6.  **Checksums**: All `inference_results/*.json` files are checksummed and recorded in `data/manifest.json`.

**Constraint**: No raw image frames are stored on disk; they are streamed, processed, and discarded to save space. Only metrics and logs are persisted.