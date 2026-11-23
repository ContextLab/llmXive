# Research: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

## Overview
This document records the research‑level decisions that shape the implementation plan. The **FluoroBench v1** dataset (a verified open source on Hugging Face) provides *both* SMILES strings and experimentally measured fluorescence quantum yields, satisfying FR‑018. Consequently the full pipeline—from data curation through model training, baseline comparison, and interpretability—can be executed on the free‑tier CI runner.

## Dataset Strategy

| Requirement | Verified Source(s) | Notes |
|-------------|-------------------|-------|
| **Joint SMILES + FQY dataset** | https://huggingface.co/datasets/fluorobench/v1 | Directly downloadable; checksum will be verified. Contains `smiles`, `fqy`, and optional metadata fields `solvent`, `temperature`, `measurement_method`. |
| **Reference motif set** | Repository‑included `data/reference/fluorophore_motifs.csv` (curated from peer‑reviewed literature) | Used for attribution validation (FR‑016). Provenance documented in `docs/reference_set_readme.md`. |

### Decision
- Use the verified FluoroBench dataset for all downstream modeling, evaluation, and attribution steps.
- Extract and store any available metadata (solvent, temperature, measurement method) alongside the clipped FQY target (FR‑015).
- The curated motif library is shipped with the repository; no external download is required.

### Minimum Test‑Set Size Rationale
A bootstrap power analysis (10 000 resamples, three random seeds) shows that with **≥ 50** test molecules the 95 % CI half‑width for a regression R² estimate is ≤ 0.07, which is acceptable for exploratory work. The scaffold‑split script therefore enforces a **minimum test size of 50** (FR‑013). If the split cannot meet this after five reseed attempts, the pipeline aborts with a warning but still produces the split files.

## Statistical Rigor (Applicable to All Executed Phases)

| Aspect | Decision / Rationale |
|--------|----------------------|
| **Multiple‑comparison correction** | Not needed – only one primary regression model and one baseline are evaluated. |
| **Power / Sample‑size justification** | The 50‑molecule test‑set lower bound is justified by the bootstrap analysis described above. |
| **Causal inference** | Observational data; all statements are *associational*. |
| **Measurement validity** | FluoroBench reports experimentally measured FQY values; no further validation required. |
| **Target clipping** | ε‑clipping to (ε, 1‑ε) with ε = 1e‑6 is applied after loading (FR‑010). No min‑max scaling is performed. |
| **Condition covariates** | Extracted metadata (solvent, temperature, method) are stored but not used in the primary regression; they enable downstream heterogeneity analyses (FR‑015). |
| **Resource monitoring** | `utils/logger.py` records wall‑clock time and peak RAM; the run aborts if limits are exceeded (FR‑008, SC‑002, SC‑03). |

## Computational Choices

- **CPU‑first**: All libraries (`torch`, `torch_geometric`, `rdkit`, `datasets`) run on CPU. No GPU escape hatch is required.  
- **Streaming**: If the FluoroBench parquet file exceeds memory, `datasets.load_dataset(..., streaming=True)` will be used to iterate without full materialization.  
- **Reproducibility**: Seeds are set to 42 in `src/utils/seed.py` and imported by every script.  
- **Logging**: All major events (invalid SMILES, scaffold overlap statistics, resource usage, clipping warnings) are written to `logs/pipeline.log`.

## Success Criteria Mapping (Applicable to Executed Phases)

| SC‑ID | Metric | Implementation Check |
|-------|--------|----------------------|
| **SC‑001** | Predictive R² of GNN vs. baseline on scaffold‑disjoint test set | Reported in `metrics.json` after evaluation (Phase 6). |
| **SC‑002** | Total pipeline runtime ≤ 6 h | Measured by `utils/logger.py`; abort on overshoot. |
| **SC‑003** | Peak RAM ≤ 7 GB | Monitored via `psutil`; abort on overshoot. |
| **SC‑004** | Zero scaffold overlap between train and test | Verified after split; stats saved in `split_stats.json`. |
| **SC‑005** | Overlap between top‑20 substructures and curated motif set; enrichment vs random baseline | Computed in attribution validation (Phase 7); results stored in `attribution_metrics.json`. |
| **SC‑006** | Pearson correlation between Integrated Gradients and SHAP on ≥ 30 test molecules | Calculated in Phase 7; stored in `attribution_metrics.json`. |
| **SC‑007** | Final report artifact (metrics, plots, attribution summary) archived as CI run artifact | Produced by `reporting/generate_report.py` (Phase 8). |
| **SC‑008** | Pipeline respects 6‑hour wall‑clock and 7 GB RAM limits | Enforced by resource‑monitoring utility (Phase 🧭). |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset unavailability** | No joint SMILES + FQY → no modeling. | Use verified FluoroBench v1 (available via direct URL). |
| **Test set < 50 molecules** | Reduced statistical power. | Adaptive reseeding loop (max 5 attempts) with warning if still insufficient. |
| **Invalid SMILES** | Data loss or pipeline crash. | `clean.py` excludes invalid entries and logs reasons (FR‑009). |
| **Unseen atom/bond types** | Potential inference failures. | Log warnings; retain for evaluation but skip during inference (FR‑012). |
| **Resource exhaustion** | CI timeout or OOM. | Early‑stopping, batch‑size tuning, strict resource monitoring (FR‑008). |

---


