# Data Model: llmXive follow‑up

## Overview
The project defines a small, version‑controlled data ecosystem. Every artifact is immutable; transformations produce new files with provenance metadata.

## Raw Inputs
| Artifact | Description | Location | Checksum (SHA‑256) |
|----------|-------------|----------|--------------------|
| `models/llama3/` | Llama‑3 checkpoint (unembedding & embedding matrices) | `data/raw/models/llama3/` | *computed at runtime* |
| `models/mistral/` | Mistral checkpoint | `data/raw/models/mistral/` | *computed at runtime* |
| `models/bloom/` | BLOOM checkpoint | `data/raw/models/bloom/` | *computed at runtime* |
| RedPajama (English) | Token stream for frequency counting | `datasets/togethercomputer/RedPajama-Data-1T` | N/A (streamed) |
| OSCAR (French) | Token stream for frequency counting | `datasets/oscar` (language=`fr`) | N/A (streamed) |
| OSCAR (Chinese) | Token stream for frequency counting | `datasets/oscar` (language=`zh`) | N/A (streamed) |

## Processed / Derived Artifacts
| Artifact | Generation Step | Format | Provenance |
|----------|----------------|--------|------------|
| `data/processed/token_counts.json` | `data_loader.py` (token counting, language filtering, guard) | JSON `{language: token_count, ...}` | Includes source URLs & hashes of RedPajama/OSCAR versions. |
| `data/processed/frequency_vector_{lang}.npy` | `data_loader.py` (normalize counts) | Numpy 1‑D float32 | Derived from `token_counts.json`. |
| `data/derived/edge_spectrum_{model}.npy` | `model_utils.py` (truncated SVD) | Numpy 2‑D float32 (k × d) | Stores top‑k singular vectors. |
| `data/derived/aligned_edge_spectrum_{model}.npy` | `subspace.py` (vocab alignment & Procrustes) | Numpy 2‑D float32 | Aligned version used for similarity. |
| `data/derived/edge_spectrum_similarity.json` | `subspace.py` (pairwise cosine similarity + bootstrap CI) | JSON conforming to `contracts/edge_spectrum.schema.yaml` | Uses `aligned_edge_spectrum_{model}.npy`. |
| `data/derived/token_attribution_{model}.json` | `token_attribution.py` (high‑logit token ranking) | JSON list of `{token_id, token_str, weight}` (top‑N) | Uses aligned edge spectrum and tokenizer. |
| `data/derived/mean_embedding_{model}_{lang}.npy` | `token_attribution.py` (projection `W_E × f`) | Numpy 1‑D float32 | Uses model’s $W_E$ and language frequency vector. |
| `data/derived/permutation_result.json` | `permutation_test.py` (within‑language null, adaptive convergence) | JSON conforming to `contracts/permutation_result.schema.yaml` | Several thousand iterations (adaptive). |
| `data/derived/final_report.json` | `run_pipeline.py` (aggregation) | JSON conforming to `contracts/similarity_report.schema.yaml` | Single source of truth for paper. |

## Metadata & Checksums
Every file written by the pipeline includes a companion metadata file (`*.meta.json`) containing:
- `generated_at` (ISO‑8601 timestamp)
- `source_artifacts` (list of input files with SHA‑256)
- `git_commit` (hash of repository at run time)
- `seed` (random seed used)

These metadata files enable reproducibility and auditability per Constitution Principle I.
