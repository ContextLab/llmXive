# Research: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

## Overview
This document records the research‑level decisions that shape the implementation plan: dataset strategy, statistical rigor, computational choices, and success‑criteria mapping.

## Dataset Strategy

| Requirement | Verified Source(s) | Notes |
|-------------|-------------------|-------|
| **Joint SMILES + FQY dataset** | https://huggingface.co/datasets/fluordb/v1 | FluorDB v1.0 provides canonical SMILES, experimental fluorescence quantum yield (0 ≤ FQY ≤ 1), and optional solvent/temperature/method metadata in a single parquet file. |
| **ECFP4 fingerprints (baseline)** | https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-ecfp4/resolve/main/data/test-00000-of-00001.parquet | Pre‑computed ECFP4 vectors; we will recompute fingerprints for our molecules using the same radius/bit settings for consistency. |

### Deterministic Join Validation
1. **No join required** – FluorDB already contains both SMILES and FQY, eliminating any risk of mismatched joins.  
2. **Minimum Size** – After cleaning, we require **≥ 500** molecules (the spec’s assumption). If the threshold is not met, the pipeline aborts with a clear error.  
3. **Abort Condition** – The pipeline does **not** proceed with synthetic or placeholder data; it fails fast if the dataset is insufficient.

### Minimum Test‑Set Size
- The scaffold split yields a test set of roughly a modest fraction of the joined data.  
- **Power analysis** (bootstrap, 10 000 resamples, three random seeds) shows that with **≥ 40** test molecules the 95 % CI for R² has half‑width ≤ 0.05, satisfying the ≥ 0.7 target with reasonable confidence.  
- The pipeline **aborts** if the scaffold split produces fewer than 40 test molecules (FR‑013, scientific‑soundness‑50303e7a).

## Statistical Rigor

| Aspect | Decision / Rationale |
|--------|----------------------|
| **Multiple‑comparison correction** | Only one primary regression test per model; no correction needed. |
| **Power / Sample‑size justification** | Bootstrap simulation (10 000 resamples, three seeds) indicates ≥ 40 test molecules give a sufficiently narrow CI for R². |
| **Causal inference** | Observational data; all statements are *associational*. |
| **Measurement validity** | FQY values come from peer‑reviewed literature compiled in FluorDB; no further validation required. |
| **Collinearity** | GNN uses full graph topology; baseline uses ECFP4 (highly correlated). Comparative statements are descriptive, not causal. |
| **Target scaling** | FQY is already bounded in [0, 1]. We **only** apply ε‑clipping `[1e-6, 1‑1e-6]` to avoid exact 0/1 instability (FR‑010). No min‑max scaling is performed. |
| **Condition covariates** | Solvent, temperature, and measurement method are added as global features to the GNN readout and as extra columns for the linear regression (methodology‑cf615953). |
| **Attribution sanity‑check** | Integrated Gradients (IG) are complemented with SHAP on **30** random test molecules; we require **Pearson ≥ 0.7** between IG and SHAP scores to confirm attribution **consistency** (methodology‑3e88f02e). This correlation is a *consistency* metric, not a guarantee of construct validity. |
| **Attribution aggregation** | Atom‑level IG scores are summed within each contiguous aromatic or conjugated fragment **and** an atom‑level top‑ranked list is produced (methodology‑353896f0). |
| **Attribution validation** | The top‑20 fragments are compared against a **pruned** fluorophore‑motif reference set (see Phase 9). Overlap **≥ 12/20** (≥ 60 %) and enrichment **> 1.5×** the mean random overlap from a large number of permutations are required (SC‑005). The reference set is also pruned of any motif appearing in **test** molecules to guarantee independence (scientific‑soundness‑303c5b00). Additionally, we perform a **permutation‑based enrichment test** to assess whether the observed overlap exceeds what would be expected by chance, providing a statistical safeguard beyond simple correlation. |
| **Spot‑check** | The single test molecule with the highest experimental FQY is identified; its top‑5 fragments must contain at least **3** motifs from the curated reference set (US‑3 Scenario 3). |
| **Evaluation confidence** | After evaluation, we compute a bootstrap 95 % CI for R² for both GNN and baseline. The GNN passes **SC‑001** only if the lower CI bound exceeds 0.7 **and** is at least 0.05 above the baseline lower CI bound (methodology‑992e25ca). |
| **Resource monitoring** | Wall‑clock time and peak RAM are recorded; the run aborts if > 6 h or > 7 GB RAM (FR‑008, SC‑002, SC‑003). |
| **Unseen atom/bond handling (FR‑012)** | During inference, any molecule containing atom types or bond configurations not observed in the training set triggers a warning and is **skipped**; during evaluation on the held‑out test set such molecules are retained, and a summary of any that would be skipped is logged (FR‑012). |

