# Research: Semantic Decay Retrieval for LightMem‑Ego

## Overview
We evaluate whether a **learnable semantic decay** scoring function improves recall of *rare, semantically significant long‑term* events compared with the existing **Fixed Hierarchy** retrieval. The study runs entirely on a CPU‑only GitHub Actions runner (multiple vCPU, 7 GB RAM) and respects all functional and success criteria from the specification.

## Dataset Strategy

| Role | Source | HF URL | Loader | Variables Required |
|------|--------|--------|--------|--------------------|
| **Raw egocentric memory** | Ego4D metadata (timestamps, event IDs) | https://huggingface.co/datasets/HuggingFaceM4/ego4d/resolve/main/dataset_infos.json | `datasets.load_dataset("HuggingFaceM4/ego4d", "metadata")` | `timestamp`, `event_label` |
| **Visual/audio embeddings** | EgoD video‑MAE L features (fps 8) | https://huggingface.co/datasets/Jazzcharles/ego4d_videomae_L14_feature_fps8/resolve/main/chunk_0.tar.gz | custom extractor (`tarfile` → `np.load`) | `embedding` (768‑dim float vector) |

*No external FAISS index is used. Instead, a FAISS HNSW index is built deterministically from the Ego4D embeddings during preprocessing, ensuring modality and domain consistency (addresses data_resources-684ec12c concern).*

All downloads are performed programmatically in `src/data/download.py`, checksummed, and cached under `data/raw/`.

## Methodology

1. **Pre‑processing & Semantic Coherence Validation** (Phase 0)
   * Load Ego4D JSON metadata and video‑MAE embeddings.  
   * Join on video ID → create a parquet `memory_nodes.parquet` with columns: `node_id`, `timestamp` (ISO), `event_label`, `embedding` (binary).  
   * Compute event frequencies; an event is "rare" if its `event_label` occurs ≤ 5 times (FR‑012).  
   * **NEW (Phase 0.4)**: Perform semantic coherence validation to operationalize "semantically significant." Cluster embeddings by event label using k-means (k = number of unique labels, seeded). Compute within-cluster cohesion (silhouette score or mean cosine similarity). Mark an event as `is_semantically_distinct = True` if its within-cluster cohesion exceeds the corpus median, ensuring rare events are not merely low-frequency but also semantically coherent. This bridges the construct validity gap between occurrence count and semantic significance.

2. **FAISS Index Construction** (Phase 1.1a)
   * Build a FAISS HNSW index directly from the Ego4D embeddings using deterministic parameters (seed = 42, M=16, ef_construction=200, ef_search=50).  
   * Store the index under `data/processed/faiss_hnsw_ego4d.index`.  
   * This ensures the baseline and Semantic Decay models query the same embedding space, eliminating domain mismatch.

3. **Baseline Retrieval (Fixed Hierarchy)** (Phase 1)
   * Route each query to the appropriate temporal bucket using hard thresholds (e.g., `<4d`, `4‑14d`, `>14d`).  
   * Perform FAISS HNSW search within the bucket.  
   * Record Top‑1 hit, latency, CPU cycles.  
   * If the FAISS index fails to load, raise `RuntimeError("FAISS index load failure: <details>")` (FR‑011).

4. **Semantic Decay Retrieval** (Phase 2)
   * Compute similarity `sim(q,m)` via cosine similarity (scikit‑learn).  
   * Score each candidate with `S = α·sim + β·exp(-λ·t)`.  
   * All hyper‑parameters (α, β, λ) are learned jointly via grid search; no fixed defaults (addresses methodology-5bba8e08 concern).

5. **Joint Hyper‑parameter Grid Search** (Phase 3)
   * Build validation set of multiple queries (random seed [fixed value]).  
   * Iterate over (α, β, λ) grid:  
     - α ∈ {, 0.6, 0.7}  
     - β ∈ {multiple values spanning a range}  
     - λ ∈ {small positive values, intermediate values, …, large positive values}  
   * For each of the combinations, compute Top‑1 accuracy on the validation set.  
   * Enforce λ bounds (0 < λ < 10) and α, β bounds (0 < α, β < 1); any out‑of‑bounds value triggers a `ValueError` (FR‑010, FR‑014).  
   * Select the first triple (α*, β*, λ*) achieving maximal validation Top‑1 accuracy (deterministic tie‑breaking: ascending order of α, then β, then λ).  
   * Store optimal parameters and validation accuracy for reporting.

