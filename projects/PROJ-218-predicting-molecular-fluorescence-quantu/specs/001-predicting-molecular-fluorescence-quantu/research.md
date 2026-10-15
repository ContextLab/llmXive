# Research: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

## Overview
This document outlines the research‑level decisions, dataset strategy, statistical considerations, and computational choices that will guide the implementation plan.

## Dataset Strategy

| Requirement | Verified Source(s) | Notes |
|-------------|-------------------|-------|
| **SMILES strings** | <https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet> (parquet) | Contains only SMILES; no FQY. |
| **Fluorescence Quantum Yields (FQY)** | <https://doi.org/10.48700/datst.mff4d-q4a24> (JSON) | Contains experimental FQY values; no SMILES. |
| **Optional RDKit descriptors** | <https://huggingface.co/datasets/nglebm19/rdkit_chemical/resolve/main/data/train-00000-of-00001.parquet> | May be useful for sanity checks but not required. |
| **ECFP4 fingerprints** | <https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-ecfp4/resolve/main/data/test-00000-of-00001.parquet> | Used for the linear‑regression baseline. |

**Important Data Gap**: No verified dataset provides *both* SMILES and FQY.  

### Deterministic Join Validation
1. **Key Generation** – For each SMILES record, generate an InChIKey using RDKit.  
2. **Matching** – Join the SMILES parquet and the FQY JSON on the InChIKey.  
3. **Threshold** – Require **≥ 200** matched molecules ([deferred] of the assumed minimum).
4. **Abort Condition** – If the threshold is not met, the pipeline stops with an informative error directing the researcher to supply an open joint dataset (e.g., a curated FluorDB release). No synthetic data are generated.

### Power‑Analysis & Minimum Test‑Set Size
- **Effect size assumption**: Anticipated R² ≥ 0.7 (Cohen’s f² ≈ 2.33).  
- **Parameters**: α = 0.05, power = 0.80.  
- **Result**: Minimum total N is set to be sufficiently large; applying an 80/10/10 scaffold split then yields a proportionate number of test molecules.  
- **Conservative safeguard**: Enforce a **minimum test‑set size of 70 molecules**. If the scaffold split produces fewer, a warning is logged (FR‑013) and SC‑001 is treated as exploratory.

## Statistical Rigor

| Aspect | Decision / Rationale |
|--------|----------------------|
| **Multiple‑comparison correction** | Only a single primary regression test per model (GNN vs baseline); no correction needed. |
| **Power / Sample‑size justification** | Presented above; a warning is emitted if the effective test set falls below 70 molecules. |
| **Causal inference** | Observational data; all statements are *associational*. |
| **Measurement validity** | FQY values are taken from peer‑reviewed literature (DOI URLs). No additional validation required. |
| **Collinearity** | GNN uses graph topology; baseline uses ECFP4 fingerprints (highly correlated). Comparative analysis remains descriptive, not causal. |

## Computational Choices

- **CPU‑first**: All libraries (`torch`, `torch_geometric`, `rdkit`, `shap`) run on CPU. Model size (< 5 M params) ensures RAM ≤ 7 GB.  
- **GPU escape hatch**: Not required for the current scope.  
- **Streaming / Sampling**: If any source file exceeds memory, it will be streamed (`datasets.load_dataset(..., streaming=True)`).  
- **Reproducibility**: `numpy.random.seed(42)`, `torch.manual_seed(42)`, `random.seed(42)` are set at the start of each script.

## Success Criteria Mapping (from spec)

| SC‑ID | Metric | Implementation Check |
|-------|--------|----------------------|
| **SC‑001** | GNN R² ≥ 0.7 and > baseline R² + 0.05 | Computed on scaffold‑disjoint test set; stored in `results/metrics.json`. |
| **SC‑002** | Total pipeline runtime ≤ 6 h | Measured via CI timing; logged. |
| **SC‑003** | Peak RAM ≤ 7 GB | Monitored with `psutil`; logged. |
| **SC‑004** | Zero scaffold overlap between train & test | Verified after split; logged (FR‑014). |
| **SC‑005** | ≥ 12 of top‑20 substructures match curated motifs **and** enrichment > 1.5× random baseline | Computed in attribution phase; random baseline defined below; spot‑check of top‑5 high‑FQY molecules also logged. |

## Reference‑Set Independence Verification
Before computing SC‑005, the curated fluorophore‑motif list (Supplementary Table S1) is cross‑checked against all molecules in the training and test splits. Any overlap triggers a warning and is excluded from the reference set for the enrichment calculation, ensuring that the validation is not circular (addresses scientific soundness‑78b9e565).

## Random‑Baseline Definition (SC‑005)
- **Fragment pool**: All unique SMARTS fragments extracted from the full dataset (excluding the top‑20 attributed substructures).  
- **Sampling**: Uniformly sample a predetermined number of fragments without replacement; repeat 100 times to build a null distribution of overlap counts with the reference motif list.  
- **Enrichment**: Compute the observed overlap (≥ 12) and compare to the mean of the null distribution; require observed ≥ 1.5 × mean.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| No joint SMILES‑FQY dataset | Blocking – cannot train model | Deterministic InChIKey join with threshold; abort with clear error; request open joint dataset. |
| Test set < 20 molecules | Low statistical power (SC‑005) | Minimum test‑set size warning (≥ 70); interpret results as exploratory if not met. |
| Unseen atom/bond types in test set | Potential crashes (FR‑012) | Log warnings, skip during inference, retain for evaluation with summary report. |
| Training exceeds 6 h | CI timeout | Early stopping, batch‑size tuning, epoch cap at 50. |
| Reference motifs derived from training data | Circular validation (SC‑005) | Independence check before attribution validation. |

---

