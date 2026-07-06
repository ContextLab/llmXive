# Quickstart: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

## Prerequisites

- Python 3.11+
- Git
- A Linux environment (or WSL on Windows)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-398-the-impact-of-visual-complexity-on-cogni
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The pipeline consists of three sequential steps:

### Step 1: Extract Visual Complexity Metrics
Process the background images to compute entropy, color variance, and object counts.
```bash
python code/01_extract_metrics.py
```
*Output*: `data/processed/metrics.json`

### Step 2: Generate Synthetic Participant Data
Simulate the study sessions with counterbalanced ordering.
```bash
python code/02_generate_synthetic_data.py
```
*Output*: `data/processed/sessions.csv`

### Step 3: Statistical Analysis
Run the LMM, VIF checks, and sensitivity analysis.
```bash
python code/03_analyze.py
```
*Output*: `data/processed/analysis_results.csv`, `data/processed/report.md`

## Verification

To verify the pipeline works on a CPU-only environment:

1. Ensure no GPU is detected:
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"  # Should print False
   ```
2. Run the metric extraction on a small subset (e.g., 5 images) to check for memory errors.
3. Check the output files for valid numerical values.

## Troubleshooting

- **Memory Error**: If YOLOv8n fails, ensure you are using the `ultralytics` CPU wheel and not a GPU-specific build. Reduce image resolution if necessary.
- **Missing Dependencies**: Re-run `pip install -r code/requirements.txt` ensuring no version conflicts.
- **VIF High**: If VIF > 5, the script will flag it. Review `data/processed/analysis_results.csv` for collinearity warnings.
