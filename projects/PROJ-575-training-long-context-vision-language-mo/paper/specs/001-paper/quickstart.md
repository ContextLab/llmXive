# Quickstart: Compiling & Running the Evaluation

This guide explains how to compile the paper locally and reproduce the evaluation pipeline.

## Prerequisites

- **Operating System**: Linux (Ubuntu 22.04 or equivalent).
- **Python**: 3.11+
- **RAM**: Minimum 8GB (strictly 7GB target for the evaluation script).
- **Disk**: 10GB free space for model weights and dataset cache.

## 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate

# Install core dependencies
pip install torch==2.3.0 transformers==4.42.0 bitsandbytes==0.43.0
pip install pandas scipy matplotlib seaborn pytest

# Install LaTeX dependencies (for PDF compilation)
# Ubuntu/Debian
sudo apt-get install texlive-latex-recommended texlive-fonts-recommended texlive-latex-extra
```

## 2. Running the Evaluation Pipeline

Execute the evaluation script with a minimal sample size (`n=10`) to verify the pipeline and generate the required artifacts.

```bash
python src/eval/run_cpu_eval.py --sample-size 10 --dataset yubo2333/MMLongBench-Doc
```

**Expected Output**:
- `results/sample_results.json`: Raw evaluation metrics.
- `results/evaluation_run.json`: Reproducibility surface metadata (commit hash, environment versions).
- `results/scaling_report.json`: Regression analysis results.
- `results/validation_report.md`: Generalization retention analysis.

**Note**: The script enforces 4-bit quantization. If the environment has less than 7GB RAM, the script will fail fast with an OOM error (Claim 5).

## 3. Validating Results

Run the validation script to check retention rates and generate the final report:

```bash
python src/eval/validate_results.py
python src/eval/scaling_analysis.py
```

Verify that `results/final_report.md` contains the **Primary Citation Claim** as per the spec logic.

## 4. Compiling the Paper

Once the evaluation is complete and the LaTeX source is populated with the generated results:

```bash
cd paper/source
pdflatex main.tex
pdflatex main.tex # Run twice for references
```

**Output**: `main.pdf` containing the full paper with figures and tables populated from the `results/` directory.

## 5. Troubleshooting

- **OOM Error**: If the script fails due to Out Of Memory, verify that 4-bit quantization is enabled and that no other processes are consuming RAM.
- **Data Unavailable**: If `yubo2333/MMLongBench-Doc` cannot be loaded, check your Hugging Face token and network connectivity. The paper must explicitly state "Data Unavailable" (Claim 5) if this occurs.
- **LaTeX Errors**: Ensure all required packages (`graphicx`, `amsmath`, `booktabs`) are installed. Check `main.log` for specific errors.
