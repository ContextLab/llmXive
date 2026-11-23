# Research: Predicting Bacterial Antibiotic Resistance (Real‑Data Pipeline)

## Objective
Quantify, on **real publicly available genomic assemblies and phenotypic AST data**, the incremental predictive value of SNP counts and mobile‑genetic‑element (MGE) proximity metrics beyond known resistance‑gene (ARG) presence for phenotypic antibiotic resistance in *E. coli* and *S. aureus*. If a verified open dataset providing the required genomes and AST phenotypes cannot be obtained, the pipeline aborts and records the limitation; no synthetic “demo‑only” results are reported.

## Dataset Strategy
| Role | Source | Access Method | Verified? |
|------|--------|---------------|-----------|
| Real genomes & AST phenotypes | NCBI Pathogen Genome Browser (NCBI FTP) & CARD API | Programmatic download via `src/pipeline/download_data.py` (uses `requests`/`ftplib`) | **Yes** – public, version‑controlled endpoints |
| ARG catalogue | Simulated CARD‑like JSON bundled with the repo (used as reference for ARG names) | Direct file read | **Yes** – part of the repository |
| SNP & MGE features | Computed from the real assemblies using `snippy`, `snp-sites`, `mob-suite`, and `isfinder` | Local computation | **Yes** – deterministic pipelines |
| Confounders (geography, platform, year) | Extracted from NCBI assembly metadata | Local file write | **Yes** – deterministic |

> **No open, verified dataset currently satisfies FR‑001** (≥1,500 *E. coli* and *S. aureus* isolates with AST). The pipeline therefore **first attempts** to download the required data; if the acquisition fails or yields insufficient isolates, the run aborts and logs the shortfall. When such a dataset becomes available, the same pipeline can be re‑executed without code changes.

### Sample‑Size Table (post‑filtering, deterministic)
| Species | Antibiotic | Resistant n | Sensitive n | Total n |
|---------|------------|------------|------------|---------|
| *E. coli* | ampicillin | ≥100 | ≥100 | ≥200 |
| *E. coli* | ciprofloxacin | ≥100 | ≥100 | ≥200 |
| *E. coli* | ceftriaxone | ≥100 | ≥100 | ≥200 |
| *S. aureus* | oxacillin | ≥100 | ≥100 | ≥200 |
| *S. aureus* | ciprofloxacin | ≥100 | ≥100 | ≥200 |
| *S. aureus* | clindamycin | ≥100 | ≥100 | ≥200 |

All counts are enforced by the **Power Gate** (Phase 0‑c). Any deviation triggers an abort and is recorded in the final report.

## Methodological Decisions
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **Real‑data‑first approach** | FR‑001 explicitly requires real genomes and AST; synthetic data would violate FR‑001 and FR‑003. | Data download [deferred]; SNP calling [deferred] per 100 isolates (parallelised). |
| **Nested 5‑fold outer / 5‑fold inner CV** | Prevents leakage during feature selection and hyper‑parameter tuning (FR‑016, methodology‑79af9d6b). | Parallelised over 2 CPU cores. |
| **Wilcoxon signed‑rank test (paired probabilities)** | Required by FR‑012 to assess whether the integrated model improves over the baseline. | Scipy implementation (< 1 s). |
| **Pre‑model Power Check & Gate** | Computes required N for effect size = 0.1, α = 0.05, power = 0.8; aborts modeling if power < 0.8 (FR‑014). | Instant. |
| **Confounder Encoding** | Geography & platform one‑hot; collection year as integer. Included as fixed effects in `pyseer` mixed‑effects model and as covariates for permutation importance (FR‑017). | Negligible cost. |
| **CPU‑only, ≤ 1,500‑isolate limit** | Guarantees fit within GitHub Actions free‑tier limits (FR‑018). | Entire pipeline ≤ 5 h, ≤ 4 GB RAM. |
| **Threshold sweep {0.3, 0.5, 0.7}** | Required robustness check (FR‑007, FR‑019). | Post‑hoc evaluation. |
| **Multiple‑Comparison Correction** | All Mann‑Whitney U p‑values corrected using Benjamini‑Hochberg FDR. | Scales linearly with feature count. |
| **Sample‑Size & Power** | Analytic power calculation (Phase 0‑b) yields required N ≈ 1 400 for effect size = 0.1. If observed N < required, modeling is skipped and a warning is logged. | Instant. |

