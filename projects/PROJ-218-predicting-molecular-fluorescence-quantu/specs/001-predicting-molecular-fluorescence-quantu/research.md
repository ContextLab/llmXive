# Research: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

## Overview
This document records the research‑level decisions that shape the implementation plan: dataset strategy, statistical rigor, computational choices, and success‑criteria mapping.

## Dataset Strategy

| Requirement | Verified Source(s) | Notes |
|-------------|-------------------|-------|
| **Joint SMILES + FQY dataset** | **None (no verified open source)** | The spec assumes an open joint dataset; none is verified. Researchers must provide a **publicly accessible** joint file (`data/raw/joint.parquet` or `data/raw/joint.csv`) containing at least **200** molecules. The pipeline will abort with an informative error if the file is missing or contains fewer than 200 matched records (see FR‑010 handling). |
| **ECFP4 fingerprints (baseline)** | <https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-ecfp4/resolve/main/data/test-00000-of-00001.parquet> (parquet) | Used for linear‑regression baseline. |

### Deterministic Join Validation
1. **Key Generation** – For each SMILES record, generate an InChIKey with RDKit.  
2. **Matching** – Join the user‑provided joint file on the InChIKey (no external join required).  
3. **Threshold** – Require **≥ 200** matched molecules after the join.  
4. **Abort Condition** – If the threshold is not met, the pipeline aborts with an informative error directing the researcher to supply an open joint dataset. No synthetic data are fabricated.

### Minimum Test‑Set Size
- The scaffold split uses a predominant training portion with smaller validation and test portions.  
- A **conservative safeguard** of **≥ 20** test molecules is enforced; if the scaffold split yields fewer, a warning is logged (FR‑013) and the result is treated as exploratory.  
- If the split cannot satisfy the ≥ 20 test‑molecule floor, the split ratios are automatically adjusted to **80/15/5** while still enforcing zero scaffold overlap.

## Statistical Rigor

| Aspect | Decision / Rationale |
|--------|----------------------|
| **Multiple‑comparison correction** | Only one primary regression test per model (GNN vs baseline); no correction required. |
| **Power / Sample‑size justification** | Based on literature reporting typical moderate to high R² values for quantum‑yield regression (see Power‑Analysis section in `plan.md`). The ≥ 20 test‑molecule floor ensures a minimum viable sample; a warning is emitted if fewer are present. |
| **Causal inference** | Observational data; all statements are *associational*. |
| **Measurement validity** | FQY values are taken from peer‑reviewed literature (DOI URLs). No further validation needed. |
| **Collinearity** | GNN uses graph topology; baseline uses ECFP4 fingerprints (highly correlated). Comparative analysis remains descriptive, not causal. |
| **Target scaling** | FQY is already in \[0, 1\]; we **only clip** exact 0/1 values to `[ε, 1‑ε]` (`ε = 1e‑6`) to avoid numerical instability. No min‑max scaling is performed (updated FR‑010). |

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
| **SC‑003** | Peak RAM ≤ 7 GB | Monitored with `psutil`; logged. |
| **SC‑004** | Zero scaffold overlap between train & test | Verified after split; logged (FR‑014). |
| **SC‑005** | ≥ 12 of top‑20 substructures match curated motifs **and** enrichment > 1.5× random baseline; ≥ 3 of top‑5 high‑FQY molecules contain ≥ 3 matching motifs | Computed in attribution phase; random baseline defined below; spot‑check logged. |

## Reference‑Set Independence Verification
Before computing SC‑005, the curated fluorophore‑motif list (Supplementary Table S1) is **constructed exclusively from external literature sources** (URLs listed in the repository) and is **cross‑checked** against all molecules in the training and test splits. Any motif that appears in the splits is removed from the reference set for the enrichment calculation, guaranteeing independence (addresses scientific‑soundness‑68e86578).

## Random‑Baseline Definition (SC‑005)
- **Fragment pool**: All unique SMARTS fragments extracted from the full dataset **excluding any fragment present in the curated motif list**.  
- **Sampling**: Uniformly sample a set of fragments without replacement; repeat 100 times to build a null distribution of overlap counts with the reference motif list.  
- **Enrichment**: Observed overlap (≥ 12) must be ≥ 1.5 × mean of the null distribution.  

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| No open joint SMILES‑FQY dataset | Blocking – cannot train model | Require user‑supplied open joint file; abort with clear error if missing or < 200 molecules. |
| Test set < 20 molecules | Low statistical power (SC‑005) | Minimum test‑set warning (≥ 20); fallback to 80/15/5 split while preserving scaffold disjointness. |
| Unseen atom/bond types in test set | Potential crashes (FR‑012) | Log warnings, skip during inference, retain summary report. |
| Training exceeds 6 h | CI timeout | Early stopping, batch‑size tuning, epoch cap at 50. |
| Reference motifs derived from training data | Circular validation (SC‑005) | Independence check before attribution validation; remove overlapping motifs. |

---



