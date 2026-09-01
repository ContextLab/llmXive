# Research: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Feature**: `001-semantic-collapse-threshold`  
**Date**: 2026-09-01  

## Objectives
1. Generate a comprehensive stress‑testing corpus for small ASR models under compound reverberation + noise distortions.  
2. Define a **continuous** “collapse intensity” based on the **inflection‑point intensity** (maximum negative derivative of the SSS curve) and use the deterministic threshold rule only for secondary binary classification.  
3. Test whether a universal critical interaction vector predicts the inflection‑point intensity across different ASR architectures, while controlling for baseline SSS/WER and transcript difficulty.

## Decision & Rationale
| Decision | Rationale |
|----------|-----------|
| **Compute**: Use CPU for all analytics; only distortion synthesis may require a GPU. | CPU‑first policy; GPU escape hatch will be invoked automatically if `torch.cuda.is_available()` fails on the CI runner. |
| **Dataset**: Use the **Voices‑in‑the‑Wild‑2M** parquet (HuggingFace) as the source of clean audio and transcripts. Use the **SSS** parquet (Liyongsea) for pre‑computed embeddings of clean text. | Both datasets have verified URLs and are directly downloadable via `datasets.load_dataset`. |
| **Synthetic Distortions**: Generated on‑the‑fly using `pyroomacoustics`; no external RT60/SNR datasets required. | SNR and RT60 are controllable parameters; we do not need an external source. |
| **Human Validation**: Conduct a crowdsourced validation on a representative subset of clips drawn from the Voices‑in‑the‑Wild‑2M dataset.; the subset is stored locally after download (no external URL needed). | FR‑011 requires this validation; we can generate the subset without extra data sources. |
| **Statistical Tests**: Apply Benjamini‑Hochberg FDR correction (α = 0.05) for all 54 interaction tests. Use permutation baseline per FR‑027. | Satisfies FR‑008, FR‑027. |
| **Model**: Hierarchical linear mixed‑effects regression (random intercept per ASR model) via `statsmodels` on CPU. | Meets FR‑025 and stays within CPU limits. |
| **SHAP**: Use the CPU‑only version of `shap` to compute global importance; no GPU needed. | Satisfies FR‑008 and principle VII. |
| **Baseline Covariates**: Include baseline SSS, baseline WER, and transcript length as additional predictors to control for clip‑level difficulty, satisfying FR‑127c2986 concern. | Improves construct validity of the regression. |

## Dataset Strategy
| Role | Dataset | Access Method | Verified URL |
|------|---------|---------------|--------------|
| Clean audio + transcripts (source for distortion) | **Voices‑in‑the‑Wild‑2M** | `datasets.load_dataset("llmxive/voices-in-the-wild-2m", split="train")` | https://huggingface.co/datasets/llmxive/voices-in-the-wild-2m |
| Pre‑computed sentence embeddings for SSS baseline | **SSS** (parquet) | `datasets.load_dataset("liyongsea/ptb-sss", split="train")` | https://huggingface.co/datasets/liyongsea/ptb-sss |
| Human annotation validation set | **Derived** (generated locally) | Random stratified sample of a sizable set of clips from Voices‑in‑the‑Wild‑2M | *no external URL* |
| DNS real‑world noisy clips for realism validation (FR‑018) | **DNS‑Challenge noise** | `datasets.load_dataset("DNS-Challenge/dns_noise", split="train")` | https://huggingface.co/datasets/DNS-Challenge/dns_noise |

> Variables such as SNR, RT60, and DNS noise are generated locally; no additional URLs are required.

## Methodology Overview
1. **Stratified Sampling & Power Analysis (FR‑001, FR‑008a)**  
   - Load Voices‑in‑the‑Wild‑2M, compute speaker‑wise counts, sample 50 000 clips ensuring ≥ 80 % power for effect size f² = 0.02 (G*Power calculation yields ≈ 38 k required; we use 50 k).  
   - Store as `data/derived/subset.parquet` with SHA‑256 checksum.

2. **Distortion Generation (FR‑002, FR‑024, FR‑018)**  
   - Create a Cartesian product of multiple SNR levels spanning a low‑to‑high range (including negative and positive decibel values) and six RT60 levels spanning short to longer reverberation times.  
   - Apply reverberation via `pyroomacoustics.RoomSimulator` and additive white Gaussian noise at target SNR.  
   - For each clip, generate multiple distorted versions.; store parameters in `stress_curves.parquet`.  
   - Validate synthetic realism against DNS‑Challenge clips using Log‑Mel Spectral Distance (LMSD ≤ 0.15); log any missing scenario warnings (FR‑017).

