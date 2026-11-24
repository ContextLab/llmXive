# Research: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence" (Re‑plan v4)

## Overview
Re‑planned (v4) after dataset‑verification failures and methodology‑panel review. The only obtainable dataset is a single verified parquet containing plain text and an overlap/CPU‑score label. Visual‑latent generation is infeasible; we replace it with deterministic structural features and add orthogonalization plus a random‑latent control to address collinearity concerns.

**Restated research question**: *Do cheap structural summary features of text, distilled into a compact model, add predictive value beyond dense text features for the dataset’s overlap/CPU‑score label?*

**Hypothesis structure**:
1. **Primary hypothesis** – Augmented representation (text ⊕ **orthogonalized** predicted structural latent) improves downstream metric over a per‑seed re‑trained text‑only baseline (paired t‑test, Bonferroni‑corrected α = 0.025).  
2. **Sanity check** – Distilled student reaches lower MSE than a frozen‑random‑head student (SC‑…, downgraded).  
3. **Ablation** – Predicted latent alone provides incremental predictive value (FR‑008 reframed).  
4. **Control** – Random‑latent model provides a baseline to ensure any gain is not due to latent redundancy (addresses methodology‑4eda2d04).

## Decision / Rationale

| Decision | Rationale | Compute |
|---|---|---|
| Use ONLY the verified parquet URL as input | It is the single verified, unattended‑downloadable source; all other cited datasets failed verification. | CPU |
| Replace visual latents with deterministic structural feature vectors | No images/layouts exist; a documented extractor is reproducible and honest. | CPU |
| Add **orthogonalization** step | Removes collinearity between text embedding and predicted latent, satisfying methodology‑4eda2d04. | CPU |
| Add **random‑latent control** model | Provides a genuine baseline to isolate the effect of the latent, further addressing collinearity. | CPU |
| **Fix seed count** to **10** (seeds = 42‑51 inclusive) | Guarantees enough replication for paired tests; power limitation noted (methodology‑94b117bc). | CPU |
| Downgrade SC‑001 to a sanity check | Target is deterministic → MSE convergence is near‑tautological; not hypothesis evidence. | CPU |
| Reframe FR‑008 as incremental predictive value | Independence cannot be demonstrated; we instead measure added performance. | CPU |
| Downstream task = predicting overlap/CPU‑score, with leakage pre‑check | Aligns with available label; prevents spurious claims if label is trivially derivable from text. | CPU |
| **Constitution amendment**: Principle VII updated to require deterministic structural latents (see plan.md). | Satisfies plan_consistency‑05b0db13. | — |

## Dataset Strategy

| Role | Dataset | Verified Source | Variables Used | Notes |
|------|---------|-----------------|----------------|-------|
| Corpus + downstream labels | MixSub‑LLaMA‑3.2 Text‑Only Overlap CPU‑Score | https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet | `text` (string), `overlap_cpu_score` (numeric) | Downloaded via `curl`/`pandas.read_parquet`; SHA‑256 recorded. No page images or layout annotations exist. |

