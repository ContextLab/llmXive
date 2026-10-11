# Implementation Plan: Evaluating the Impact of LLM-Generated Code Comments on Code Readability

**Branch**: `001-evaluating-llm-comments-readability` | **Date**: 2026-10-10 | **Spec**: [spec.md](../specs/001-evaluating-llm-comments-readability/spec.md)  
**Input**: Feature specification from `/specs/001-evaluating-llm-comments-readability/spec.md`

## Summary
The project builds a three‑condition experimental dataset (LLM‑generated comment, human‑written docstring, no comment) from the CodeSearchNet Python corpus, computes lexical (BLEU, ROUGE‑L) and semantic (Sentence‑BERT) similarity metrics, gathers human performance data via a controlled user study, and conducts statistical analyses (ANOVA, power analysis, correlation) to answer whether LLM‑generated comments improve code readability.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets==2.19.0`, `torch==2.2.0`, `transformers==4.41.0`, `sentence-transformers==2.7.0`, `scikit-learn==1.5.0`, `statsmodels==0.14.2`, `pandas==2.2.2`, `tqdm==4.66.2`, `requests==2.32.3`  
- **Storage**: File‑based (raw parquet → JSONL → CSV) under `data/`  
- **Testing**: `pytest==8.2.2` (unit tests for each pipeline stage)  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only)  
- **Project Type**: Research library / CLI utilities  
- **Performance Goals**: Entire pipeline ≤ 30 min on free‑tier CI for the default sample (≈ 500 snippets)  
- **Constraints**: ≤ 7 GB RAM, ≤ 6 h job wall‑time, no GPU required (LLM inference via remote HuggingFace Inference API)  

## Constitution Check
| Principle | Compliance Action |
|-----------|-------------------|
| I. Reproducibility | All scripts are deterministic (seeded RNG), external datasets fetched via fixed URLs, `requirements.txt` pins versions. |
| II. Verified Accuracy | All citations (CodeSearchNet, CodeLlama, BLEU/ROUGE datasets) are limited to the verified URLs listed in the spec. |
| III. Data Hygiene | Checksums recorded in `data/artifact_hashes.yaml`; every transformation writes a new file; no in‑place edits. |
| IV. Single Source of Truth | Every figure/table references a row in `data/` and a line in `code/`. |
| V. Versioning Discipline | Content hashes stored in `state/projects/...yaml`; any change updates the timestamp. |
| VI. Automated Metric‑Human Correlation Validation | Correlation analysis (Pearson) is mandatory before any claim about metric validity. |
| VII. Controlled Experimental Condition Isolation | Each snippet appears exactly once per condition; all other variables are held constant. |

## Project Structure
```text
specs/001-evaluating-llm-comments-readability/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── analysis.schema.yaml

src/
├── data/
│   ├── download.py               # download & checksum CodeSearchNet
│   ├── prepare.py                # validation, exclusion, three‑condition assembly
│   ├── generate_comments.py      # HuggingFace API wrapper with retry/backoff
│   ├── metrics.py                # BLEU, ROUGE‑L, Sentence‑BERT (fallback to MiniLM)
│   └── analysis.py               # ANOVA, power analysis, correlation, reporting
├── utils/
│   └── logging.py
└── cli/
    └── run_pipeline.py           # orchestrates all stages

tests/
├── unit/
│   ├── test_download.py
│   ├── test_prepare.py
│   ├── test_generate_comments.py
│   ├── test_metrics.py
│   └── test_analysis.py
└── contract/
    └── test_contracts.py
```

## Phase Overview & FR/SC Mapping
| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|-----------------|------------------|
| **0 Setup** | Install dependencies, set `HUGGINGFACE_API_KEY`. | — | — |
| **1 Data Acquisition & Validation** | Download three verified parquet files, verify checksum, extract `code` & `docstring` fields, filter out malformed records, write `raw_snippets.jsonl` and `excluded_records.json`. | FR‑001 | SC‑005 |
| **2 Comment Generation** | For each retained snippet, call CodeLlama‑7B via HuggingFace Inference API (max‑tokens ≈ 256). Apply exponential‑backoff (3 attempts, 60 s pause). Truncate code longer than 1024 tokens, log warning. Produce `llm_comments.jsonl` with fields `code`, `human_comment`, `llm_comment`, `no_comment` (empty). | FR‑002 | SC‑001, SC‑002 |
| **3 Metric Computation** | Compute BLEU, ROUGE‑L (using `nltk.translate`), and Sentence‑BERT cosine similarity (model `sentence-transformers/all-MiniLM-L6-v2` as fallback). Normalize scores to 0‑1. Output `readability_metrics.csv`. | FR‑003 | SC‑003 |
| **4 Human Study Data Integration** | Load CSV files produced by the external user‑study platform (pre‑agreed schema). Merge with snippet IDs to create `analysis_dataset.csv`. | FR‑004, FR‑006 | SC‑001, SC‑002 |
| **5 Statistical Analysis** | • Power analysis (using `statsmodels.stats.power.FTestAnovaPower`) → `power_report.txt`. <br>• One‑way ANOVA on `completion_time` and `accuracy` across conditions → `anova_results.json`. <br>• Pearson correlation between each readability metric and each human outcome → `correlations.csv`. Apply Bonferroni correction for the three metric‑outcome pairs. | FR‑005, FR‑007 | SC‑004, SC‑005 |
| **6 Reporting** | Assemble tables & figures (`fig_time.pdf`, `fig_corr.png`). Write a concise `results_summary.md` that references the exact rows in `analysis_dataset.csv` and the contract schemas. | — | — |
| **7 Contract Validation** | Run `pytest` contract suite to ensure output files conform to `contracts/*.schema.yaml`. | — | — |

## Edge‑Case Handling (explicitly required)
| Situation | Mechanism |
|-----------|-----------|
| HuggingFace API rate‑limit / transient failure | Retry wrapper with 3 attempts, exponential back‑off (60 s). |
| Code snippet exceeds CodeLlama‑7B context window | Tokenize with `tiktoken`, truncate to 1024 tokens, log snippet ID to `truncation_warnings.log`. |
| Sentence‑BERT model OOM | Attempt to load `all-MiniLM-L6-v2`; if that fails, fall back to `paraphrase-MiniLM-L3-v2` (even smaller). |
| Insufficient power after recruitment | Power analysis reports achieved power; if < 0.80, the `results_summary.md` notes the limitation and no claim of significance is made. |

## Timeline (estimated CI minutes)
| Step | Approx. runtime (CPU) |
|------|-----------------------|
| Download & checksum | 2 min |
| Validation & exclusion | 3 min |
| Comment generation (≈ 500 snippets) | 12 min (API latency dominates) |
| Metric computation | 4 min |
| Merge human data | 1 min |
| Power + ANOVA + correlation | 2 min |
| Reporting & contract check | 2 min |
| **Total** | **≈ 26 min** (well under 30 min budget) |

---
