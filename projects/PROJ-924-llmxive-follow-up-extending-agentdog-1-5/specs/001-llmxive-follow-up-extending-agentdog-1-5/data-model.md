# Data Model: Centroid‑Based Drift Detection

## Overview
Definitions of all entities, their JSON‑Schema contracts, and the transformation pipeline that turns raw logs into drift scores, human annotations, and final metrics. Added fields for confound control (log length, source) and clarified the drift‑score record.

## Entities & Schemas

| Entity | Schema File | Key Fields |
|--------|-------------|------------|
| **LogEntry** | `contracts/agent_log.schema.yaml` | `log_id`, `text`, `source`, `timestamp`, `label`, **`log_length`** |
| **TaxonomyCentroid** | `contracts/taxonomy_centroid.schema.yaml` | `category`, `description`, `embedding` (384‑dim), `n_samples` ≥ 100, `source_version` |
| **DriftScoreRecord** | `contracts/drift_output.schema.yaml` | `log_id`, `drift_score` ∈ [0, 2], `nearest_centroid`, `review_flag`, **`log_length`**, **`source`** |
| **HumanAnnotation** | `contracts/human_annotation.schema.yaml` | `log_id`, `annotator_id`, `label` ∈ {“novel attack”, “known attack”, “benign”} |
| **MetricsBundle** (JSON) | N/A (generated) | `kappa_mean`, `mannwhitney_p`, `rank_biserial`, `logistic_coef_p`, `auc_drift`, `auc_flant5`, `latency_ratio`, `chi2_p`, `resource_usage`, `holm_adjusted_pvalues` |

## Transformation Logic

1. **Load & Scrub** (`FR‑004`, `FR‑014`)  
   - Load `agentdog/safety-v1` via HF loader.  
   - Fetch ≥ 500 post‑2025 GitHub issue logs via the public API, store in `data/raw/novel_corpus.jsonl`.  
   - Apply deterministic PII scrubbing; compute SHA‑256 checksums recorded in `data/raw/checksums.json`.  

2. **Centroid Generation** (`FR‑003`, `FR‑004`)  
   - Group labeled logs by category, embed with MiniLM (batch = 64).  
   - Compute L2‑normalized mean vector → centroid; store in `data/processed/centroids.json` (validated against `taxonomy_centroid.schema.yaml`).  

3. **Drift Scoring** (`FR‑001`, `FR‑002`)  
   - Embed every log (both safety‑v1 and novel corpus).  
   - Compute cosine distance to each centroid; keep minimum as `drift_score`.  
   - Set `review_flag = drift_score >= DRIFT_THRESHOLD` (calibrated, default 0.5).  
   - Record **`log_length`** (character count) and **`source`** for confound analysis.  
   - Persist as Parquet `data/processed/drift_scores.parquet` (validated against `drift_output.schema.yaml`).  

4. **Stratification & Sampling** (`FR‑005`, `FR‑017`)  
   - Determine high‑drift (top quantile) and low‑drift (bottom quantile) bins **while controlling for log length and source** (quantiles resolved at runtime).  
   - Seeded random sample of ≥ 100 logs uniformly across the full drift distribution; write IDs to `data/processed/full_range_sample.json`.  

5. **Blinded Annotation Batches** (`FR‑006`)  
   - For each sampled log, create JSONL files containing `log_id`, `text`, `log_length`, and `source` (no scores or bin labels).  
   - Store under `data/processed/annotation_batches/`.  

6. **Gold‑Standard Construction & Validation** (`FR‑007‑009`, `FR‑015`, `FR‑017`)  
   - Ingest external `data/human_annotations.json`.  
   - Verify exactly three distinct `annotator_id`s per `log_id`.  
   - Compute majority‑vote binary “novel” label.  
   - Run: mean pairwise Cohen’s κ, Mann‑Whitney U (with rank‑biserial), logistic regression `novel ~ drift_score + log_length + source`, chi‑squared test, Holm correction.  
   - Store all results in `data/processed/metrics.json`.  

7. **Baseline Comparison** (`FR‑010‑011`, `FR‑016`)  
   - Run zero‑shot `google/flan‑t5‑small` on the same annotated set.  
   - Compute AUC‑ROC; enforce baseline AUC ≥ 0.70.  
   - Measure per‑log latency for both methods; compute ratio.  
   - Perform **DeLong’s test** for paired AUCs; append baseline metrics to `metrics.json`.  

8. **Final Report Generation** (`FR‑013`, `FR‑012`)  
   - `code/report.py` reads `metrics.json`, creates `data/processed/report.md` with tables, ROC curves, latency plots.  
   - Records peak RAM and wall‑clock time; asserts ≤ 7 GB and ≤ 6 h.  
   - If human annotations missing or κ < 0.6, the script writes `status: Incomplete` and exits non‑zero (Principle VI).  

## Constraints
- `RANDOM_SEED = 42`; `BATCH_SIZE = 64`; `MAX_RAM_GB = 7`; `DRIFT_THRESHOLD = 0.5`.  
- Raw data immutable; all transformations produce new files under `data/processed/`.  
- No PII in committed data; any PII detected triggers scrubbing and re‑checksum.  
- Human annotations are external; the pipeline never fabricates them.
