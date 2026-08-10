# Quickstart Guide: Evaluating Code Summarization Techniques for Bug Localization

This guide provides the steps to set up the environment, generate necessary data (offline), and run the statistical analysis pipeline for the project "Evaluating the Efficacy of Code Summarization Techniques for Bug Localization".

## Prerequisites

- Python 3.9+
- Access to a machine with GPU (for the offline summary generation step, T014)
- Internet connection (to download Defects4J dataset and dependencies)

## 1. Environment Setup

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd PROJ-140-evaluating-the-efficacy-of-code-summariz
pip install -r requirements.txt
```

Ensure you have a `.env` file in the root directory with the following variables (if not present, copy from `.env.example`):

```
DEFECTS4J_DATA_PATH=data/raw/defects4j
SUMMARIES_PATH=data/summaries
INTERACTION_LOGS_PATH=data/interaction_logs
ANALYSIS_RESULTS_PATH=data/analysis_results
CONSENT_PATH=data/consent
SEED=42
```

## 2. Offline Summary Generation (One-time, GPU Required)

**Note**: This step generates the LLM summaries required for the study. It must be run on a machine with a GPU. The resulting CSVs are committed to the repository for CI consumption.

```bash
python code/generation/generate_summaries_offline.py
```

This will produce:
- `data/summaries/llm_summaries.csv`
- `data/summaries/rule_summaries.csv`

## 3. Data Download and Preparation

Download the Defects4J dataset and generate the ground truth CSV. This script uses streaming to handle large datasets within memory constraints and will fail loudly if the source is unreachable.

```bash
python code/download/download_defects4j.py
```

This will produce:
- `data/raw/defects4j/ground_truth.csv`

## 4. Run the Simulation (User Story 1)

Simulate participant interactions to generate the study dataset. This includes Latin-square assignment and latency calibration.

```bash
python code/main.py --simulate
```

This will produce:
- `data/interaction_logs/raw_logs.csv`
- `data/interaction_logs/anonymized_logs.csv` (after anonymization)

## 5. Statistical Analysis (User Story 2)

Run the full statistical analysis pipeline, including McNemar's tests, LME models, sensitivity analysis, and outlier detection.

```bash
python code/main.py --analyze
```

This will produce:
- `data/analysis_results/results.csv`
- `data/analysis_results/sensitivity_analysis.csv`
- `data/analysis_results/sensitivity_analysis_report.md`
- `data/analysis_results/outlier_flags.json`

## 6. Reproducibility Package Generation (User Story 3)

Generate the final reproducibility package for publication on OSF.

```bash
python code/main.py --package
```

This will produce:
- `data/reproducibility_package_v1.0.tar.gz`

## 7. Validation

Validate the project structure and `quickstart.md` itself.

```bash
python code/quickstart_validator.py
```

## Troubleshooting

- **Latency Calibration Failure**: If the startup gate fails due to timestamp precision > 100ms, ensure your system clock is synchronized and try again.
- **Missing Ground Truth**: Tasks with missing ground truth are flagged in `data/interaction_logs/missing_ground_truth.json` and excluded from accuracy calculations.
- **Outliers**: Participants with ≥2 tasks taking >30 minutes are excluded from paired analyses. Check `data/analysis_results/outlier_flags.json` for details.
- **Memory Issues**: The pipeline is optimized to run within 7GB RAM. If issues persist, ensure no other heavy processes are running.

## CI Execution

To run the CI reproducibility test locally (simulating GitHub Actions free-tier constraints):

```bash
python code/utils/ci_test_procedure.py
```

This script asserts runtime ≤6h and memory ≤7GB.
