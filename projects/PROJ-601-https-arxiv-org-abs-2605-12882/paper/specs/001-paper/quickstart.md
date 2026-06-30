# Quickstart: Compiling the CiteVQA Paper

This guide details how to compile the paper locally and regenerate the figures from the research artifacts.

## Prerequisites

- **LaTeX Distribution**: TeX Live 2023 or later (or MacTeX on macOS).
- **Python Environment**: Python 3.11 with `matplotlib`, `seaborn`, `pyyaml`.
- **Data Artifacts**: You must have run the research pipeline to generate `outputs/evaluation_report.json` and `outputs/validation_log.json`.

## Step 1: Environment Setup

```bash
# Create a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies for figure generation
pip install matplotlib seaborn pyyaml pandas
```

## Step 2: Generate Figures

The paper figures are generated dynamically from the `outputs/` directory.

```bash
# Navigate to the paper root
cd projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper

# Run the figure generation script
python scripts/generate_figures.py
```

*Note: This script reads `outputs/evaluation_report.json` and `outputs/validation_log.json` and saves the resulting PDF/SVG files to `source/figures/`.*

## Step 3: Compile the LaTeX Source

```bash
# Compile the main document
pdflatex -interaction=nonstopmode source/main.tex

# Run BibTeX for references
bibtex main

# Compile twice more to resolve references
pdflatex -interaction=nonstopmode source/main.tex
pdflatex -interaction=nonstopmode source/main.tex
```

## Step 4: Verify Output

- Check `source/main.pdf` for the final paper.
- Ensure all figures (SAA Workflow, Error Distribution, Integrity Chart) are present.
- Verify that the "Reproducibility Appendix" contains the correct random seed and environment versions.

## Troubleshooting

- **Missing Figures**: Ensure `outputs/evaluation_report.json` exists and is not empty. The figure generation script will fail if the data model contract is violated.
- **BibTeX Errors**: Ensure `references.bib` is in the `source/bib/` directory and matches the citations in the `.tex` file.
- **Package Missing**: If `pdflatex` complains about missing packages, install the full TeX Live distribution or the specific missing package (e.g., `sudo apt-get install texlive-latex-extra`).