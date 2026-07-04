# Quickstart: The Impact of Emotional Expression in AI Avatars on User Trust

## Prerequisites
- Python 3.11+
- Git
- (Optional) `ffmpeg` (for audio/video processing, often required by librosa/openface)

## Installation

1.  **Clone and Setup**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-344-the-impact-of-emotional-expression-in-ai
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `openface` requires a pre-compiled binary. Ensure the `openface` executable is in your PATH or installed via the project's `scripts/setup-openface.sh` if provided.*
    *Note: `synthpop` is installed for synthetic landmark generation (simulation mode).*

4.  **Verify Environment**
    ```bash
    python -c "import openface; import librosa; import statsmodels; import synthpop; print('Dependencies OK')"
    ```

## Running the Pipeline

### Option A: Simulated Data (Default)
Since no verified dataset exists, run the pipeline with simulated data to test the full workflow. This uses `synthpop` to generate synthetic landmarks and prosody, bypassing the need for OpenFace on raw video.

```bash
# Generate synthetic data (N=500) - Signal Mode (correlated)
python code/extract_features.py --mode simulate --n 500 --signal

# Generate synthetic data (N=500) - Null Mode (independent)
python code/extract_features.py --mode simulate --n 500 --null

# Compute consistency metrics
python code/compute_metrics.py

# Run statistical analysis
python code/analyze.py

# Generate visualization
python code/visualize.py
```

### Option B: Real Data (If Available)
1.  Place video files in `data/raw/video/`.
2.  Place audio files in `data/raw/audio/`.
3.  Create `data/raw/metadata.csv` with columns: `interaction_id`, `video_file`, `audio_file`, `trust_score`, `avatar_type`, `duration`, `task_difficulty`.
4.  Run:
    ```bash
    python code/extract_features.py --mode real
    python code/compute_metrics.py
    python code/analyze.py
    python code/visualize.py
    ```

## Output Verification
- Check `outputs/results.json` for the correlation coefficient and p-value.
- Check `outputs/plot.png` for the scatter plot.
- Ensure no errors in the console regarding "insufficient data" (handled by skipping).

## Troubleshooting
- **OpenFace Error**: Ensure `openface` binary is in PATH.
- **Memory Error**: Reduce `--n` (simulation size) or process video in smaller batches.
- **Missing Data**: The script logs skipped interactions; check `logs/processing.log`.
- **Synthpop Error**: Ensure `synthpop` is installed and the random seed is set in `config.py`.