# Quickstart: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Prerequisites

- **OS**: Linux (Ubuntu 22.04 recommended)
- **Python**: 3.11+
- **RAM**: 7GB+ (for streaming)
- **Disk**: 14GB+ (for video cache)
- **GPU**: None required (CPU-only)

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-812-llmxive-follow-up-extending-anyflow-any
    ```

2.  **Create a virtual environment** and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `onnxruntime`, `opencv-python`, `pyscenedetect`, `pandas`, `scikit-learn`, `scipy`, `datasets`.*

3.  **Verify Dataset Availability**:
    - Check `research.md` for the list of verified video datasets.
    - **CRITICAL**: If no verified URL is present for UCF101/Kinetics/DAVIS, the pipeline will fail. Ensure a verified source is added to the `research.md` block before proceeding.

## Execution Workflow

### Phase 1: Data Curation & Annotation
1.  **Download & Stratify**:
    ```bash
    python code/download_curation.py --source <verified_dataset_id> --stratify --output data/raw/
    ```
    - Runs PySceneDetect, stratified sampling (balanced).
    - Outputs `data/raw/clips.csv`.

2.  **Manual Annotation**:
    - Open `code/annotation_tool.py` (GUI or CLI).
    - Annotate clips using a Likert rubric.
    - System checks Cohen's Kappa. If < 0.81, it halts.
    - Output: `data/annotations/manual_continuity_scores.csv`.

### Phase 2: CPU Inference
1.  **Run Pilot**:
    ```bash
    python code/inference_cpu.py --mode pilot --n_clips [selected_count]
    ```
    - Estimates runtime. If > 5.5h, reduces N to 200.

2.  **Full Inference**:
    ```bash
    python code/inference_cpu.py --mode full --n_clips <NUM_CLIPS>
    ```
    - Computes divergence scores.
    - Output: `data/processed/divergence_scores.csv`.

### Phase 3: Analysis & Validation
1.  **Statistical Analysis**:
    ```bash
    python code/analysis_stats.py
    ```
    - Performs correlation, regression, sensitivity analysis.
    - Output: `artifacts/final_report_manifest.json`, `artifacts/power_analysis_report.md`.

2.  **Synthetic Validation**:
    ```bash
    python code/validation.py --mode synthetic
    ```
    - Validates false-positive/negative rates.
    - Output: `artifacts/synthetic_validation_report.md`.

## Verification

1.  **Check Artifacts**: Ensure all files listed in `final_report_manifest.json` exist and checksums match.
2.  **Check Kappa**: Verify `adjudication_log.csv` shows Kappa ≥ 0.81.
3.  **Check Runtime**: Ensure total runtime < 6 hours (recorded in `runtime_pilot_report.md`).

## Troubleshooting

- **Memory Error**: Ensure `streaming=True` is used in `datasets.load_dataset`. Reduce batch size.
- **Runtime Error**: If N=500 is too slow, the pilot should have auto-reduced to N=200. Check `runtime_pilot_report.md`.
- **No Data**: If the script fails to find a dataset, verify the `research.md` "Verified datasets" block contains a valid Hugging Face video dataset URL.
