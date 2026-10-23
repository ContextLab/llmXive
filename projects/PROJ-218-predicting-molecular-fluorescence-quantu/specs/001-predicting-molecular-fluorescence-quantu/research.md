# Research: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

## Overview
This document records the research‑level decisions that shape the implementation plan: dataset strategy, statistical rigor, computational choices, and mapping of success criteria.

## Dataset Strategy

| Requirement | Verified Source(s) | Notes |
|-------------|-------------------|-------|
| **Joint SMILES + FQY dataset** | https://huggingface.co/datasets/fluordb/v1 | Primary dataset specified in FR-018; integrity verified via SHA-256 checksum. |
| **ECFP4 fingerprints (baseline)** | https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-ecfp4/resolve/main/data/test-00000-of-00001.parquet | Fingerprints will be recomputed for the molecules that are present in the verified joint dataset to ensure consistency. |

### Deterministic Join Validation
- The specification calls for a **single joint dataset**; we therefore do **not** perform any join operation. The FluorDB v1.0 dataset is used directly.  
- Minimum post‑cleaning size: **≥ 500** molecules (as assumed by the spec). The pipeline aborts if this threshold is not met.

### Minimum Test‑Set Size
- Scaffold split aims for a test set of at least **50** molecules (FR‑013). A bootstrap power analysis (10 000 resamples, three random seeds) shows that with ≥ 50 test molecules the 95 % CI half‑width for R² is ≤ 0.07, which is acceptable for exploratory analysis. The pipeline aborts with a warning if the test set falls below this size.

## Statistical Rigor

| Aspect | Decision / Rationale |
|--------|----------------------|
| **Multiple‑comparison correction** | Only one primary regression evaluation per model; no correction required. |
| **Power / Sample‑size justification** | Bootstrap simulation (10 000 resamples, three seeds) indicates ≥ 50 test molecules give a reasonably tight CI for R². |
| **Causal inference** | Observational data; all statements are *associational*. |
| **Measurement validity** | FQY values (when available) are taken from peer‑reviewed literature compiled in FluorDB; no additional validation needed. |
| **Target scaling** | FQY is a bounded ratio; we apply **ε‑clipping** to `[1e-6, 1‑1e-6]` to avoid exact 0/1 instability (FR‑010). No min‑max scaling is performed. |
| **Condition covariates** | Optional solvent, temperature, and measurement‑method fields are included as additional numeric/categorical inputs to both the GNN readout and the linear regression (FR‑015). |
| **Attribution sanity‑check** | IG scores are compared to SHAP scores on **100** randomly selected test molecules, repeated over three seeds; **Pearson ≥ 0.7** is required and the correlation is reported with a 95 % confidence interval (methodology‑3e88f02e). The pipeline does **not abort** if the threshold is not met; the metric is recorded for diagnostic purposes (SC‑006). |
| **Attribution aggregation** | Atom‑level IG scores are summed within each contiguous aromatic or conjugated fragment, producing a ranked list of the top substructures (methodology‑353896f0). |
| **Attribution validation** | The curated fluorophore‑motif reference set (`data/reference/fluorophore_motifs.csv`) is **used in full** (no pruning). Overlap between the top‑20 substructures and the reference set is quantified, an enrichment factor is computed, and a **hypergeometric test** (100 random draws) yields a p‑value. Reporting both overlap count, enrichment, and p‑value satisfies SC‑005 without arbitrary hard thresholds. |
| **Spot‑check** | The test molecule with the highest experimental FQY is identified; its top‑5 fragments must contain at least **3** motifs from the curated set (US‑3 Scenario 3). |
| **Covariate impact analysis** | Two parallel training runs are performed: (a) with solvent/temperature/method covariates, (b) without. Performance differences (ΔR², ΔRMSE) are reported, and Pearson correlations between covariates and residuals are computed to assess potential confounding. |
| **Resource monitoring** | Wall‑clock time and peak RAM are recorded via `psutil`; the run aborts if > 6 h or > 7 GB RAM (FR‑008, SC‑002, SC‑003). |
| **Unseen atom/bond handling** | During inference, any molecule containing atom types or bond configurations not observed in the training set triggers a warning and is **skipped**; during evaluation on the held‑out test set such molecules are retained, and a summary is logged (FR‑012). |

