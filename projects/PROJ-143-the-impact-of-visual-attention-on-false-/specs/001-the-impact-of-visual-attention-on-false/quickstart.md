# Quickstart: The Impact of Visual Attention on False Memory Formation

## Prerequisites

- Python 3.11+
- Git
- **A verified URL for Visual Genome, SALICON, and OpenNeuro (or a plan to re-scope the project).**
- **IRB approval and consent forms in `data/ethics/` (if using human recall data).**

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-143-the-impact-of-visual-attention-on-false-
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

## Data Setup

> **Critical**: You must provide a verified URL for Visual Genome, SALICON, and OpenNeuro. If not, the project cannot proceed.

1. **Download Visual Genome**:
   ```bash
   python src/data/download.py --dataset visual-genome --url <verified-url>
   ```

2. **Download SALICON**:
   ```bash
   python src/data/download.py --dataset salicon --url <verified-url>
   ```

3. **Download Recall Transcripts**:
   ```bash
   python src/data/download.py --dataset openneuro --url <verified-url>
   ```

## Running the Pipeline

1. **Preprocess data**:
   ```bash
   python src/data/preprocessing.py
   ```

2. **Align data**:
   ```bash
   python src/data/linking.py
   ```

3. **Compute saliency**:
   ```bash
   python src/analysis/saliency.py
   ```

4. **Code false memories**:
   ```bash
   python src/utils/validation.py
   ```

5. **Run analysis**:
   ```bash
   python src/analysis/metrics.py
   ```

6. **Robustness checks**:
   ```bash
   python src/analysis/robustness.py
   ```

## Expected Output

- `data/processed/correlation_results.csv`: Pearson correlation and p-values.
- `data/processed/mixed_effects_results.csv`: Mixed-effects regression results.
- `data/processed/robustness_results.csv`: Sensitivity analysis results.
- `results/figures/`: Generated plots (e.g., correlation scatter, sensitivity curves).
- `data/processed/noise_analysis.csv`: Correlation between saliency and annotation density.

## Troubleshooting

- **Dataset not found**: Ensure the verified URL is provided and the download script is correct.
- **Memory error**: Reduce the sample size in `src/data/preprocessing.py`.
- **Model not found**: Check the `models/` directory for pretrained weights.
- **IRB/Consent missing**: The pipeline will halt if ethics files are not found in `data/ethics/`.
