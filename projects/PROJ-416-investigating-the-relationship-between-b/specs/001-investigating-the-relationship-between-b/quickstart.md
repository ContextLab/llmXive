# Quickstart: Investigate Brain Network Dynamics and VR Therapy Response

## 1. Prerequisites

-   Python 3.10+
-   `pip`
-   (Optional) `git` for cloning the repo.

## 2. Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Configuration

Before running, ensure a valid dataset is available.
**Note**: The current `# Verified datasets` block does not contain a verified source for paired fMRI and clinical scores.
1.  If you have a local dataset, place it in `data/raw/`.
2.  If using OpenNeuro, update `config.yaml` (or environment variables) with the dataset ID.
3.  **Critical**: The pipeline will halt if `pre_treatment_score` and `post_treatment_score` are missing from the metadata.

## 4. Running the Pipeline

The pipeline executes in four stages:

```bash
# Stage 1: Download & Validate (Halt if missing variables)
python code/main.py --stage download

# Stage 2: Preprocess (Motion correction, normalization)
python code/main.py --stage preprocess

# Stage 3: Compute Metrics (Network graphs)
python code/main.py --stage compute

# Stage 4: Analyze (ANCOVA State, Exploratory Response, Sensitivity, Plots)
python code/main.py --stage analyze
```

## 5. Output

-   `data/metrics/network_metrics.csv`: Computed metrics per subject.
-   `data/results/analysis_results.json`: Regression coefficients and p-values (Primary: State, Secondary: Response, Tertiary: Delta-Delta).
-   `figures/`: Diagnostic plots (scatter, residuals, sensitivity).
-   `paper/draft.md`: Auto-generated text with associational framing.

## 6. Troubleshooting

-   **"Fatal Error: Missing required variable"**: The dataset lacks pre/post clinical scores. Verify the dataset metadata.
-   **"Out of Memory"**: Reduce the number of subjects (N) in the configuration. The pipeline is designed for N=10.
-   **"High Collinearity"**: The system runs Univariate models but flags VIF > 5. Ridge regression is NOT used. **Spec update required to remove Ridge mandate.**
