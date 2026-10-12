# Quickstart: Evaluating the Impact of Code Generation on Code Review Time

## Prerequisites
- Python 3.11+  
- Git (for cloning)  
- HuggingFace `datasets` library (handles streaming downloads)  
- No GPU required locally; the pipeline runs entirely on CPU using the **CodeLlama‑7B‑4bit‑GGUF** model (≤ 30 s per snippet).  

## 1. Clone the Repository
```bash
git clone <REPO_URL>
cd projects/PROJ-302-evaluating-the-impact-of-code-generation
```

## 2. Set Up a Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Verify Dependencies
```bash
python -c "import pandas, datasets, torch, transformers, radon; print('All dependencies available')"
```

## 4. Run the Full End‑to‑End Pipeline
```bash
python code/main.py --full-run
```
The script will:
1. **Stream** the three verified PR parquet files into `data/raw/`.  
2. **Extract** intent prompts from commit messages.  
3. **Generate** two LLM cohorts (prompt‑only & context‑based) **on CPU only** (CodeLlama‑7B‑4bit‑GGUF, ≤ 30 s per snippet).  
4. **Compute** LOC, cyclomatic complexity, CI build time, and **semantic similarity to the repository‑level centroid** for every PR and synthetic snippet.  
5. **Simulate** `review_effort_duration` for synthetic LLM snippets by sampling from the empirical distribution of human review durations conditioned on the matched covariates (see Research.md for details).  
6. **Perform** a pre‑study power analysis to confirm sufficient matched‑pair count.  
7. **Execute** propensity‑score matching on the five required covariates, produce a Covariate Balance Report, and abort if any SMD ≥ 0.1.  
8. **Run** the appropriate statistical test (paired t‑test or Mann‑Whitney U) and report effect size, p‑value, and validation against `test_result.schema.yaml`.  
9. **Conduct** sensitivity analysis across the four repository‑star‑count quartiles.  
10. **Create** box‑plot and CDF visualisations.  
11. **Generate** an HTML/PDF report (`reports/analysis_report.pdf`).  
12. **Write** a runtime summary (`data/reports/runtime_report.json`) and enforce the 6 h wall‑time limit.

## 5. Individual Stage Commands (for debugging)

| Stage | Command | Expected Output |
|---|---|---|
| Data Acquisition | `python code/data_acquisition.py --stream` | `data/raw/*.parquet` files |
| Prompt Engineering | `python code/prompt_engineering.py --input data/raw/` | `data/processed/intent_prompts.json` |
| Synthetic Generation | `python code/synthetic_generation.py --cohort prompt,context --max-snippets 200` | `data/synthetic/llm_snippets.jsonl` |
| Feature Extraction | `python code/feature_extraction.py --input data/raw/ --synthetic data/synthetic/` | `data/processed/features.parquet`, `data/processed/merged_features.parquet` |
| Power Analysis | `python code/power_analysis.py --target-d=0.3 --alpha=0.05 --power=0.8` | `data/reports/power_requirements.json` |
| Matching & Analysis | `python code/matching.py && python code/analysis.py` | `data/processed/matched_pairs.parquet`, `data/reports/covariate_balance.json`, `data/reports/statistical_results.json` |
| Sensitivity Analysis | `python code/sensitivity.py` | `data/reports/sensitivity_summary.json` |
| Visualization | `python code/visualization.py` | `data/reports/boxplot.png`, `data/reports/cdf.png` |
| Report Generation | `python code/report_generator.py` | `reports/analysis_report.pdf` |
| Runtime Measurement | `python code/runtime.py` | `data/reports/runtime_report.json` |
| Documentation Update | `python code/docs_generator.py` | Updated `docs/quickstart.md` and `README.md` |

## 6. Verification Checklist
- **Covariate Balance**: `data/reports/covariate_balance.json` shows all SMD < 0.1.  
- **Synthetic Validity**: `data/reports/syntax_validity.json` reports ≥ 95 % valid snippets.  
- **Statistical Results**: `data/reports/statistical_results.json` conforms to `test_result.schema.yaml` and contains `p_value < 0.05` (or clearly notes under‑powered).  
- **Runtime**: `data/reports/runtime_report.json` total ≤ 6 h.  
- **Reproducibility**: Re‑run `python code/main.py --full-run` and confirm that SHA‑256 checksums of all data files match the entries in `state/projects/PROJ-302-evaluating-the-impact-of-code-generation.yaml`.

## 7. Troubleshooting
- **Rate‑limit errors**: Export a GitHub token: `export GITHUB_TOKEN=your_token`.  
- **Memory errors**: Reduce streaming batch size (`--batch-size 200`) or limit PR count (`--max-prs 5000`).  
- **Matching failure**: Inspect `data/reports/matching_failure_report.json` for covariates violating the SMD threshold; adjust caliper or drop the most imbalanced covariate and re‑run.  
- **Generation timeout**: The chosen CPU‑only model is benchmarked to stay ≤ 30 s; if a rare outlier exceeds this, the script will retry up to 3 times and then exclude the snippet.  

---

