# Research: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

## Dataset Strategy
| Role | Source | Access Method | Verified? |
|------|--------|---------------|-----------|
| RNA‑seq counts (Arabidopsis) | NCBI GEO series (e.g., GSE5620, GSE6690) | `GEOparse.get_GEO(geo=accession, destdir="data/raw/")` (programmatic, open) | ✅ (public, no auth) |
| STRING protein‑protein interactions | STRING v11.5 `protein.links.v11.5.txt.gz` | Direct download from ` | ✅ (public) |
| GO ontology | GOATOOLS built‑in downloader (`goatools.obo_parser`) | HTTP GET to ` | ✅ (public) |
| UniProt subcellular annotations (orthogonal filter) | UniProtKB API (batch query) | `requests.get("...")` | ✅ (public) |

| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| **RNA‑seq counts** | NCBI GEO (public) | `datasets.load_dataset("geo", data_dir="data/raw", split="train", streaming=False)` via `geopy`‑style API (or `ncbi-geo-downloader` CLI) | Series list supplied in `species.yaml`. Series with < 30 samples are omitted (FR‑043). |
| **STRING protein‑protein interactions** | STRING (v11.5) | Direct download from verified HuggingFace parquet: ` | Only edges with combined score ≥ 700 *and* without evidence channels `coexpression`, `transcriptomics`, `gene_expression` are retained (FR‑006). |
| **GO ontology** | GO (released via GOATOOLS at runtime) | Automatic download by GOATOOLS (`goatools.obo_parser.GODag`) | No external URL needed; GOATOOLS caches the OBO file. |

*No other external datasets are required.* All downloads are fully scriptable on a fresh GitHub Actions runner.

## Methodological Decisions & Rationale

| Decision | Rationale | Compute Placement |
|----------|-----------|-------------------|
| **Normalization** | Default VST (DESeq2) preserves variance for count data; TPM option supported for compositional data (FR‑002). | CPU (R via `rpy2` runs on 2 cores). |
| **Correlation** | Pearson for VST, Spearman for TPM (FR‑004). Block‑wise streaming to keep RAM < 6 GB. | CPU – pure NumPy/SciPy. |
| **Threshold** | Default 0.80; CLI enforces lower bound 0.75 (FR‑012, T012). | CPU – enforced in `run_pipeline.py`. |
| **Batch‑effect correction** | ComBat (limma) when > 1 GEO series; fallback to SVA if metadata missing (FR‑014). | CPU – R implementation via `rpy2`. |
| **Negative sampling** | Uniform sampling from complement of STRING high‑confidence set, size = |positive| (FR‑032). | CPU – `numpy.random`. |
| **Random‑graph baseline** | Degree‑preserving edge rewiring (on the order of |E| swaps) (FR‑007). | CPU – NetworkX. |
| **GO enrichment** | Fisher’s exact test + Benjamini‑Hochberg (FR‑008). | CPU – GOATOOLS. |
| **Sensitivity analysis** | Evaluate thresholds across a low‑to‑high range (e.g., 0.80, 0.85, 0.90) (FR‑025). | CPU – repeated correlation filtering. |
| **Pilot benchmark** | Held‑out Arabidopsis GEO series not used for model building; compute precision/recall for default threshold (FR‑048). | CPU – same pipeline, separate config. |
| **GPU Escape Hatch** | None required – all steps are fully tractable on CPU within the 6‑h budget. No GPU offload planned. |

## Statistical Rigor

* **Multiple‑testing** – GO enrichment p‑values corrected via Benjamini‑Hochberg (FR‑008).
* **Power justification** – Minimum 50 samples per species (FR‑001) ensures > 80 % power to detect a true Pearson r = 0.8 at α = 0.05 (Cohen, 1992). This is documented in `metadata/power_analysis.txt`.
* **Causal inference** – All claims are associational; co‑expression is not assumed causal (Constitution Principle VII).
* **Measurement validity** – DESeq2 VST and TPM are standard, peer‑reviewed normalizations; STRING high‑confidence edges are curated experimentally.
* **Collinearity** – Edge list is undirected; no regression on correlated predictors, so collinearity is not a concern.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient GEO samples (< 50) | Abort (FR‑047) | Provide fallback species list; log clear error. |
| STRING file format change | Evaluation failure | Pin to specific STRING release version (v11.5) and verify header fields at download time. |
| Memory blow‑up for 5 000 genes | > 6 GB RAM | Stream correlations in large gene blocks; use `np.memmap` for intermediate storage. |
| Batch‑effect metadata missing | SVA fallback may be slower | Log warning, proceed with SVA; benchmark time budget. |

---