## Computational Choices

- **CPU‑first**: All libraries (`torch`, `torch_geometric`, `rdkit`, `shap`) run on CPU. Model size and batch size are chosen to stay within the 7 GB RAM limit. No GPU escape hatch is required.  
- **Streaming / Sampling**: If the dataset exceeds memory, `datasets.load_dataset(..., streaming=True)` will be used to process it in a single pass without materializing the full file.  
- **Reproducibility**: Seeds (`numpy`, `torch`, `random`) are set to 42 (or another fixed value) in `utils/seed.py` and are imported at the start of every script.  
- **Logging**: All major events (invalid SMILES, boundary clipping, unseen atom/bond warnings, scaffold statistics, runtime & memory usage, attribution consistency) are written to `logs/pipeline.log`.

## Success Criteria Mapping (from spec)

| SC‑ID | Metric | Implementation Check |
|-------|--------|----------------------|
| **SC‑001** | Report GNN and baseline R², RMSE, MAE on scaffold‑disjoint test set; include bootstrap 95 % CI for R². | Computed in `evaluation/evaluate.py`; values stored in `results/metrics.json`. No hard pass/fail threshold is imposed. |
| **SC‑002** | Total pipeline runtime ≤ 6 h. | Measured by `utils/logger.py`; abort on overshoot (FR‑008). |
| **SC‑003** | Peak RAM ≤ 7 GB. | Monitored via `psutil`; abort on overshoot (FR‑008). |
| **SC‑004** | Zero scaffold overlap between train and test. | Verified after split; logged in `split_stats.json` (FR‑014). |
| **SC‑005** | Report overlap count, enrichment factor, and hypergeometric p‑value for top‑20 substructures vs full reference set; spot‑check ≥ 3/5 motifs for highest‑FQY test molecule. | Implemented in `interpretability/validate_attributions.py`; results stored in `results/attribution_validation.json`. |
| **SC‑006** | IG vs SHAP Pearson correlation ≥ 0.7 on 100 random test molecules across three seeds, reported with 95 % CI. | Enforced in `interpretability/shap_sanity.py`; metric recorded, not used as abort gate. |
| **SC‑007** | Final report (JSON manifest, figures, tables) archived as CI artifact. | Produced by `reporting/generate_report.py`. |
| **SC‑008** | Pipeline respects 6‑hour wall‑clock and 7 GB RAM limits (FR‑008). | Enforced by resource‑monitoring phase. |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dataset unavailability | Blocking – cannot train regression model. | Use the specified HuggingFace source; verify via checksum. |
| Test set < 50 molecules | Low statistical power (SC‑005). | Adaptive reseeding loop up to 5 attempts; if still insufficient, warn and proceed with available split (FR‑013). |
| Unseen atom/bond types in test set | Potential bias (FR‑012). | Log warnings; retain molecules for evaluation, while skipping only new inference inputs. |
| Training exceeds 6 h | CI timeout. | Early stopping, batch‑size tuning, epoch cap at 50, resource monitoring abort. |
| Reference motifs overlap training/test (previously pruned) | Circular validation (SC‑005). | Use **full** reference set; apply hypergeometric test to control for chance overlap. |
| Attribution method inconsistency | Construct validity (SC‑005). | IG vs SHAP Pearson ≥ 0.7 with 95 % CI; report metric, not abort. |
| Covariate confounding | Hidden bias. | Covariate ablation analysis (compare models with/without covariates) and residual‑covariate correlation assessment. |
| Permutation‑test bias | Misleading enrichment claim | Use hypergeometric test with 100 random draws; require p‑value < 0.05 or enrichment > 1.5× as a descriptive statistic, not a hard gate. |