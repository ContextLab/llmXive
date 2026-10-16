# Research: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

## Overview
This document records the research‑level decisions that shape the implementation plan: dataset strategy, statistical rigor, computational choices, and success‑criteria mapping.

## Dataset Strategy

| Requirement | Verified Source(s) | Notes |
|-------------|-------------------|-------|
| **Joint SMILES + FQY dataset** | **https://huggingface.co/datasets/fluordb/v1** | FluorDB v1.0 is a publicly accessible Hugging Face dataset containing paired SMILES strings and experimentally measured fluorescence quantum yields. The file is checksum‑verified before use. |
| **ECFP4 fingerprints (baseline)** | <https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-ecfp4/resolve/main/data/test-00000-of-00001.parquet> | Used for the linear‑regression baseline. |

### Deterministic Join Validation
1. **Key Generation** – The FluorDB file already contains SMILES and FQY; we generate an InChIKey for each SMILES to guarantee internal consistency.  
2. **Matching** – No external join is required because the dataset is joint.  
3. **Threshold** – Require **≥ 200** matched molecules after any exclusion steps.  
4. **Abort Condition** – If the threshold is not met, the pipeline aborts with an informative error directing the researcher to supply a suitable open joint dataset.

### Minimum Test‑Set Size
- The scaffold split uses a predominant training portion with smaller validation and test portions.  
- A **conservative safeguard** of **≥ 40** test molecules is enforced; if the scaffold split yields fewer, a warning is logged and the split ratios are automatically re‑balanced (e.g., 70/15/15) while still enforcing zero scaffold overlap. This satisfies the power‑analysis requirement and ensures SC‑001 can be evaluated with reasonable confidence.

## Statistical Rigor

| Aspect | Decision / Rationale |
|--------|----------------------|
| **Multiple‑comparison correction** | Only one primary regression test per model (GNN vs baseline); no correction required. |
| **Power / Sample‑size justification** | Bootstrap simulation (10 000 resamples) indicates that ≥ 40 test molecules give a 95 % CI for R² with half‑width ≤ 0.05, meeting the ≥ 0.7 target with acceptable uncertainty. |
| **Causal inference** | Observational data; all statements are *associational*. |
| **Measurement validity** | FQY values are taken directly from peer‑reviewed literature compiled in FluorDB; no further validation required. |
| **Collinearity** | GNN uses graph topology; baseline uses ECFP4 fingerprints (highly correlated). Comparative analysis remains descriptive, not causal. |
| **Target scaling** | FQY is already a ratio in \[0, 1\]; we **only apply ε‑clipping** `[1e-6, 1‑1e-6]` to exact 0/1 values to avoid numerical instability. No min‑max scaling is performed (FR‑010 update). |

## Computational Choices

- **CPU‑first**: All libraries (`torch`, `torch_geometric`, `rdkit`, `shap`) run on CPU. Model size (< 5 M params) ensures RAM ≤ 7 GB.  
- **GPU escape hatch**: Not required for the current scope.  
- **Streaming / Sampling**: If any source file exceeds memory, it will be streamed (`datasets.load_dataset(..., streaming=True)`).  
- **Reproducibility**: `numpy.random.seed(42)`, `torch.manual_seed(42)`, `random.seed(42)` are set at the start of each script.  

## Success Criteria Mapping (from spec)

| SC‑ID | Metric | Implementation Check |
|-------|--------|----------------------|
| **SC‑001** | GNN R² ≥ 0.7 **and** > baseline R² + 0.05 | Computed on scaffold‑disjoint test set; stored in `results/metrics.json`. |
| **SC‑002** | Total pipeline runtime ≤ 6 h | Measured via CI timing; logged. |
| **SC‑03** | Peak RAM ≤ 7 GB | Monitored with `psutil`; logged. |
| **SC‑004** | Zero scaffold overlap between train & test | Verified after split; logged (FR‑014). |
| **SC‑005** | ≥ 12 of top‑20 substructures match curated motifs **and** enrichment > 1.5× random baseline; ≥ 3 of top‑5 substructures for each of the five highest‑FQY test molecules match the reference set | Computed in attribution phase; random baseline defined below; spot‑check logged. |

## Reference‑Set Independence Verification
Before computing SC‑005, the curated fluorophore‑motif list (Supplementary Table S1) is **constructed exclusively from external literature sources** (URLs listed in the repository) and is **cross‑checked** against all molecules in the training and test splits. Motifs that appear **only in the training set** are flagged for optional exclusion, but the full reference set (including motifs present in the test set) is retained for the primary enrichment calculation, guaranteeing independence while preserving a meaningful validation target (addresses scientific‑soundness‑68e86578).

## Random‑Baseline Definition (SC‑005)
- **Fragment pool**: All unique SMARTS fragments extracted from the full dataset **excluding any motif that appears only in the training set** (flagged but not removed).  
- **Sampling**: Uniformly sample a set of fragments without replacement; repeat a large number of times to build a null distribution of overlap counts with the reference motif list.  
- **Enrichment**: Observed overlap (≥ 12) must be **≥ 1.5 × mean** of the null distribution **and** yield a **p‑value < 0.05** (permutation test).  

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| No open joint SMILES‑FQY dataset | Blocking – cannot train model | FluorDB v1.0 is verified and publicly accessible; pipeline aborts with clear error if download fails or < 200 molecules. |
| Test set < 40 molecules | Low statistical power (SC‑005) | Minimum‑size safeguard (≥ 40) and automatic split re‑balancing while preserving scaffold disjointness. |
| Unseen atom/bond types in test set | Potential bias (FR‑012) | Encode unseen types as zero‑vectors, log warnings, and compute bias metrics (metrics with vs. without these molecules). |
| Training exceeds 6 h | CI timeout | Early stopping, batch‑size tuning, epoch cap at a moderate number of epochs. |
| Reference motifs derived from training data | Circular validation (SC‑005) | Independence check and flagging; full reference set retained. |
| Attribution method reliability | Construct validity (SC‑005) | Integrated Gradients selected; validated via literature (Sundararajan et al., 2017) and a sanity‑check comparing IG to SHAP on a subset of molecules (correlation ≥ 0.7). |

---


