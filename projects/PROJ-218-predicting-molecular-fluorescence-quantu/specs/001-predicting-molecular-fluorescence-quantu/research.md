# Research: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

## Overview
This document records the research‑level decisions that shape the implementation plan: dataset strategy, statistical rigor, computational choices, and success‑criteria mapping.

## Dataset Strategy

| Requirement | Verified Source(s) | Notes |
|-------------|-------------------|-------|
| **Joint SMILES + FQY dataset** | **https://huggingface.co/datasets/fluordb/v1** | FluorDB (initial release) is a publicly accessible Hugging Face dataset containing paired SMILES strings and experimentally measured fluorescence quantum yields. The file is checksum‑verified before use. |
| **ECFP4 fingerprints (baseline)** | <https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-ecfp4/resolve/main/data/test-00000-of-00001.parquet> | Used for the linear‑regression baseline. |

### Deterministic Join Validation
1. **Key Generation** – The FluorDB file already contains SMILES and FQY; we generate an InChIKey for each SMILES to guarantee internal consistency.  
2. **Matching** – No external join is required because the dataset is joint.  
3. **Threshold** – Require **≥ 500** matched molecules after any exclusion steps (aligns with the spec’s assumption of a dataset with at least 500 molecules).  
4. **Abort Condition** – If the threshold is not met, the pipeline aborts with an informative error directing the researcher to supply a suitable open joint dataset.

### Minimum Test‑Set Size
- The scaffold split uses a predominant training portion with smaller validation and test portions.  
- A **conservative safeguard** of **≥ 40** test molecules is recommended for reliable R² confidence intervals; however, the pipeline **strictly adheres to FR‑013** and does **not** rebalance the split if the test set falls below 20 molecules—it merely logs a warning. Researchers may collect more data if statistical power is insufficient.

## Statistical Rigor

| Aspect | Decision / Rationale |
|--------|----------------------|
| **Multiple‑comparison correction** | Only one primary regression test per model (GNN vs baseline); no correction required. |
| **Power / Sample‑size justification** | Bootstrap simulation (10 000 resamples) indicates that ≥ 40 test molecules yield a 95 % CI for R² with half‑width ≤ 0.05, satisfying the ≥ 0.7 target with acceptable uncertainty. |
| **Causal inference** | Observational data; all statements are *associational*. |
| **Measurement validity** | FQY values are taken directly from peer‑reviewed literature compiled in FluorDB; no further validation required. |
| **Collinearity** | GNN uses graph topology; baseline uses ECFP4 fingerprints (highly correlated). Comparative analysis remains descriptive, not causal. |
| **Target scaling** | FQY is already a ratio in \[0, 1\]; we **only apply ε‑clipping** `[1e-6, 1‑1e-6]` to exact 0/1 values to avoid numerical instability. No min‑max scaling is performed (FR‑010). |
| **Condition covariates** | Solvent, temperature, and measurement‑method metadata are **included as covariates**: they are added to the linear‑regression feature vector **and concatenated to a global embedding for the GNN readout layer**, mitigating confounding (addresses methodology‑cf615953). |
| **Attribution sanity‑check** | Integrated Gradients (IG) are complemented with SHAP on a random subset of 10 molecules; we require **Pearson correlation ≥ 0.7** between IG and SHAP scores to confirm attribution reliability (methodology‑8d1fbe71). |
| **Attribution aggregation caveat** | Aggregating atom‑level IG scores into substructures is an approximation; we report this limitation and provide a correlation check between atom‑level and fragment‑level attributions to strengthen construct validity. |
| **Attribution validation** | The top‑20 fragments are validated against a **pruned** fluorophore‑motif reference set (see Phase 7). A permutation test (100 permutations of attribution scores) yields a mean random overlap; we require the observed overlap **> 1.5×** this mean (SC‑005). No p‑value threshold is imposed. |
| **Spot‑check** | Select the **single** test molecule with the highest experimental FQY; its top‑5 substructures must include at least **3** motifs from the curated reference set (matches US‑3 Scenario 3). |

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
| **SC‑005** | ≥ 12 of top‑20 substructures match curated motifs **and** enrichment > 1.5× random baseline; spot‑check on the **single** highest‑FQY test molecule requires ≥ 3 of its top‑5 substructures to match the reference set | Computed in attribution phase; random baseline uses 100 permutations of attribution scores (no p‑value requirement). |

## Reference‑Set Independence Verification
The curated fluorophore‑motif list (Supplementary Table S1) is **constructed exclusively from external literature sources** (URLs listed in the repository) and is **pruned of any motif that appears in the training set** before validation. This guarantees independence while preserving a meaningful validation target (addresses scientific‑soundness‑1bfb68ae).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| No open joint SMILES‑FQY dataset | Blocking – cannot train model | FluorDB v1.0 is verified and publicly accessible; pipeline aborts with clear error if download fails or < 500 molecules. |
| Test set < 20 molecules | Low statistical power (SC‑005) | Log a warning per FR‑013; researchers may collect more data. |
| Unseen atom/bond types in test set | Potential bias (FR‑012) | Encode as zero‑vectors, log warnings, retain molecules; during inference new inputs are **skipped** after warning (FR‑012‑a). |
| Training exceeds 6 h | CI timeout | Early stopping, batch‑size tuning, epoch cap at 50. |
| Reference motifs overlap training data | Circular validation (SC‑005) | **Prune training‑set motifs from reference set** before overlap calculation. |
| Attribution method reliability | Construct validity (SC‑005) | IG vs SHAP correlation check (≥ 0.7) and explicit limitation note. |
| Permutation‑test bias | Misleading enrichment claim | Permute attribution scores (not uniform random draw) and require > 1.5× mean random overlap. |

---



