# Research: Semantic Decay Retrieval for LightMem‑Ego

## Overview
We evaluate whether a **learnable semantic decay** scoring function improves recall of *rare, semantically significant long‑term* events compared with the existing **Fixed Hierarchy** retrieval. The study runs entirely on a CPU‑only GitHub Actions runner (2 vCPU, 7 GB RAM) and respects every functional and success criterion from the specification.

## Dataset Strategy

| Role | Source | HF URL | Loader | Required Variables |
|------|--------|--------|--------|--------------------|
| **Ego4D metadata (timestamps, event IDs)** | Ego4D dataset info | https://huggingface.co/datasets/HuggingFaceM4/ego4d/resolve/main/dataset_infos.json | `datasets.load_dataset("HuggingFaceM4/ego4d", "metadata")` | `timestamp`, `event_label` |
| **Video‑MAE L14 embeddings (768‑dim float)** | Ego4D video‑MAE features (fps 8) | https://huggingface.co/datasets/Jazzcharles/ego4d_videomae_L14_feature_fps8/resolve/main/chunk_0.tar.gz | custom extractor (`tarfile` → `np.load`) | `embedding` |
| **Optional auxiliary index data** | FAISS‑compatible index (not used directly) | https://huggingface.co/datasets/AlgorithmicResearchGroup/arxiv_abstracts_specter_faiss_flat_index/resolve/main/arxiv-abstracts.jsonl | – | – |

All downloads are performed programmatically in `src/data/download.py`, checksummed, and cached under `data/raw/`. No other external datasets are accessed.

## Methodology

1. **Pre‑processing & Rare‑Event Identification** (Phase 0)  
   * Load metadata and embeddings, join on video ID, and write `memory_nodes.parquet` with columns `node_id`, `timestamp`, `event_label`, `embedding`.  
   * Compute per‑event frequencies; flag `is_rare = True` when the frequency ≤ 5 (FR‑012).  

2. **FAISS HNSW Index Construction** (Phase 1)  
   * Build a deterministic HNSW index (`faiss.IndexHNSWFlat`) from all embeddings (seed = 42). Store under `data/processed/faiss_hnsw.index`.  
   * If index loading fails, raise `RuntimeError("FAISS index load failure: <details>")` (FR‑011).  

3. **Baseline Retrieval (Fixed Hierarchy)** (Phase 1)  
   * Route queries to one of three temporal buckets based on hard thresholds (e.g., `<4 d`, `4‑14 d`, `>14 d`).  
   * Perform a k‑NN search (k = 1) within the appropriate bucket.  

4. **Semantic Decay Retrieval** (Phase 2)  
   * Compute cosine similarity `sim(q,m)` via `sklearn.metrics.pairwise.cosine_similarity`.  
   * Score each candidate with `S = α·sim + β·exp(-λ·t)`, where α = 1.0, β = 1.0 (constants) and λ is the learnable decay rate.  
   * Enforce λ bounds `0 < λ < 10`; any violation raises `ValueError` (FR‑010, FR‑014).  

5. **Deterministic λ Grid Search** (Phase 3)  
   * Use a fixed‑seed validation set of a modest number of queries.  
   * Iterate λ over `{0.1, 0.2, …, 9.9}`. For each λ, compute Top‑1 accuracy on the validation set.  
   * Select the **first** λ (ascending order) that achieves the maximal validation accuracy (deterministic tie‑breaking, FR‑015).  

6. **Full Evaluation** (Phase 4)  
   * Load an evaluation query set spanning 1‑30 days.  
   * **Power check**: If the number of rare events (`is_rare == True`) is < 30, abort the long‑term analysis and emit flag “Insufficient rare‑event data (n < 30): analysis skipped” (FR‑009).  
   * Run both retrievers on all queries, recording per‑query: correctness (Top‑1 hit), latency (ms), and CPU cycles (user time via `psutil`).  
   * Aggregate metrics for:  
     - Long‑term (> 14 days) accuracy.  
     - Short‑term (1‑3 days) accuracy.  
   * Perform **McNemar’s test** on the long‑term contingency table (`scipy.stats.mcnemar`) (FR‑005). Report statistic, p‑value, and a boolean `significant` (SC‑002).  
   * Verify **latency** ≤ 200 ms for all queries (FR‑006, SC‑003).  
   * Verify **CPU‑cycle ratio** ≤ 1.10 (FR‑013, SC‑009).  
   * Verify **short‑term degradation** ≤ 5 % (FR‑007, SC‑004); flag any breach.  

7. **Reporting** (Phase 5)  
   * Serialize all aggregated numbers, optimal λ, validation accuracy, and any flags into `evaluation_report.json`.  
   * Validate the JSON against `contracts/evaluation_report.schema.yaml`.  
   * Produce a concise markdown summary (`report.md`) for quick human inspection.

### Decision / Rationale
*All computation is CPU‑only.* The scoring function is a lightweight linear combination; FAISS HNSW runs with `faiss-cpu`. No GPU is required, satisfying Principle VI and the spec's “CPU‑constrained” requirement.

### Statistical Rigor
* **Multiple‑comparison correction**: Not required; only one primary hypothesis (long‑term accuracy improvement) is tested.  
* **Power limitation**: Explicitly handled via the `<30` rare‑event abort rule (FR‑009). This aligns with standard guidance that McNemar’s test needs ≥ 30 discordant pairs for 80 % power at α = 0.05.  
* **Causal inference**: The analysis is purely associational; we do not claim causal effects beyond algorithmic improvement (Principle VII).  
* **Measurement validity**: Ego4D video‑MAE embeddings are a validated visual representation (Tong et al., 2022).  
* **Collinearity**: Not applicable; α and β are fixed constants, λ is the sole learnable scalar.

## Expected Deliverables
* `data/processed/memory_nodes.parquet` – cleaned dataset with `is_rare` flag.  
* `data/processed/faiss_hnsw.index` – deterministic FAISS HNSW index.  
* `src/cli/run.py` – CLI that produces `evaluation_report.json`.  
* `evaluation_report.json` conforming to the contract schema, including `optimal_lambda`.  
* `report.md` – markdown summary and optional plots (accuracy vs. λ, latency distribution).  

---