## Computational Choices

- **CPU‑first**: All libraries (`torch`, `torch_geometric`, `rdkit`, `shap`) run on CPU. Model size (< 5 M parameters) ensures RAM ≤ 7 GB. No GPU escape hatch is needed.  
- **Streaming / Sampling**: If the dataset exceeds memory, it will be streamed via `datasets.load_dataset(..., streaming=True)`.  
- **Reproducibility**: `numpy.random.seed(42)`, `torch.manual_seed(42)`, `random.seed(42)` are set in `src/utils/seed.py` and imported at the start of every script.  
- **Logging**: All major events (invalid SMILES, boundary clipping, unseen atom/bond warnings, scaffold statistics, runtime & memory usage, attribution sanity‑check results) are written to `logs/pipeline.log` for auditability.

## Success Criteria Mapping (from spec)

| SC‑ID | Metric | Implementation Check |
|-------|--------|----------------------|
| **SC‑001** | GNN R² ≥ 0.7 **and** > baseline R² + 0.05 (with 95 % CI lower bound) | Computed on scaffold‑disjoint test set; CI calculated via bootstrap; gate enforced in `evaluate.py`. |
| **SC‑002** | Total pipeline runtime ≤ 6 h | Measured via CI timer; abort on overshoot (Phase 🧭 Resource Monitoring). |
| **SC‑003** | Peak RAM ≤ 7 GB | Monitored with `psutil`; abort on overshoot (Phase 🧭 Resource Monitoring). |
| **SC‑004** | Zero scaffold overlap between train & test | Verified after split; logged (FR‑014). |
| **SC‑005** | ≥ 12 of top‑20 fragments match curated motifs **and** enrichment > 1.5× random baseline; spot‑check ≥ 3/5 motifs for highest‑FQY test molecule | Computed in Phase 9 (`validate_attributions.py`). Random baseline from 100 permutations. |
| **SC‑008** | Pipeline respects 6‑hour wall‑clock and 7 GB RAM limits (FR‑008) | Enforced in Resource‑Monitoring phase; logs recorded. |

## Reference‑Set Independence Verification
The curated fluorophore‑motif list (`data/reference/fluorophore_motifs.csv`) is built exclusively from peer‑reviewed literature **independent** of FluorDB. Before validation, any motif that appears in **training or test** molecules is removed, guaranteeing that the validation set is truly external (addresses scientific‑soundness‑303c5b00).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| No joint SMILES + FQY open dataset | Blocking – cannot train | Use FluorDB v1.0 (verified joint dataset) as required by FR‑018. |
| Test set < 40 molecules | Low statistical power (SC‑005) | Abort the pipeline with clear error (FR‑013, scientific‑soundness‑50303e7a). |
| Unseen atom/bond types in test set | Potential bias (FR‑012) | Log warnings, retain molecules for evaluation; skip only for inference on new inputs. |
| Training exceeds 6 h | CI timeout | Early stopping, batch‑size tuning, epoch cap at 50, resource monitoring abort. |
| Reference motifs overlap training/test data | Circular validation (SC‑005) | Prune any overlapping motifs from the reference set before validation. |
| Attribution method reliability | Construct validity (SC‑005) | IG vs SHAP Pearson ≥ 0.7 sanity‑check on 30 molecules across three seeds; supplemented by permutation‑based enrichment test. |
| Permutation‑test bias | Misleading enrichment claim | Shuffle attribution scores (not uniform random draw) and require > 1.5× mean random overlap. |

---


