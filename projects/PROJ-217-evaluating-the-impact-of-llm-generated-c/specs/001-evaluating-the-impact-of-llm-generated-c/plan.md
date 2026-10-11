# Implementation Plan: Evaluating the Impact of LLM-Generated Code Comments on Code Readability

**Branch**: `001-evaluating-llm-comments-readability` | **Date**: 2026-10-10 | **Spec**: [spec.md](../specs/001-evaluating-llm-comments-readability/spec.md)

## Summary
The project builds a three‑condition experimental dataset (LLM‑generated comment, human‑written docstring, no comment) from the CodeSearchNet Python corpus, computes lexical (BLEU, ROUGE‑L) and semantic (Sentence‑BERT similarity) readability metrics **only for the LLM‑generated comments**, gathers human performance data via a **randomised between‑subject user study**, and conducts statistical analyses (ANOVA, power analysis, correlation) to answer whether LLM‑generated comments **causally improve** developer task performance.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets==2.19.0`, `torch==2.2.0`, `transformers==4.41.0`, `sentence-transformers==2.7.0`, `scikit-learn==1.5.0`, `statsmodels==0.14.2`, `pandas==2.2.2`, `tqdm==4.66.2`, `requests==2.32.3`  
- **Storage**: File‑based (raw parquet → JSONL → CSV) under `data/`  
- **Testing**: `pytest==8.2.2` (unit tests for each pipeline stage)  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only)  
- **Constraints**: ≤ 7 GB RAM, ≤ 6 h job wall‑time, no GPU required (LLM inference via remote HuggingFace Inference API)  

## Constitution Check
| Principle | Compliance Action |
|-----------|-------------------|
| I. Reproducibility | All scripts are deterministic (seeded RNG), external datasets fetched via fixed URLs, `requirements.txt` pins versions. |
| II. Verified Accuracy | All citations (CodeSearchNet, CodeLlama, BLEU/ROUGE datasets) are limited to the verified URLs listed in the spec. |
| III. Data Hygiene | Checksums recorded in `data/artifact_hashes.yaml`; every transformation writes a new file; no in‑place edits. |
| IV. Single Source of Truth | Every figure/table references a row in `data/` and a line in `code/`. |
| V. Versioning Discipline | Content hashes stored in `state/projects/...yaml`; any change updates the timestamp. |
| VI. Automated Metric‑Human Correlation Validation | Correlation analysis is performed **only on LLM‑generated comments** (human and none conditions are excluded). Auxiliary metrics (comment length, Flesch‑Kincaid readability) are also examined. |
| VII. Controlled Experimental Condition Isolation | Each snippet appears exactly once per condition; participants are randomised **once** to a single condition for the whole study, eliminating order and skill confounds. |

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
│   ├── metrics.py                # BLEU, ROUGE‑L, Sentence‑BERT (fallback to MiniLM) + comment length & readability
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
| **1 Data Acquisition & Validation** | Download three verified parquet files, verify SHA‑256 checksums (recorded in `data/artifact_hashes.yaml`). Extract `code`, `docstring`, generate a UUID `snippet_id` for each record, and **store `snippet_id`** in `raw_snippets.jsonl`. Filter out malformed records, write `raw_snippets.jsonl` and `excluded_records.json`. | FR‑001 | SC‑005 |
| **2 Comment Generation** | For each retained snippet, call CodeLlama‑7B via the HF Inference API (max‑tokens ≈ 256). Apply exponential‑backoff (3 attempts, 60 s base). Truncate code longer than 1024 tokens, log warning. Produce `llm_comments.jsonl` containing **`snippet_id`**, `code`, `human_comment`, `llm_comment`, and `no_comment` (empty). | FR‑002 | SC‑001, SC‑002 |
| **3 Metric Computation** | Compute BLEU and ROUGE‑L (using `nltk.translate` and `rouge_score`) **for the LLM‑generated comment only**, using the human docstring as reference. Compute Sentence‑BERT cosine similarity **between the LLM comment and the human docstring** (fallback to `all-MiniLM-L6-v2`). For human and none conditions, set metric fields to `null`. Additionally compute comment length (character count) and Flesch‑Kincaid readability as auxiliary metrics for the LLM comment. Normalize all scores to 0‑1. Output `readability_metrics.csv`. | FR‑003 | SC‑003 |
| **4 Human Study Data Integration** | Load `human_study_responses.csv` (the CSV defined in the Data Model) and merge with `llm_comments.jsonl` and `readability_metrics.csv` on `snippet_id` to create `analysis_dataset.csv`. | FR‑004, FR‑006 | SC‑001, SC‑002 |
| **5 Statistical Analysis** | • **Power analysis**: use `FTestAnovaPower` with target effect size f = 0.25, α = 0.05 → required N≈60 per group; we target **60 participants per condition**. Output `power_report.txt`. <br>• **One‑way ANOVA** on `completion_time_sec` and `accuracy` (accuracy arcsine‑sqrt transformed) across the three *randomised* conditions → `anova_results.json`. <br>• **Correlation**: Pearson r between each *LLM‑only* readability metric (BLEU, ROUGE‑L, Semantic_Similarity, comment length) and each human outcome; apply Bonferroni correction (α/4). Output `correlations.csv`. | FR‑005, FR‑007 | SC‑004, SC‑005 |
| **6 Reporting** | Assemble tables & figures (`fig_time.pdf`, `fig_corr.png`). Write `results_summary.md` that references exact rows in `analysis_dataset.csv` and the contract schemas. | — | — |
| **7 Contract Validation** | Run `pytest` contract suite to ensure output files conform to `contracts/*.schema.yaml`. | — | — |

## Edge‑Case Handling (explicitly required)
| Situation | Mechanism |
|-----------|-----------|
| HuggingFace API rate‑limit / transient failure | Retry wrapper with 3 attempts, exponential back‑off (60 s). |
| Code snippet exceeds CodeLlama‑7B context window | Tokenize with `tiktoken`, truncate to 1024 tokens, log snippet ID to `truncation_warnings.log`. |
| Sentence‑BERT model OOM | Attempt to load `all-MiniLM-L6-v2`; if that fails, fall back to `paraphrase-MiniLM-L3-v2`. |
| Insufficient power after recruitment | Power analysis reports achieved power; if < 0.80, `results_summary.md` notes the limitation and no causal claim is made. |
| Correlation tautology | Correlation analysis is restricted to **LLM‑generated comments only**; human and none conditions are excluded. An auxiliary metric (comment length) provides a non‑deterministic predictor. |

## Timeline (estimated CI minutes)
| Step | Approx. runtime (CPU) |
|------|-----------------------|
| Download & checksum | 2 min |
| Validation & exclusion | 3 min |
| Comment generation (≈ several hundred snippets) | 12 min (API latency dominates) |
| Metric computation | 4 min |
| Merge human data | 1 min |
| Power + ANOVA + correlation | 3 min |
| Reporting & contract check | 2 min |
| **Total** | **[deferred]** (well within budget) |

---


