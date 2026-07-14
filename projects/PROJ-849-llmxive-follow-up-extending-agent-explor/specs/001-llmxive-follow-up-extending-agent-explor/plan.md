# Implementation Plan: llmXive Follow-up: Semantic Divergence Diagnostic for Agentic Reasoning

**Branch**: `001-llmxive-semantic-gap-diagnostic` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-agent-explor/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-agent-explor/spec.md`

## Summary

This project is a **Simulation & Feasibility Study** that computes a **Semantic Divergence Score** for each multimodal reasoning problem, correlates it with (synthetically or user‑provided) RL failure rates, and builds a predictive risk classifier. All steps are designed to run on a CPU‑only GitHub Actions free‑tier runner within the memory and time limits of the Constitution.

## Technical Context

- **Language**: Python 3.11  
- **Core Libraries** (pinned in `requirements.txt`):  
  - `datasets==2.20.0`  
  - `transformers==4.44.0` (CPU‑only, `torch==2.3.0+cpu`)  
  - `scikit-learn==1.5.0`  
  - `rank-bm25==0.2.2`  
  - `pandas==2.2.2`  
  - `numpy==2.1.0`  
  - `pyyaml==6.0.2`  
- **Storage**: Local `data/` directory, HuggingFace cache.  
- **Testing**: `pytest` suite validates vector math, schema compliance, and end‑to‑end pipeline flow.  
- **Target Platform**: Linux on GitHub Actions Free Tier (2 CPU, ≈7 GB RAM, ≈14 GB disk, ≤5 h timeout).  

### Automatic Sampling Mechanism (FR‑008)

1. **Pre‑flight size check** – before loading, the file size (or streaming metadata) of the MathVista subset is inspected.  
2. **Streaming fallback** – if estimated size > 6 GB, the loader switches to `datasets.load_dataset(..., streaming=True)` and processes records in batches of **32**.  
3. **Batch‑size safety** – each batch is embedded and discarded before the next batch, guaranteeing peak RAM ≤ 7 GB.  
4. **Graceful abort** – if streaming is unavailable and the file exceeds the limit, the job aborts with a clear error message.

### BM25 Retrieval & Embedding (Principle VI)

* The tool documentation corpus is **synthetically generated** (see Research.md) from a fixed list of 30 domain‑relevant tool IDs with templated descriptions.  
* A BM25 index is built over these descriptions.  
* For each problem we query the top 10 tools.  
* **Crucially**, each retrieved tool description is **embedded with the same DistilBERT encoder** (`distilbert-base-uncased`) used for the thinking prefix. The centroid is the arithmetic mean of those 10 embeddings (dimension = 768). This guarantees vector‑space compatibility for cosine similarity.

## Phases & Mapping to Functional Requirements (FR)

| Phase | Tasks | FR(s) addressed |
|-------|-------|-----------------|
| **0. Environment Setup** | Create virtualenv, install pinned deps, set `PYTHONHASHSEED=0` and `numpy.random.seed(42)`. | – |
| **1. Data Ingestion** | • Download MathVista test split (≤ 500 records) via streaming if needed.<br>• Load `tool_mapping.csv` (checksum‑verified). If missing, **synthetically generate** a deterministic mapping from problem difficulty (low → basic tools, medium → mixed, high → advanced).<br>• Load `rl_failure_rates.csv` (checksum‑verified). If missing, **synthetically generate** failure rates as `failure_rate = 0.5 * difficulty + 0.5 * Uniform(0,1)` using a fixed seed.<br>• Load `tool_descriptions.csv` (checksum‑verified) or generate the synthetic tool corpus. | FR‑001, FR‑008 |
| **2. Tool Corpus Construction** | Build BM25 index from the (synthetic or provided) tool descriptions. | FR‑002 |
| **3. Embedding Service** | Encode `thinking_prefix` and each retrieved tool description with DistilBERT (CPU). Compute centroid of the top‑10 tool embeddings. | FR‑003 |
| **4. Divergence Computation** | Compute cosine similarity and `semantic_divergence_score = 1 - cosine_similarity`. | FR‑004 |
| **5. Correlation Analysis** | Verify sample size ≥ 30; perform Pearson correlation (single test, no multiple‑comparison correction). Power analysis (see Research.md) ensures detectability of r ≥ 0.20. Abort with “Statistical Power Insufficient” if N < 30. | FR‑005, SC‑001 |
| **6. Predictive Modeling** | • Apply **K‑Means (k=2)** **only on the training split** to obtain risk groups “High‑Divergence” and “Low‑Divergence” (silhouette ≥ 0.25).<br>• Train a **logistic regression** classifier **using only** `semantic_divergence_score` (and optional `difficulty`) to predict binary RL outcome. Evaluate on held‑out test set; report accuracy, precision, recall. | FR‑006, FR‑007, SC‑002, SC‑003 |
| **7. Output Generation** | Write per‑record JSON (`divergence_scores.json`) conforming to `output.schema.yaml`; write analysis summary JSON (`analysis_results.json`). | FR‑004, FR‑005, FR‑007 |
| **8. Versioning & Checksums** | Compute SHA‑256 for every new artifact and **record them in** `state/projects/PROJ-849-llmxive-follow-up-extending-agent-explor.yaml` (Principle V). | FR‑008, Principle V |
| **9. Reference‑Validator CI Step** | After documentation generation, run `scripts/verify_references.py` which invokes the Reference‑Validator Agent on all citation URLs; CI fails if any citation does not meet the title‑token overlap threshold. | Principle II |
| **10. Schema Generation** | Run `scripts/generate_schemas.py` to regenerate `src/models/schemas.py` from all `contracts/*.schema.yaml` before any code import, guaranteeing SSoT. | Principle IV |

## Detailed Methodology

### Synthetic Data Generation (independence guarantee)

* **Problem Difficulty** – extracted from MathVista metadata (`difficulty` field, normalized to [0,1]).  
* **Tool Mapping** – deterministic rule:  
  - `difficulty < 0.33` → assign tools `{search, calculator}`.  
  - `0.33 ≤ difficulty < 0.66` → `{search, calculator, graph_plotter}`.  
  - `difficulty ≥ 0.66` → `{search, calculator, graph_plotter, symbolic_solver}`.  
  Random seed = 42 ensures reproducibility.  
* **RL Failure Rate** – computed as `0.5 * difficulty + 0.5 * U` where `U ~ Uniform(0,1)` with seed = 123. This makes failure rates **statistically related** to difficulty but **independent** of the tool‑mapping process.  

Both generated files are written with accompanying SHA‑256 checksums recorded in the project state.

### Power Analysis (Methodology‑597864ad)

Using `statsmodels.stats.power.NormalIndPower`, with α = 0.05, power = 0.80, the required sample size to detect r = 0.20 is **≈ 194**. Our cap of 500 records comfortably exceeds this; the pipeline aborts if after filtering N < 30.

### Edge‑Case Handling

- **BM25 zero results** → `tool_centroid_embedding` set to `null`; record flagged `BM25_NO_RESULTS` and excluded from downstream analysis.  
- **Missing `thinking_prefix`** → record skipped, logged with error code `THINKING_MISSING`.  
- **Timeout** – `scripts/timeout_handler.py` enforces a 5‑hour wall‑clock limit; on breach, raises `TimeoutError`.  

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | `requirements.txt` pins exact versions; all random seeds are fixed; CI runs the full pipeline from a fresh runner. |
| II. Verified Accuracy | CI includes `scripts/verify_references.py` invoking the Reference‑Validator Agent on every citation URL. |
| III. Data Hygiene | Raw datasets are read‑only; every transformation writes a new file with a SHA‑256 checksum recorded in `state/...`. |
| IV. Single Source of Truth | Contracts define schemas; `scripts/generate_schemas.py` syncs them to `src/models/schemas.py`. |
| V. Versioning Discipline | After each stage, `scripts/update_state_hashes.py` records SHA‑256 hashes of all artifacts in `state/projects/PROJ-849-llmxive-follow-up-extending-agent-explor.yaml`. |
| VI. Semantic Divergence Quantification | Divergence = `1 – cosine_similarity` between DistilBERT embeddings of thinking prefix and tool‑centroid (same encoder). |
| VII. Diagnostic Validation Rigor | Logistic regression is trained on divergence (and optional difficulty) only; the ground‑truth RL failure rates are independent synthetic labels. |

## Timeline (≤ 5 h CI)

| Step | Estimated Runtime |
|------|-------------------|
| Data download & checksum | < 5 min |
| BM25 index building | < 1 min |
| Embedding (500 × batch‑32) | ≈ 30 s |
| Divergence computation | < 1 min |
| Correlation & power check | < 1 min |
| K‑Means + logistic regression | < 2 min |
| Output writing, hashing, CI checks | < 2 min |
| **Total** | **< 15 min** |

All steps comfortably satisfy the free‑tier constraints.
