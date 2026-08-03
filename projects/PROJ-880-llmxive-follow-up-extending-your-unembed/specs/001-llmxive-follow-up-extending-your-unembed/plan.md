# Implementation Plan: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

**Branch**: `001-llmxive-crosslingual` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-follow-up-extending-your-unembed/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-your-unembed/spec.md`

## Summary

This project investigates whether the "edge spectrum" subspace (top-$k$ singular vectors of $W_U$) encodes a universal, language-agnostic "common sense" prior or reflects language-specific syntactic noise. The technical approach involves loading the unembedding matrices of three distinct models (Llama-3, Mistral, BLOOM), performing Singular Value Decomposition (SVD) to extract the top-$k$ subspace, and computing the cosine similarity between these subspaces across English and multilingual models. The plan further includes projecting external token frequency distributions (RedPajama/OSCAR) onto the embedding matrices to compute "mean embeddings," validating shifts against WALS typological features and Multilingual SentEval benchmarks, and performing a permutation test to establish statistical significance.

**Critical Methodological Update**: To address cross-model vocabulary differences, all comparisons (SVD similarity, mean embedding shift) are performed on a **Shared-Vocabulary Projection**. This involves intersecting the tokenizers of the models, re-indexing the singular vectors and frequency distributions to the shared token rows, and only then computing geometric metrics. This ensures the "shift" is a meaningful, invariant quantity rather than an artifact of basis mismatch.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `numpy`, `scipy`, `torch` (CPU-only), `datasets`, `pandas`, `requests`, `scikit-learn`  
**Storage**: Local file system (`data/raw`, `data/processed`) for model weights and frequency lists; JSON/CSV for results.  
**Testing**: `pytest` (unit tests for matrix operations, integration tests for full pipeline).  
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU-first: 2 vCPU, 7GB RAM, 14GB disk).  
**Project Type**: Computational Linguistics / Research Pipeline  
**Success Criteria**: Complete SVD and permutation pipeline on a GitHub Actions ubuntu-latest runner within 6 hours.
**Constraints**: 
- **No local GPU**; memory usage must stay within a reasonable limit during SVD.
- **Mandatory Streaming**: Models must be loaded **one at a time** (unload after processing) to respect RAM limits.
- **Real Data Only**: No synthetic placeholders. Frequency distributions must be derived from streaming real corpora (RedPajama/OSCAR) until $\ge [deferred]$ tokens are collected.
- **Alignment**: All cross-model comparisons must use the Shared-Vocabulary Projection.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the implementation/research phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, fixed random seeds in `code/`, and canonical Hugging Face sources for all datasets. |
| **II. Verified Accuracy** | **PASS** | Plan requires citations only from the `# Verified datasets` block. WALS and SentEval data sources must be validated via URL checks before use. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw downloads (RedPajama, OSCAR) and derivation logs. No in-place modification of raw files. |
| **IV. Single Source of Truth** | **PASS** | Every figure, statistic, or interpretation in the paper MUST trace back to exactly one row in this project's `data/` and one block in this project's `code/`. Derived numbers MUST NOT be hand-typed into the paper. |
| **V. Versioning Discipline** | **PASS** | **Explicit Mechanism**: Upon successful download of any artifact (model weights, frequency lists), the script MUST compute the SHA-256 checksum and update the `state/projects/PROJ-880-llmxive-follow-up-extending-your-unembed.yaml` file in the `artifact_hashes` map. This ensures stale review records are invalidated when artifacts change. |
| **VI. Cross-Lingual Subspace Isolation** | **PASS** | Plan explicitly isolates $W_U$ and $W_E$ operations per model/language. Mean embeddings computed separately per language using shared-vocab projection. |
| **VII. Typological Shift Quantification Rigor** | **PASS** | Plan separates "shift quantification" (cosine similarity) from "validation" (SentEval/WALS). Permutation test uses strict frequency lists as the sole source of truth for generating the null distribution. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-your-unembed/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-880-llmxive-follow-up-extending-your-unembed/
├── code/
│   ├── __init__.py
│   ├── main.py                 # Entry point, orchestration
│   ├── data_loader.py          # HF datasets, RedPajama, OSCAR
│   ├── model_analyzer.py       # SVD, Cosine Similarity, Mean Embedding, Shared-Vocab Projection
│   ├── stats.py                # Permutation tests, WALS correlation
│   ├── utils.py                # Logging, checksumming, error handling
│   └── requirements.txt
├── data/
│   ├── raw/                    # Downloaded model weights (symlinks), freq lists
│   ├── processed/              # SVD results, similarity matrices, reports
│   └── external/               # WALS data, SentEval benchmarks
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── results/
    └── final_report.json
