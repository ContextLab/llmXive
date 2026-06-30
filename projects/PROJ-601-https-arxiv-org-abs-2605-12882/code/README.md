# CiteVQA CPU Adaptation

## Purpose
This adaptation reproduces the **Strict Attributed Accuracy (SAA)** metric from the CiteVQA paper using a **CPU-tractable, synthetic dataset**.

## Simplifications vs. Original
1.  **No MLLMs**: The original paper evaluates 20+ Multimodal LLMs (Gemini, etc.) on 1,897 real PDFs. This adaptation uses a **rule-based "dummy model"** that generates answers and bounding boxes based on simple heuristics. This allows us to calculate the *metric logic* without requiring expensive GPU inference or API keys.
2.  **Synthetic Data**: Instead of downloading 711 PDFs (gigabytes of data), we generate a small CSV of 100 synthetic "questions" with known ground-truth answers and bounding boxes.
3.  **Metric Focus**: The core contribution of the paper is the **SAA metric** (Answer Correctness AND Citation Correctness). This script focuses entirely on implementing and verifying this metric calculation.
4.  **Scale**: Reduced from 1,897 items to 100 items; reduced from 7 domains to 1 synthetic domain.

## Output Artifacts
- `data/results.csv`: Per-item evaluation results (Answer, Citation, SAA boolean).
- `data/summary.csv`: Aggregated metrics (Recall, Rel, QA_ACC, SAA) matching the paper's Table 1 format.
- `figures/saa_distribution.png`: A histogram showing the distribution of SAA scores.

## Running

### Prerequisites
Before running the pipeline, ensure the external CiteVQA submodule is initialized:
```bash
git submodule update --init --recursive
```

### Execution
Run the main script from the project root:
```bash
python code/citevqa_cpu_adaptation.py
```