## Modeling Approach
1. **Download & verify parquet** (`src/data/download.py`): fetch parquet, verify SHA‑256, assert row count ≥ 10 000, record column inventory + label semantics in `provenance.json`. Exits non‑zero with a clear message if download fails, checksum mismatch, or row count < minimum (FR‑007).  
2. **Preprocess** (`src/data/preprocess.py`): validate rows against `contracts/documentpair.schema.yaml`; skip+log invalid rows; write `data/processed/document_pairs.parquet`.  
3. **Structural target generation** (`src/features/structure.py`): deterministic feature vector (line counts, mean line length, heading markers, whitespace/punctuation ratios, etc.). Non‑degeneracy gate ensures per‑feature variance above a threshold; fallback to newline‑free features; abort with clear error if still degenerate.  
4. **Splits** (`src/utils/split_generator.py`): deterministic 80/10/10 train/val/test split (seed = 42).  
5. **Student** (`src/models/distilled.py`): hashed n‑gram → small MLP → structural vector; MSE loss; Adam; early‑stop on val MSE; seeds pinned; memory & wall‑clock recorded (FR‑002/FR‑03, SC‑004/SC‑005/SC‑007). Sanity check vs frozen‑random‑head student.  
6. **Baseline** (`src/models.baseline.py`): text embedding (pre‑trained `sentence‑transformers/all‑MiniLM‑L6‑v2` in CPU mode) + ridge head; re‑initialized and re‑trained per seed (FR‑009).  
7. **Random‑Latent Control** (`src/models/random_latent.py`): predicts random vectors of same dimension as structural latent; trained with same MSE pipeline to serve as a control.  
8. **Orthogonalization** (`src/eval/downstream.py` step 5a): regress predicted structural latent on the text embedding; use residual (orthogonal component) as augmentation.  
9. **Augmented representation** (FR‑004, reframed): concatenate text embedding with orthogonalized latent; identical ridge head.  
10. **Leakage pre‑check & downstream evaluation** (`src/eval/downstream.py`): (a) compute correlation between label and simple surface text‑similarity features; if correlation > 0.8, flag as trivial and do not claim gain. Otherwise train ridge/logistic head on (i) text‑only, (ii) augmented, (iii) latent‑only, (iv) random‑latent control; evaluate on test set; record metrics.  
11. **Stats** (`src/eval/stats.py`): paired t‑test across seeds (Shapiro‑Wilk normality; Wilcoxon fallback); Bonferroni α = 0.025; power‑limitation note; associational framing (FR‑006).  

## Evaluation Plan

| Metric | Comparison (arms, pairing unit = seed) | Test | Status |
|--------|-----------|------|--------|
| Val MSE vs frozen‑random‑head student | student vs frozen‑random‑head | Paired t‑test across seeds | **Sanity check only** (SC‑001 downgraded) |
| Downstream RMSE | augmented vs per‑seed re‑trained text‑only baseline | Paired t‑test, α = 0.025 (SC‑002/SC‑003) – gated by leakage check | **Primary hypothesis** |
| Latent‑only ablation | latent‑only vs text‑only baseline | Paired test | Incremental‑value criterion (FR‑008 reframed) |
| Random‑latent control | random‑latent vs text‑only baseline | Paired test | Controls for collinearity (addresses methodology‑4eda2d04) |
| Independence (descriptive) | MI, Pearson r (latent vs text embedding) | Descriptive only | No independence claim (FR‑008 not executable) |
| Label leakage | label vs surface text‑similarity correlation | Pre‑registered gate | If trivial, report finding; no augmented‑vs‑baseline gain claimed |
| Structural target degeneracy | per‑feature variance | Gate at Phase 1b | Fallback to newline‑free features; else abort |
| Val/train loss ratio | vs 2.0 | Overfitting check (SC‑007) | Sanity |
| Peak RAM / runtime | vs 7 GB / 6 h | psutil + wall‑clock (SC‑004/SC‑005) | Feasibility |
| Valid row count | vs 10 000 | Count at preprocess (SC‑006) | Data sufficiency |
| Seed count | **10** (seeds = 42‑51) | — | Power limitation noted (methodology‑94b117bc) |
| Random‑latent control gain | vs augmented | Paired test | Ensures gain not due to redundancy |

## Statistical Rigor Checklist
- **Multiple comparisons**: Bonferroni correction (α = 0.025) for primary hypothesis, latent‑only ablation, and random‑latent control.  
- **Power**: 10 seeds; explicit note that power may be limited for modest effect sizes.  
- **Causal framing**: associational only (FR‑006).  
- **Measurement validity**: structural targets are a documented deterministic extractor; downstream label semantics recorded and leakage‑checked.  
- **Collinearity**: orthogonalization step removes linear redundancy; residual correlation reported descriptively; random‑latent control further isolates effect.  
- **Circular validation avoided**: downstream test uses a label not identical to the distilled target; orthogonalization ensures independence of augmentation.  

## Reproducibility Measures
- Pinned random seeds (`src/utils/seed.py`).  
- Single canonical dataset URL; SHA‑256 checksum recorded.  
- Pure‑function transforms; no in‑place data mutation.  
- `requirements.txt` pins exact package versions.  
- All results trace to `artifacts/eval/results.json`.  

---