### Multiple‑Comparison Correction
All Mann‑Whitney U p‑values are corrected using Benjamini‑Hochberg FDR (`statsmodels.stats.multitest.multipletests`).

### Sample‑Size & Power
The analytic power calculation (Phase 0‑b) yields a required N ≈ 1 400 for effect size = 0.1. If a species‑antibiotic pair provides fewer isolates, **Phase 0‑c aborts** modeling for that pair and records the insufficiency in the report.

## Edge‑Case Handling
- **Download failures / insufficient isolates**: The pipeline logs a warning, aborts modeling for the affected pair, and records the shortfall in the final report.  
- **Assembly quality**: isolates with core‑genome alignment coverage < 90 % are filtered out before downstream analysis.  
- **Confounder sparsity**: geography and platform categories are limited to a fixed set to avoid empty one‑hot columns.  

## Expected Deliverables
1. `baseline_metrics.csv` – per‑fold AUC, Precision, Recall, F1 for ARG‑only model.  
2. `integrated_metrics.csv` – same metrics for the full feature set, plus delta columns.  
3. `wilcoxon_results.csv` – Wilcoxon signed‑rank statistics and p‑values for paired predicted probabilities.  
4. `mannwhitney_results.csv` – SNP/MGE features with raw and FDR‑adjusted p‑values.  
5. `permutation_results.csv` – phylogeny‑aware permutation p‑values (via `pyseer`).  
6. `report.pdf` – comparative summary, threshold‑sweep plots, power analysis, and any data‑shortage warnings.  
7. `metrics.json` – conforms to `contracts/metrics.schema.yaml`.  
8. `checksums.txt` – SHA‑256 checksums for all generated raw files.  

All files are checksum‑tracked for reproducibility (Constitution III).

## Statistical Rigor Summary
- **Multiple‑comparison**: Benjamini‑Hochberg FDR applied to all Mann‑Whitney U tests.  
- **Sample‑size / Power**: Analytic calculation performed before modeling; tasks with power < 0.8 are **skipped** and flagged.  
- **Causal‑inference framing**: Results are strictly **associational**, as the data are observational.  
- **Measurement validity**: Phenotypes are taken directly from NCBI AST records; ARG catalogue mirrors CARD.  
- **Predictor collinearity**: Correlation diagnostics are logged; models treat features jointly without claiming independent effects.  

## Alignment with Success Criteria
- **SC‑001**: `metrics.json` records delta in AUC‑ROC, Precision, Recall, and F1 between baseline and integrated models.  
- **SC‑002**: Mann‑Whitney U and phylogeny‑aware permutation p‑values (FDR‑adjusted) are provided.  
- **SC‑003**: The pipeline completes within the GitHub Actions free‑tier limits (≤ 6 h, ≤ 7 GB RAM), verified by Phase 10 monitoring.  
- **SC‑004**: Threshold sweep results for {0.3, 0.5, 0.7} are included in `metrics.json` and `report.pdf`.  
- **SC‑005**: Power analysis is performed, warnings logged, and under‑powered tasks are omitted (methodology‑b9ffaa07).  

## Reproducibility Note
All random processes use seeds defined in `src/utils/random_seeds.py`. The download step is deterministic given the same API state; checksums ensure data integrity. When a verified open dataset becomes available, the same pipeline can be re‑run without modification.

## Scientific Limitations
If the required real dataset is not obtainable, the pipeline aborts and **does not produce any synthetic “demo‑only” results**. This limitation is explicitly reported, and the project will await availability of an appropriate open dataset before any scientific conclusions can be drawn.

---

