# Quickstart Guide: Visual Distraction Impact Study

## Overview
This pipeline analyzes the impact of visual distraction on cognitive control in remote work environments.

## Synthetic Data Fallback
If real datasets (e.g., from HuggingFace) are unavailable, the pipeline automatically falls back to generating synthetic data (`code/01_data_acquisition.py`). This synthetic data simulates the negative correlation structure described in literature and generates corresponding workspace images using Pillow.

## Associational Framing
All statistical findings are framed as associational. No causal claims are made. The alpha threshold of 0.05 is used as a community-standard convention.

## Execution
1. Install dependencies: `pip install -r code/requirements.txt`
2. Run data acquisition: `python code/01_data_acquisition.py`
3. Run visual metrics: `python code/02_visual_metrics.py`
4. Run analysis: `python code/03_analysis.py`
5. Run visualization: `python code/04_visualization.py`
