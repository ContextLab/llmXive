# Implementation Plan: llmXive follow-up: extending "Edit-Compass & EditReward-Compass: A Unified Benchmark for Image Editing"

**Branch**: `001-llmxive-followup-correlation-study` | **Date**: 2026-07-11 | **Spec**: [link to spec]  
**Input**: Feature specification from `/specs/001-llmxive-followup-correlation-study/spec.md`

## Summary
The project must download the Edit‑Compass dataset, filter it to the *World Knowledge Reasoning* and *Visual Reasoning* categories, compute an **Instruction-Description Semantic Similarity Score** using a quantized CPU‑optimized Vision‑Language Model (VLM) and a **Fidelity Score** using SSIM + LPIPS, run a multicollinearity check and a multiple linear regression with Benjamini‑Hochberg correction, and report whether the semantic similarity score predicts human preference more strongly than the fidelity score. All steps are designed to run on a free‑tier GitHub Actions runner (2 CPU, ≤7 GB RAM, ≤6 h).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers==4.41.0`, `sentence‑transformers==2.7.0`, `torch==2.2.2+cpu`, `opencv-python`, `scikit-image`, `lpips==0.1.4`, `pandas`, `statsmodels`, `numpy`, `scipy`, `tqdm`, `llama-cpp-python==0.2.80` (for 4-bit GGUF VLM)  
- **Storage**: Files under `data/` (raw download, filtered subset, scores JSON) and `outputs/` (regression report, figures).  
- **Testing**: `pytest`, `pytest‑cov` for unit tests of each module; contract validation via `jsonschema` against schemas in `contracts/`.  
- **Target Platform**: Linux (GitHub Actions runner).  
- **Project Type**: CLI‑style data‑processing pipeline packaged under `src/`.  
- **Performance Goals**: End‑to‑end runtime ≤ 6 h, peak RAM ≤ 7 GB.  
- **Constraints**: CPU‑only inference; no GPU or CUDA; batch size chosen to respect RAM limit (batch=8 for 4-bit VLM).  
- **Scale/Scope**: Up to 2 388 instances (full Edit‑Compass) but processing may be truncated for CI timing; the plan includes optional sub‑sampling for quick CI checks.  
- **Model Versions**:  
  - VLM: `Phi-minik-instruct-GGUF` (4-bit quantized, loaded via `llama-cpp-python`).  
  - Embedding: `sentence-transformers/all-MiniLM-L-v`.

## Constitution Check
| Principle | Check |
|-----------|-------|
| I. Reproducibility | All scripts are deterministic (random seeds fixed), data fetched from canonical HuggingFace URLs, and `requirements.txt` pins exact versions. |
| II. Verified Accuracy | External citations (models: Phi-mini, all-MiniLM-L6-v2; dataset: Edit-Compass) are listed and will be verified by the Reference‑Validator Agent before the study proceeds. |
| III. Data Hygiene | Raw download is stored unchanged; every transformation writes a new file with a checksum recorded in `state/projects/PROJ-814-...yaml`. |
| IV. Single Source of Truth | Each figure and statistic is generated directly from the JSON score file and regression output; no manual transcription. |
| V. Versioning Discipline | All artifacts (data files, model checkpoints, scripts) are hashed; changes update `state/projects/...yaml`. |
| VI. Semantic‑Logic Over Pixel‑Fidelity Priority | The analysis pipeline is **explicitly designed to test** the hypothesis that semantic logic consistency is the primary driver of human preference. The plan does not assume the result; it structures the regression and reporting to determine if the Logic Score coefficient is significantly larger than the Fidelity Score coefficient. |
| VII. Computational Resource‑Constrained Execution | Batch sizes (8) and model selection (Phi-3-mini 4-bit GGUF, MiniLM) guarantee ≤ 7 GB RAM; runtime estimate ≤ 5 h on free runner. |

## Project Structure
```text
specs/001-llmxive-followup-correlation-study/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── score-record.schema.yaml

src/
├── data/
│   ├── raw/                # raw Edit‑Compass download (unchanged)
│   ├── filtered/           # subset after category filter
│   └── scores/             # JSON files with Semantic Similarity & Fidelity scores
├── models/
│   └── vlm.py              # wrapper for Phi-3-mini (4-bit GGUF) inference
├── services/
│   ├── download.py         # dataset download & checksum
│   ├── filter.py           # category filtering
│   ├── scoring.py          # semantic similarity & fidelity computation
│   └── analysis.py         # multicollinearity check + regression
├── cli/
│   └── main.py             # entry point orchestrating the pipeline
└── utils/
    └── logging.py

tests/
├── unit/
│   ├── test_download.py
│   ├── test_filter.py
│   ├── test_scoring.py
│   └── test_analysis.py
└── contract/
    └── test_score_schema.py
```

**Structure Decision**: A single‑project layout (`src/`, `tests/`) suffices because the feature is a data‑processing pipeline without a separate service or UI component.

## Complexity Tracking
All functional requirements are mapped to explicit pipeline stages.; no principle violations are identified. Any future extension (e.g., GPU acceleration) would require a new principle amendment.

---