```

**Structure Decision**: Single-project structure selected for tight coupling of data loading, analysis, and statistics. `data/` is strictly separated into `raw` (immutable) and `processed` (derived). `code/` contains modular scripts for SVD, stats, and data loading to facilitate unit testing and reproducibility.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **N/A** | N/A | No violations detected. The complexity is inherent to the scientific method (SVD + Permutation + Cross-lingual validation + Shared-Vocab Projection). |

## Methodology & Execution Steps

### 3.1. Edge Spectrum Extraction & Shared-Vocabulary Projection (FR-001, FR-002, FR-008)
1. **Shared-Vocabulary Intersection**:
   - Load tokenizers for all target models (Llama-3, Mistral, BLOOM).
   - Compute the intersection of token IDs: $V_{shared} = V_{Llama} \cap V_{Mistral} \cap V_{BLOOM}$.
   - Create a mapping index that re-indexes rows of $W_U$ and $W_E$ to the shared vocabulary.
2. **Load Model**: Load model $M$ (e.g., BLOOM) into CPU memory. **Unload immediately after processing** to respect RAM limits.
3. **Extract $W_U^{shared}$**: Extract unembedding matrix $W_U$, project to $W_U^{shared}$ using the shared index.
4. **Perform SVD**: Compute $W_U^{shared} = U \Sigma V^T$ using `scipy.sparse.linalg.svds` (Arnoldi iteration) to extract top-$k$ singular vectors ($U_{shared} \in \mathbb{R}^{d_{model} \times k}$).
5. **Procrustes Alignment**: If models have different embedding dimensions ($d_{model}$), apply orthogonal Procrustes alignment to $U_{shared}$ matrices to a common reference frame before computing similarity.
6. **Compute Similarity**: Calculate cosine similarity between aligned $U_{shared}^{M1}$ and $U_{shared}^{M2}$ for all model pairs.

### 3.2. Mean Embedding & Token Attribution (FR-003, FR-005, FR-008)
1. **Re-tokenization**:
   - Stream the external corpus (RedPajama for EN, OSCAR for FR/ZH).
   - **Re-tokenize** the corpus using the target model's tokenizer to generate a frequency vector $f$ of size $|V|$.
2. **Frequency Count**: Count tokens until $\ge [deferred]$ tokens are processed.
   - **Fallback Strategy**: If the stream yields a limited number of tokens, log a limitation and proceed with the maximum available. Do not synthesize data.
3. **Mean Embedding**: Compute $\hat{h} = W_E^{shared} \times f^{shared}$ (using the shared-vocab projected embedding matrix).
4. **Shift Vector**: Compute $\Delta = \hat{h}_{EN} - \hat{h}_{Target}$. This vector is now in the shared coordinate system.

### 3.3. Validation (FR-007)
1. **WALS Correlation**:
   - Retrieve WALS feature vectors for EN, FR, ZH.
   - **Dimensionality Reduction**: Apply PCA to the high-dimensional shift vector $\Delta$ to reduce it to $N$ components, where $N$ matches the number of WALS features (or a fixed low dimension).
   - Compute Pearson correlation between the reduced shift vector and the WALS feature difference vector.
2. **SentEval Performance**:
   - **Download SICK-R/STS-B test sets** explicitly.
   - **Execute SentEval code** against these test sets to generate performance metrics (STS accuracy) for each language. Do not assume pre-computed scores.

### 3.4. Statistical Significance (FR-004, US-3)
1. **Permutation Test**:
   - **Null Distribution**: Generate $N=1000$ samples by:
     a. **Within-Language Baseline**: Compare subspaces of same-language model pairs (e.g., Llama-EN vs Mistral-EN).
     b. **Label Permutation**: Shuffle the language labels of the frequency vectors $f$ before projecting to $W_E$, then recompute the shift vector and similarity.
   - **Observed Statistic**: Compute the similarity between observed cross-lingual subspaces (from 3.1).
   - **P-Value**: Calculate $P(\text{Sim}_{obs} \le \text{Sim}_{null})$.
   - **Frequency List Ground Truth**: The permutation test strictly uses the specific token frequency lists as the sole source of truth for generating the null distribution.

### 3.5. Feasibility & Alignment Checks (T060, T065)
1. **Feasibility Check (T060)**:
   - Implement `check_svd_feasibility` in `code/main.py`.
   - Log detailed warnings if memory usage exceeds limits.
   - Mark T012b as SKIPPED if necessary.
   - **Write Output**: Generate `data/processed/feasibility_report.json` with memory/time metrics.
2. **Vocabulary Alignment Check (T065)**:
   - Implement shared-vocabulary intersection check in `model_analyzer.py`.
   - Log warnings if overlap ratio is low.
   - **Write Output**: Generate `data/processed/vocab_alignment_warning.json` with overlap metrics and recommended actions.

## Decision Rationale

- **Why Shared-Vocabulary Projection?** To resolve the category error of comparing subspaces from different vocabularies. This ensures the similarity metric is defined and meaningful.
- **Why OSCAR?** OSCAR is a cleaned, language-filtered subset of Common Crawl, providing stable, representative token frequencies without the noise of raw web crawls.
- **Why Within-Language Null?** To test the specific hypothesis of typological shift, the null must represent "expected variation within the same language," not random geometric noise.
- **Why Streaming?** The RedPajama/OSCAR datasets are too large for the CI runner. Streaming ensures we use *real* data without fabricating a smaller synthetic subset.
- **Why Separate Model Loading?** Loading multiple large models simultaneously requires substantial RAM. Loading one-by-one respects the 7GB limit.
