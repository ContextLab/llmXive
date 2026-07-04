# Quickstart: Assessing the Impact of Code Style Consistency on LLM Code Understanding

## Prerequisites
- Python 3.10+
- Access to a GitHub Actions runner (or local machine with 7GB+ RAM)
- HuggingFace CLI access (if model requires auth, though StarCoder 1B is public)

## Installation
1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/requirements.txt
   ```

## Data Setup
The pipeline automatically downloads datasets from the verified HuggingFace sources defined in `research.md`.
1. **Validate URLs**: Run the Reference-Validator to ensure all dataset URLs are reachable and match the spec.
   ```bash
   python projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/00_validate_urls.py
   ```
2. **Download Data**: Run the data preparation script (downloads and checksums).
   ```bash
   python projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/00_download_data.py
   ```
   *Note: Ensure ~14GB disk space is available.*

## Running the Pipeline
Execute the pipeline in sequential order. Each step generates artifacts for the next.

1. **Versioning & Hashing**:
   ```bash
   python projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/00_hash_artifacts.py
   ```
   *Output: Updates state file with artifact hashes.*

2. **Style Scoring & Stratification**:
   ```bash
   python projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/01_style_scoring.py
   python projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/02_stratification.py
   ```
   *Output: `data/processed/stratified_samples.parquet`*

3. **Pre-Check Gate**:
   *Automatically runs within `05_statistical_analysis.py` to verify effect size > 0.5. If failed, pipeline halts.*

4. **Inference (CPU)**:
   ```bash
   timeout 6h python projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/03_inference.py
   ```
   *Output: `data/processed/inference_results.jsonl`*

5. **Evaluation**:
   ```bash
   python projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/04_evaluation.py
   ```
   *Output: `data/processed/performance_metrics.parquet`*

6. **Statistical Analysis**:
   ```bash
   python projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/05_statistical_analysis.py
   ```
   *Output: `data/processed/statistical_report.json`*

7. **Robustness Check (Optional)**:
   ```bash
   python projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/06_robustness_check.py
   ```
   *Output: `data/processed/robustness_report.json`*

## Verification
- Check `data/processed/` for expected parquet/jsonl files.
- Verify `statistical_report.json` contains non-null p-values, effect sizes, and `r_squared`.
- Ensure no "OOM" or "timeout" logs exceed 5% of the total samples.
- Check `state/*.yaml` for updated artifact hashes.