3. **ASR Inference**  
   - Run Whisper‑tiny, Distil‑Whisper, wav2vec2‑base, and two custom small models.  
   - Capture hypothesis transcripts; compute Word Error Rate (WER) via `jiwer`.  

4. **Semantic Similarity Score (FR‑003, FR‑011, FR‑022)**  
   - Encode clean transcript and ASR hypothesis with `sentence‑transformers` `all‑MiniLM‑L6‑v2`.  
   - Compute cosine similarity → SSS.  
   - For high‑reverb clips (RT60 > 0.5 s) where SSS AUC‑ROC < 0.85, switch to phoneme‑level edit distance via Montreal Forced Aligner (fallback per FR‑022).  

5. **Collapse Intensity Detection (FR‑021, FR‑020, FR‑012, SC‑009)**  
   - Compute first derivative of SSS curve, locate **inflection‑point intensity** (maximum negative derivative) – primary continuous target.  
   - Apply deterministic rule (SSS < 0.5 × baseline **and** WER > 2 × baseline) to generate a **binary collapse label** for secondary validation (interpolated if needed).  
   - If no crossing, use inflection intensity; else record “None”.  
   - Store continuous inflection‑point record in `collapse_point.parquet` (schema `contracts/collapse_point.schema.yaml`).  
   - Store binary label and detection parameters in `collapse_points.parquet` (schema `contracts/collapse_points.schema.yaml`).  

6. **Regression Modeling (FR‑005, FR‑025, FR‑027, SC‑001, SC‑002, SC‑003)**  
   - **Feature engineering**: raw SNR, RT60, interaction (SNR × RT60), quadratic terms, **baseline SSS**, **baseline WER**, **transcript length** (difficulty proxy), plus model‑architecture features (layers, embedding size).  
   - Stratified train/test split (80/20) by speaker ID + distortion type.  
   - Fit hierarchical mixed‑effects model (`statsmodels.MixedLM`) with random intercepts for ASR model.  
   - Evaluate R², MAE on test set; require R² ≥ 0.6.  
   - Permutation baseline: randomly shuffle predictor rows, refit, ensure ΔR² ≥ 0.20.  
   - Sensitivity analysis: vary SSS threshold factor (low/med/high) and WER multiplier (1.5, 2, 2.5); record coefficient CV ≤ 0.10.  

7. **Interaction Significance (FR‑013, FR‑008, SC‑003)**  
   - Fit additive linear model (SSS ~ SNR + RT60) and full non‑linear model (including interaction + quadratics).  
   - Compare via likelihood‑ratio test; apply Benjamini‑Hochberg FDR ≤ 0.05.  

8. **Critical Interaction Vector & Cross‑Model Generalization (SC‑005)**  
   - Extract interaction coefficients (and SHAP interaction strengths) from each model’s random‑effects component.  
   - Compute cosine similarity across models; report ≥ 0.80.  

9. **Reporting & Auditing (FR‑026)**  
   - All intermediate parquet files are logged with timestamps and SHA‑256 checksums.  
   - A final `paper/figures/` directory will be auto‑generated from the artifacts.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open‑source DNS real‑world clips (FR‑018) | Validation of synthetic realism could be incomplete | Use the public DNS‑Challenge noise library (`https://huggingface.co/datasets/DNS-Challenge/dns_noise`). |
| SSS metric fails validation (AUC < 0.85) | Pipeline aborts per FR‑016 | Fallback to phoneme‑level edit distance (FR‑022) automatically. |
| GPU resources unavailable for distortion generation | Exceeds 48 h wall‑time | Auto‑scale down to a CPU‑only subset (e.g., 10 k clips) and note reduced power in SC‑004. |
| Memory overflow when storing full stress‑curve parquet | CI job crash | Stream generation: write each clip’s 54 rows directly to parquet using `pyarrow` writer, never loading whole dataset into RAM. |

---


## Expected Outcomes
- **R² ≥ 0.6** on held‑out test set for predicting inflection‑point intensity.  
- **Coefficient of variation ≤ 0.10** for the critical interaction vector across sensitivity‑analysis settings.  
- **FDR‑corrected p < 0.05** for interaction terms, confirming non‑linear synergy.  
- **Cosine similarity ≥ 0.80** of interaction vectors across ASR models, supporting a universal critical interaction vector.  

All outcomes will be derived from reproducible, fully audited artifacts.
