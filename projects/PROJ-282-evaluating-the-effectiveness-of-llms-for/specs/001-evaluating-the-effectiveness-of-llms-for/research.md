# Research: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

## Decision & Rationale
- **Zero‑shot LLM**: StarCoder‑Base 1.6B quantized to 4‑bit (CPU‑compatible) provides a balance between capability and the 2‑core, ≤ 7 GB RAM runner. No GPU is required; the model fits in ~1.2 GB RAM after quantization.
- **Embedding Encoder**: `microsoft/codebert-base` (12 M parameters) quantized to 4‑bit for CPU. **Crucially**, it computes similarity to an **EXTERNAL** vulnerability pattern corpus (CWE Top 25 snippets), NOT the evaluation datasets, to prevent data leakage.
- **Static Baselines**: Bandit (Python) and cppcheck (C) are open‑source, installable via pip/apt, and run fully on CPU.
- **Dataset Selection**: Only the three verified dataset URLs listed in the project specification are used. All are HuggingFace‑hosted parquet/JSONL files that can be streamed directly.
- **Compute Strategy**: All steps are CPU‑first. No method requires GPU; therefore the plan avoids the GPU escape hatch. The pipeline processes data in ≤ 50‑sample batches to stay under memory limits.

## Dataset Strategy
| Dataset | Source URL (verified) | Access Method | Expected Size (post‑stream) | Notes |
|---------|----------------------|---------------|-----------------------------|-------|
| VulDeePecker (full) | https://huggingface.co/datasets/ijakenorton/vuldeepecker_for_ml/resolve/main/vuldeepecker_full_dataset.jsonl | `datasets.load_dataset(..., streaming=True)` | ~3 GB JSONL (≈ 4 500 snippets) | Contains `code`, `cwe_id`, `vul_type`. |
| Juliet (C) | https://huggingface.co/datasets/claudios/VulDeePecker/resolve/main/data/test-00000-of-00001.parquet | `datasets.load_dataset("claudios/VulDeePecker", split="test")` | ~1 GB parquet (≈ 1 200 C snippets) | Provides `ground_truth_label` and `ground_truth_category`. |
| JavaScript (auxiliary) | https://huggingface.co/datasets/hchautran/javascript/resolve/main/data/test-00000-of-00038.parquet | `datasets.load_dataset("hchautran/javascript", split="test")` | ~0.8 GB parquet (≈ 2 000 JS snippets) | Used to broaden language coverage; ground‑truth labels are present. |

**External Corpus (for Embedding Similarity)**:
- **Source**: A curated list of code snippets representing the CWE Top 25 vulnerabilities, sourced from the public `CWE-Code-Snippets` repository (GitHub: `cwe-community/snippets`).
- **Usage**: Pre-computed embeddings are stored in `data/corpus/cwe_embeddings.npy`. This corpus is **independent** of the VulDeePecker/Juliet datasets to ensure no data leakage. The `embed.py` script explicitly loads this pre-computed vector store and the `microsoft/codebert-base` model to compute similarity scores for the evaluation dataset.

All three evaluation datasets are publicly downloadable without authentication. The pipeline streams each dataset, extracts the required fields, and stops after 5 000 total labeled snippets (FR‑001).

## Methodology Overview
1. **Parsing & Feature Extraction**  
   - `tree_sitter` parses each snippet → AST depth, node count.  
   - `radon` computes cyclomatic complexity (Python) or equivalent for C/JS via `lizard`.  
   - Regex‑based scan counts occurrences of known taint‑source APIs (e.g., `exec`, `system`, `eval`) and flags presence of sanitization functions (`escape`, `sanitize`).  
   - **Embedding Similarity (T021)**: `embed.py` loads the 4‑bit CodeBERT encoder (`microsoft/codebert-base`) and the pre-computed external CWE corpus embeddings. For each snippet, it computes the **average cosine similarity to the top 5 nearest neighbors (KNN, k=5)** in the external corpus. This replaces the flawed "single centroid" approach to better capture the vulnerability manifold while ensuring the predictor is independent of the evaluation dataset's labels.  

2. **Zero‑Shot LLM Inference**  
   - Prompt template: “Identify any security vulnerability in the following code and output the CWE category (e.g., CWE‑89 for SQL injection) or ‘none’.”  
   - Model output parsed with regex; unmapped responses → “uncertain” category.  
   - Truncation policy: keep the most recent tokens up to the model's context limit if the sequence length exceeds capacity.; log truncation event.  

3. **Static Analyzer Baseline**  
   - `bandit` (Python) and `cppcheck` (C) executed via subprocess; results normalized to `{snippet_id, predicted_label, is_correct}`.  

4. **Statistical Analyses**  
   - **Per‑category metrics**: precision, recall, F1, ROC‑AUC (scikit‑learn).  
   - **Feature‑outcome correlations**: **Point-Biserial correlation** (r_pb) for each continuous feature vs. binary `is_correct` outcome; apply Benjamini‑Hochberg FDR correction across the family of tests per category (FR‑005). Spearman rank correlation is also computed as a robustness check.  
   - **Regression Model**: **Binary Logistic Regression** (GLM with logit link) using `is_correct` as the dependent variable and all features as predictors; report pseudo-R² (McFadden) and coefficient significance (FR‑006). *Note: OLS is rejected for binary outcomes.*  
   - **McNemar’s Test**: Compare LLM vs. static analyzer binary outcomes. **Strict Intersection Rule**: The test is performed ONLY on samples where BOTH models produced a definitive binary prediction (excluding 'uncertain' or crashed samples). The contingency table is constructed from this intersection to avoid bias.  
   - **Sensitivity Analysis**: a random human-verified subset (re‑labelled by two security experts) – recompute metrics to assess label‑noise impact (FR‑011).  

5. **Reporting**  
   - All artefacts stored under `data/processed/` with SHA‑256 filenames.  
   - Figures generated with reproducible random seeds.  
   - Final JSON summary `results/summary.json` conforms to `contracts/analysis_metric.schema.yaml`.

## Data Leakage Prevention
- **Corpus Independence**: The vulnerability pattern corpus (CWE Top 25 snippets) is downloaded and embedded **before** any evaluation dataset (VulDeePecker/Juliet) is loaded. The evaluation datasets are never used to train or tune the embedding model or the reference corpus.
- **No Overlap**: The external corpus is distinct from the evaluation datasets. No snippet ID from the evaluation datasets appears in the reference corpus. The `embed.py` script explicitly verifies that the corpus file path points to a pre-computed artifact not derived from the current run's data.

## Risks & Mitigations
- **Embedding Encoder Load Time**: Pre‑compute and cache the reference pattern embeddings; load once per run.  
- **Memory Pressure**: Stream datasets, process in batches ≤ 50, delete intermediate tensors after each batch.  
- **Model Quantization Compatibility**: Use `bitsandbytes` CPU‑only mode; fallback to 8‑bit if 4‑bit fails, still within RAM budget.  
- **Static Analyzer Failures on malformed code**: Wrap calls in try/except; record `is_correct = false` and continue.
