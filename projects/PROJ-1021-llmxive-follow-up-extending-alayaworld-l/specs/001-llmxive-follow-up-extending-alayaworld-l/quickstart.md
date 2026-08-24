# Quickstart: llmXive follow-up: extending "AlayaWorld: Long-Horizon and Playable Video World Generation"

## Prerequisites

- Python 3.11+
- CPU cores, 7 GB RAM available (GitHub Actions free-tier or local equivalent).
- AlayaWorld model weights (provided as local artifact or internal path).
- A subset of video sequences for testing.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/code
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` includes `torch` (CPU), `opencv-python-headless`, `scikit-learn`, `pandas`, `numpy`, `pytest`.*

## Configuration

1. **Set up paths**:
   Edit `code/config.py` to point to the local AlayaWorld model and video data:
   ```python
   MODEL_PATH = "/path/to/alayaworld/model.pth"
   DATA_PATH = "/path/to/alayaworld/data"
   GROUND_TRUTH_PATH = "data/ground_truth"
   ```

2. **Set random seeds**:
   Ensure `config.py` defines a fixed seed for reproducibility:
   ```python
   RANDOM_SEED = 42
   ```

## Running the Pipeline

### 1. Generate Ground Truth Subset (Manual Step)
   - Run the symbolic engine to generate state logs for ≥50 frames.
   - Save annotations in `data/ground_truth/annotations.json` following the schema in `contracts/cv_annotation.schema.yaml`.

### 2. Run Ground Truth Validation (FR-007)
   ```bash
   python -m code.validation --mode validate
   ```
   *Output: A report indicating if CV accuracy ≥ 85%. If not, the experiment is invalid.*

### 3. Run Baseline (US-1)
   ```bash
   python -m code.main --mode baseline --seeds multiple
   ```
   *Output: `data/results/baseline_scores.json`*

### 4. Run Hybrid (US-2)
   ```bash
   python -m code.main --mode hybrid --seeds multiple
   ```
   *Output: `data/results/hybrid_scores.json`*

### 5. Statistical Analysis (US-2)
   ```bash
   python -m code.metrics --compare baseline hybrid
   ```
   *Output: Statistical report including p-value and drift score reduction (Wilcoxon signed-rank test).*

### 6. Resource Check (US-3)
   Resource usage is logged automatically during runs. Check `data/results/resource_logs.json` to ensure:
   - Peak RAM ≤ 7 GB
   - Wall-clock time ≤ 30 minutes per sequence

## Verification

- **Check Drift Reduction**: Verify that the mean drift score for the hybrid mode is at least 30% lower than the baseline (SC-001).
- **Check Significance**: Ensure the p-value from the **Wilcoxon signed-rank test** is < 0.05 (SC-004).
- **Check Constraints**: Ensure all resource logs are within limits (SC-002, SC-003).

## Troubleshooting

- **Memory Error**: If the process exceeds 7 GB RAM, reduce the batch size in `config.py` or enable streaming mode.
- **CV Accuracy Low**: If validation accuracy < 85%, re-annotate the ground truth or adjust template matching parameters in `code/cv_pipeline.py`.
- **Model Not Found**: Ensure `MODEL_PATH` in `config.py` points to a valid, CPU-compatible model file.