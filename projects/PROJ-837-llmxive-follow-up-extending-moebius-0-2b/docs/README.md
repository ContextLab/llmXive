# llmXive: Dynamic Image Inpainting Research Pipeline

## Overview
This project implements the "Moebius-Dynamic" framework for efficient image inpainting,
featuring dynamic rank adjustment based on mask complexity.

## Modes of Operation
The pipeline supports two distinct modes:

### 1. CI Mode (Continuous Integration / Simulation)
- **Purpose**: Automated testing, reproducibility, and simulation without external human data.
- **Ground Truth**: Uses decoupled synthetic scores (randomly generated but validated for independence from mask metrics).
- **Data**: Fetches Places365 subset from HuggingFace.
- **Validation**: Skips Inter-Rater Reliability (Krippendorff's alpha) and human score checks.
- **Proxy Gate**: Expected to show low correlation (r < 0.7) between synthetic metrics and synthetic scores; this is **expected** and does not block execution.

### 2. Research Mode
- **Purpose**: Full scientific evaluation with real human annotations.
- **Ground Truth**: Requires `data/annotations/human_scores.csv` with schema `(image_id, score, rater_id)`.
- **Validation**: Calculates Krippendorff's alpha; requires alpha >= 0.5 for valid results.
- **Proxy Gate**: Requires Pearson correlation r >= 0.7 between synthetic metrics and human scores. Fails if r < 0.7.

## Project Structure
```
.
├── code/
│ ├── config.py # Global configuration and mode flags
│ ├── data/ # Data loading, masking, annotation
│ ├── models/ # Moebius-Tiny, Gating Head, Dynamic Model
│ ├── training/ # Training scripts
│ ├── eval/ # Metrics, stats, reporting
│ └── utils/ # Logging, seeding, validation
├── data/
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Masked images
│ ├── annotations/ # Human or synthetic scores
│ └── results/ # Validation logs, metrics, reports
├── docs/ # Documentation
├── paper/ # Draft manuscript
└── tests/ # Unit and integration tests
```

## Quickstart
1. **Setup**:
 ```bash
 pip install -r requirements.txt
 ```
2. **Run Validation**:
 ```bash
 # CI Mode (Default)
 python code/utils/quickstart_validator.py

 # Research Mode (Requires human_scores.csv)
 python code/utils/quickstart_validator.py --mode RESEARCH
 ```
3. **Execute Pipeline**:
 Follow the tasks in `tasks.md` to run the full pipeline (Data Prep -> Proxy Validation -> Training -> Evaluation).

## Key Artifacts
- `data/results/proxy_validation.json`: Gate status for synthetic vs ground truth correlation.
- `data/results/evaluation_report.json`: Final latency and FID metrics.
- `data/results/ablation_report.json`: Comparison of dynamic vs static models.
- `data/results/quickstart_manifest.json`: Checksums of all validated artifacts.

## License
Research use only.