6. **Full Evaluation** (Phase 4)
   * Load a representative set of evaluation queries (spanning multiple days to a month).  
   * Identify "rare, semantically significant" events: `event_label` frequency ≤ 5 AND `is_semantically_distinct = True` (from Phase 0.4).  
   * **Power Check** (FR‑009, revised): If rare‑event count < 50, abort long‑term analysis and emit flag "Insufficient rare‑event data (n < 50): analysis skipped." This threshold is justified by the rule-of-thumb that McNemar's test requires ≥50 discordant pairs for 80% power at α=0.05 (Fleiss, 1981; Siegel & Castellan, 1988).  
   * Run both retrievers on all queries in the evaluation set, record per‑query:  
     - `hit` (bool)  
     - `latency_ms` (`time.perf_counter()` diff)  
     - `cpu_cycles` (`psutil.Process().cpu_times().user * 1e9` as proxy)  
   * Aggregate metrics per subset (short‑term 1‑3d, long‑term >14d).  
   * **Statistical Test**: Build a 2×2 contingency table of correct/incorrect predictions for the long‑term subset and run **McNemar's test** (`scipy.stats.mcnemar`) (FR‑005).  
   * **Significance**: report p‑value; success if `p < 0.05` (SC‑002).  
   * **Latency Check**: assert `max(latency_ms) ≤ 200` (FR‑006, SC‑003).  
   * **CPU‑Cycle Check**: compute `ratio = avg_cycles_semantic / avg_cycles_baseline`; assert `ratio ≤ 1.10` (FR‑013, SC‑009).  
   * **Short‑Term Regression**: compute accuracy drop; flag if > 5 % (FR‑007, SC‑004).  

7. **Reporting** (Phase 5)
   * Serialize all aggregated numbers, optimal parameters, and flags into `evaluation_report.json`.  
   * Validate against `contracts/evaluation_report.schema.yaml`.  
   * Generate a markdown summary (`report.md`) for quick inspection.

### Decision / Rationale
*All computation is CPU‑only.* The scoring function is a simple linear combination; FAISS HNSW runs on CPU (`faiss-cpu`). No GPU is required, satisfying Principle VI and the spec's "CPU‑constrained" requirement. The FAISS index is built from Ego4D embeddings on the same CPU runner, eliminating external index dependencies and ensuring modality consistency.

### Statistical Rigor
* **Multiple‑comparison correction**: Not needed because only **one** primary hypothesis (long‑term accuracy improvement) is tested via McNemar's test.  
* **Power limitation**: Explicitly handled with a revised threshold of ≥50 rare events (FR‑009). If the dataset contains fewer rare events, the analysis is aborted and flagged (SC‑006).  
* **Causal inference**: The analysis is **associational**; we do **not** claim causality beyond the algorithmic improvement (Principle VII).  
* **Measurement validity**: Ego embeddings are pre‑computed by video‑MAE, a validated vision model (Tong et al., 2022). We assume embedding stability and do not retrain.  
* **Collinearity**: Irrelevant because α, β, λ are jointly optimized; no fixed defaults confound attribution.  
* **Construct validity**: The rare-event definition is refined to include semantic coherence (Phase 0.4), ensuring "semantically significant" is operationalized beyond mere frequency.

## Expected Deliverables
* `data/processed/memory_nodes.parquet` – cleaned, checksum‑verified dataset with `is_semantically_distinct` flag.  
* `data/processed/faiss_hnsw_ego4d.index` – deterministically built FAISS index.  
* `src/cli/run.py` – end‑to‑end script that produces `evaluation_report.json`.  
* `evaluation_report.json` conforming to `contracts/evaluation_report.schema.yaml`, including `optimal_alpha`, `optimal_beta`, `optimal_lambda`.  
* Markdown summary and optional plots (accuracy vs. λ, latency distribution).  

---