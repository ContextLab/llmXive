# Research: llmXive Follow-up: Semantic Divergence Diagnostic for Agentic Reasoning

## 1. Methodology Overview

This study is a **Simulation & Feasibility Study**. It quantifies the **Semantic Divergence Score** as:

```
semantic_divergence_score = 1 - cosine_similarity(thinking_embedding, tool_centroid_embedding)
```

Both embeddings are produced by the same DistilBERT encoder (CPU‑only). The score is used as an independent variable to test the *sensitivity* of the metric to a latent “problem difficulty” variable. Ground‑truth tools and RL failure rates are **synthetically generated** when not supplied by the user, following deterministic, reproducible algorithms (see Dataset Strategy). The correlation analysis validates whether the metric can track this synthetic ground truth, serving as a proof‑of‑concept rather than a claim about real‑world RL agents.

## 2. Dataset Strategy

| Dataset / File | Purpose | Verification / Generation |
|----------------|---------|---------------------------|
| **MathVista (test split)** | Source of problem instances and `thinking_prefix`. | Verified URL; checksum recorded in `state/...`. |
| **tool_mapping.csv** (User‑Provided) | Maps `problem_id` → list of ground‑truth tool IDs. | SHA‑256 checksum supplied. **If missing**, synthetic mapping is generated **deterministically** from problem difficulty (see Synthetic Generation Algorithm). |
| **tool_descriptions.csv** (User‑Provided) | `tool_id`, `description` for BM25 indexing. | SHA‑256 checksum supplied. **If missing**, a **synthetic tool corpus** of 30 domain‑relevant tools is generated (see Synthetic Generation Algorithm). |
| **rl_failure_rates.csv** (User‑Provided) | `problem_id`, `failure_rate` (independent RL outcome). | SHA‑256 checksum supplied. **If missing**, synthetic failure rates are generated **independently** from the tool mapping (see Synthetic Generation Algorithm). |

### Synthetic Generation Algorithm (deterministic, seed‑controlled)

1. **Extract Difficulty** – Each MathVista record contains a `difficulty` field (0 – 1).  
2. **Tool Mapping** –  
   - `difficulty < 0.33` → assign tools `{search, calculator}`.  
   - `0.33 ≤ difficulty < 0.66` → `{search, calculator, graph_plotter}`.  
   - `difficulty ≥ 0.66` → `{search, calculator, graph_plotter, symbolic_solver}`.  
   The assignment uses a fixed random seed (42) for reproducibility.  
3. **Tool Corpus** – For each of the 30 predefined tool IDs, a templated description is created, e.g., “The **search** tool queries the web for relevant information.” The corpus is checksum‑verified.  
4. **RL Failure Rate** – Computed as  
   ```
   failure_rate = 0.5 * difficulty + 0.5 * U
   ```
   where `U ~ Uniform(0,1)` drawn with a separate fixed seed (123). This makes failure rates correlated with difficulty but **statistically independent** of the tool‑mapping procedure.  

All generated files are written to `data/external/` with accompanying SHA‑256 checksum files; the hashes are recorded in the project state YAML.

### Power Analysis (Methodology‑597864ad)

With a post‑filter sample size **N ≈ 500**, a two‑tailed Pearson test at α = 0.05 has 80 % power to detect **r ≥ 0.20** (small‑to‑medium effect). The pipeline aborts with a “Statistical Power Insufficient” warning if after filtering N < 30, satisfying SC‑004.

## 3. Statistical & Computational Rigor

1. **Cosine Similarity** – Vector similarity in ℝ⁷⁶⁸. Identical vectors → similarity ≈ 1, divergence ≈ 0; orthogonal → similarity ≈ 0, divergence ≈ 1.  
2. **Embedding Consistency** – Tool descriptions retrieved by BM25 are **embedded with the same DistilBERT model** before centroid calculation (addressing methodology‑f580469b).  
3. **Pearson Correlation** – Primary hypothesis test (Divergence vs. Synthetic RL failure rate). Only one test → no multiple‑comparison correction needed.  
4. **K‑Means Clustering** – Performed **only on the training split** (k = 2) to create risk groups “High‑Divergence” and “Low‑Divergence”. Silhouette score ≥ 0.25 is required. The clusters are **used for reporting only**; they are **not** fed into the logistic regression model (addressing methodology‑3f2a81d8 and scientific_soundness‑5c5fb5fb).  
5. **Logistic Regression** – Trains on the **continuous divergence score** (and optional difficulty) to predict the binary RL outcome (`success_failure`). No cluster label is used as a predictor, avoiding circular reasoning. Model evaluation reports accuracy, precision, recall (SC‑002).  
6. **Assumptions** – Correlation is associative within the simulation; no causal claims about real agents are made. Predictors are single‑dimensional, so multicollinearity is not a concern.

## 4. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing `thinking_prefix` | Record excluded, may reduce N | Log `THINKING_MISSING`; abort correlation if N < 30. |
| BM25 returns zero tools | `tool_centroid_embedding` set to `null`; record excluded. | Log `BM25_NO_RESULTS`. |
| External CSV not verified | Pipeline aborts early. | Enforce checksum verification; record hash in project state. |
| Insufficient sample size | Correlation test invalid. | Power check (see above). |
| Memory overflow | Use streaming loader and batch processing. | Streaming via `datasets` library; batch size 32. |
| Synthetic data validity | Results are simulation‑only. | Clearly label all outputs and the paper as “Simulation Study”. |

## 5. Deliverables

- `divergence_scores.json` – per‑record embeddings and scores (conforms to `output.schema.yaml`).  
- `analysis_results.json` – Pearson correlation (r, p‑value), silhouette score, logistic regression metrics.  
- `checksums.txt` – SHA‑256 hashes of all generated artifacts.  

All artifacts are traceable to a single source (raw MathVista split, verified CSVs, or deterministic synthetic generation) per Constitution Principle IV.
