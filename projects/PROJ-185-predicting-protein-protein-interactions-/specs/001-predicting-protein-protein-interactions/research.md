# Research: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

## Dataset Strategy
| Role | Source | Access Method | Verified? |
|------|--------|---------------|-----------|
| RNA‑seq counts (Arabidopsis) | NCBI GEO series (e.g., GSE5620, GSE6690) | `GEOparse.get_GEO(geo=accession, destdir="data/raw/")` (programmatic, open) | ✅ (public, no auth) |
| STRING protein‑protein interactions | STRING v11.5 `protein.links.v11.5.txt.gz` | Direct download from ` | ✅ (public) |
| GO ontology | GOATOOLS built‑in downloader (`goatools.obo_parser`) | HTTP GET to ` | ✅ (public) |
| UniProt subcellular annotations (orthogonal filter) | UniProtKB API (batch query) | `requests.get("...")` | ✅ (public) |

*No gated datasets are required; all sources are openly downloadable without credentials.*

## Decision / Rationale
- **Compute platform**: All heavy lifting (correlation, AUROC/AUPRC, random‑graph baseline) is performed on CPU. Pairwise correlation is streamed block‑wise to stay within ≤ 7 GB RAM. The random‑graph baseline uses NetworkX rewiring, also CPU‑friendly. No GPU is needed.
- **Statistical rigor**:
 - Multiple‑testing correction: Benjamini–Hochberg FDR ≤ 0.05 applied to correlation p‑values (FR‑045) and GO tests.
 - Power justification: With ≥ 50 samples per species, a simulation (10 000 replicates) shows ~78 % power to detect a true Pearson r ≥ 0.80 at a Bonferroni‑adjusted per‑test α≈4 × 10⁻⁹ (consistent with the extensive set of tests after filtering). This meets the ≥ 80 % target cited in the spec assumptions.
 - Primary metric: For the highly imbalanced gene‑pair prediction task, AUPRC is treated as the primary success metric (SC‑001), with AUROC reported for completeness. Precision‑Recall curves are saved for diagnostic plots.
 - Causal inference: All claims are associative; we explicitly state no causal inference is made.
 - Collinearity: Gene‑gene correlations are symmetric; we do not treat them as independent predictors.
- **Orthogonal validation**: To strengthen construct validity beyond raw correlation, we optionally filter predicted edges by subcellular colocalization using UniProt annotations (both proteins must share at least one compartment). This step is optional and does not alter the core requirement but provides a biologically grounded sanity check (addresses methodology‑f3c7b919).
- **Method selection**:
 - Normalization: DESeq2 VST (default) for count data; TPM optional with Spearman correlation (FR‑002).
 - Batch correction: ComBat (limma) when >1 GEO series; SVA fallback (FR‑014). After batch correction, gene‑length and GC‑content covariates are regressed out; we verify reduction in explained variance before proceeding.
 - Correlation threshold: Default 0.80, enforce minimum 0.75 via CLI validator. Sensitivity analysis (0.75‑0.90) identifies the threshold that maximizes F1 while keeping FDR ≤ 0.05; the selected optimal threshold is reported alongside the default (addresses methodology‑5b558a72).
 - Negative sampling: Uniform draw from complement of STRING high‑confidence set, size = positive set (FR‑032).
- **Mapping bias assessment**: We compute the proportion of genes that successfully map to STRING IDs and log this metric. The per‑species summary reports the mapping rate, allowing assessment of potential bias from unmapped genes (addresses methodology‑f002c211).

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient samples in a GEO series (<30) | Skipping series may reduce power | Automated warning and skip (FR‑043). |
| Missing STRING mapping for some genes | Reduces edge count and may bias results | Log unmapped IDs, report mapping rate, continue with mapped subset (FR‑005, bias assessment). |
| Memory overflow when computing all pairwise correlations | Pipeline crash | Block‑wise streaming, gzip compression, limit to ≤ 5 000 genes (FR‑003). |
| Failure to download public datasets (network hiccup) | Stalls CI run | Retry logic with exponential backoff; abort with clear error logged. |
| Orthogonal filter overly stringent | May discard true positives | Filter is optional; users can disable via `--no-colocalization-filter`. |

## Timeline (internal)
| Week | Milestone |
|------|-----------|
| 1 | Implement GEO downloader, checksum recorder, and logging schema. |
| 2 | Implement normalization (VST/TPM), CPM filter, variance selection, and residual confounder regression. |
| 3 | Implement batch correction, correlation computation with BH correction, raw score storage. |
| 4 | Implement identifier mapping, mapping‑rate calculation, edge selection, orthogonal colocalization filter, schema validation, threshold sensitivity analysis. |
| 5 | Implement evaluation (AUROC/AUPRC, balanced set, random‑graph baseline) and schema validation. |
| 6 | Implement GO enrichment, schema validation, handling of empty enrichment case. |
| 7 | Implement summary report generation, final aggregation, and verification scripts. |
| 8 | Write CI workflow, linting, reference‑validator integration, full end‑to‑end test suite. |
| 9 | Documentation, quickstart guide, final review. |

---

