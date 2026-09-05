# Data Model: llmXive follow‑up

## Overview
All pipeline outputs are JSON documents adhering to explicit JSON‑Schema contracts stored in `contracts/`. The schemas enforce field types, required keys, and basic value constraints (e.g., `top_k` ≥ 1, `similarity` ∈ [‑1, 1]).

## Core Schemas & Artifact Mapping

| Schema | File | Purpose | Produced Artifact(s) |
|--------|------|---------|----------------------|
| **Edge Spectrum** | `contracts/edge_spectrum.schema.yaml` | Stores model name, language, top‑k singular vectors, checksum, generation timestamp. | `edge_spectrum_<model>_<lang>_<hash>.json` |
| **Frequency List** | `contracts/frequency_list.schema.yaml` | Token‑frequency vector for a given language (probability distribution). | `frequency_list_<lang>_<hash>.json` |
| **Mapped Vocabulary** | `contracts/mapped_vocab.schema.yaml` | Mapping from each model’s token IDs to the shared large subword vocabulary (Q136293754). | `mapped_vocab_<model>_<hash>.json` |
| **Token Attribution** | `contracts/token_attribution.schema.yaml` | List of top‑tokens with highest logit weights in the edge spectrum (also stores optional vocab mapping). | `token_attribution_<model>_<hash>.json` |
| **Mean Embedding / Baseline Shift** | `contracts/token_shift.schema.yaml` | Records mean‑embedding norm, shift vector, and baseline comparison. | `mean_embedding_<lang>_<hash>.json`, `baseline_shift_<lang>_<hash>.json` |
| **Anisotropy Bias** | `contracts/bootstrap_test.schema.yaml` | Bootstrap confidence interval for anisotropy bias of the edge spectrum. | `anisotropy_bias_<lang>_<hash>.json` |
| **Similarity Matrix** | `contracts/similarity_matrix.schema.yaml` | Pairwise cosine similarity scores (with bootstrap CI) for all model‑language pairs. | `similarity_matrix_<hash>.json` |
| **Similarity Metric** | `contracts/similarity_metric.schema.yaml` | Δ‑similarity values after architecture control adjustment. | `similarity_metric_<hash>.json` |
| **Bootstrap Test (Similarity)** | `contracts/bootstrap_test.schema.yaml` | Details of bootstrap resampling for similarity scores (replicate count, CI). | `bootstrap_test_<hash>.json` |
| **Permutation Test** | `contracts/permutation_test.schema.yaml` | Null distribution components, raw p‑values, Bonferroni‑adjusted combined p‑value. | `permutation_test_<hash>.json` |
| **Validation** | `contracts/validation.schema.yaml` | Pearson correlation results with WALS and SentEval (r, p, CI). | `validation_<hash>.json` |
| **Ablation Report** | `contracts/validation.schema.yaml` | Same schema as validation; used for the randomized‑frequency ablation. | `ablation_report_<hash>.json` |
| **Feasibility Report** | `contracts/feasibility_report.schema.yaml` | Runtime, peak memory, CPU usage, abort warnings. | `dataset_verification.json` (re‑used for reporting verification) |

## Data Lineage
1. **Raw data** (`data/raw/`) – downloaded from verified URLs, checksummed.  
2. **Derived artifacts** (`data/derived/`) – each step reads from previous artifacts, writes a new file whose name encodes the operation **and** includes a 10‑character SHA‑256 content‑hash suffix (e.g., `edge_spectrum_llama3_en_abcdef1234.json`).  
3. **Provenance metadata** – every JSON includes `generated_at` (ISO‑8601 UTC) and `source_checksum` fields linking back to the raw input(s).  

## Naming Conventions
- Files use snake_case, include model, language, and operation identifiers **plus** a 10‑character hash suffix.  
- Example: `edge_spectrum_llama3_en_abcdef1234.json`, `frequency_list_fr_1234abcd56.json`.  

All paths start with `data/derived/` to satisfy **FR‑018** and the version‑discipline principle.

---


