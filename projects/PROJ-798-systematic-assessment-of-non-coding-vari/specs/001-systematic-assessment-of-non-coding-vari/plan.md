# Implementation Plan: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

**Branch**: `001-gene-regulation` | **Date**: 2026-10-10 | **Spec**: [link]  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
Implement a reproducible, CPU‑only pipeline that (1) streams and downloads common human SNPs (MAF > 1 %) from dbSNP (a recent build version), (2) filters them to ENCODE/Roadmap regulatory regions and creates a GC‑matched non‑regulatory control set, (3) loads the latest JASPAR PWMs and computes allele‑specific binding affinity changes (Δ Score) using a dynamic window equal to the PWM length, and (4) tests whether Δ Score distributions are enriched in GWAS Catalog lead SNPs via a Kolmogorov‑Smirnov test and a West‑Stephens max‑T permutation FDR correction. All steps are fully instrumented, checksum‑verified, and produce schema‑validated artefacts. Runtime is bounded to ≤ 6 h on a free‑tier CI runner by streaming, batch processing, and limiting the analysis to the A set of highly informative TF motifs.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `biopython`, `pybedtools`, `pysam`, `requests`, `pyyaml`  
- **System Dependencies**: `bedtools` (installed via `apt-get` in CI)  
- **Storage**: Local file hierarchy under `data/` (VCF, BED, Parquet, CSV)  
- **Testing**: `pytest` + contract validation (`jsonschema`)  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU, 7 GB RAM)  
- **Performance Goals**: End‑to‑end runtime ≤ 6 h, peak RAM < 7 GB  
- **Constraints**: CPU‑only; batch size of k SNP‑TF pairs; limit to 200 PWMs (information‑content ≥ 1.5 bits per position); optional sub‑sampling to a computationally manageable number of SNPs if full set exceeds compute budget; permutation count fixed at **500** (see below).  

## Constitution Check
| Principle | How the Plan Satisfies It |
|-----------|---------------------------|
| I. Reproducibility | Fixed `requirements.txt`, pinned random seeds (`config.SEED`), deterministic FTP URLs, explicit `.gitignore` patterns removed (not required for verification), checksums recorded in `state/projects/...yaml`. |
| II. Verified Accuracy | All external datasets are fetched from the canonical URLs specified in the spec (dbSNP FTP, JASPAR HTTP, ENCODE FTP, GWAS Catalog FTP). No unverified mirrors are used. |
| III. Data Hygiene | Every transformation writes to a new file; `utils/checksum.py` records SHA‑256 hashes; raw files remain immutable under `data/raw/`. |
| IV. Single Source of Truth | Each figure/table in the final report references a single row in `results_summary.csv` or `scores.parquet`; the pipeline logs the provenance of every derived artefact. |
| V. Versioning Discipline | Artifact hashes are written to `state/projects/...yaml` after each stage; any change invalidates downstream caches. |
| VI. Biophysical Proxy Validity | Affinity changes are computed exclusively with PWM log‑odds scores from JASPAR; a sensitivity analysis using high‑information PWMs and optional chromatin‑accessibility covariates is performed. |
| VII. Population‑Genetic Independence | GWAS lead SNPs are read from a separate FTP source; permutation shuffles GWAS labels **within** LD blocks and GC/TSS strata, preserving independence between motif scoring and GWAS status. |

## Project Structure
```text
specs/001-gene-regulation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset_schema.schema.yaml
│   ├── enrichment_result_schema.schema.yaml
│   └── ... (other schemas)
└── tasks.md          # generated later

code/
├── __init__.py
├── config.py
├── data_ingestion/
│   ├── __init__.py
│   ├── fetch_dbsnp.py          # streaming FTP download with retry logic
│   ├── fetch_gwas.py
│   ├── fetch_motifs.py
│   └── filter_regions.py
├── scoring/
│   ├── __init__.py
│   ├── pwm_scorer.py
│   └── delta_calculator.py
├── analysis/
│   ├── __init__.py
│   ├── enrichment_test.py
│   └── fdr_correction.py
├── utils/
│   ├── __init__.py
│   ├── checksum.py
│   └── logger.py
└── main.py
tests/
├── unit/
│   ├── test_filter_regions.py
│   └── test_pwm_scorer.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schema_validation.py
```

## Complexity Tracking & Verification Fixes
| Task | Description | Verification |
|------|-------------|--------------|
| **T002** | Implement robust FTP download in `fetch_dbsnp.py` using `ftplib` with retry logic and streaming to avoid OOM. | Script exits 0 and produces `data/raw/snps_raw.vcf.gz` with matching checksum. |
| **T003** | LD‑block definition and stratified permutation logic (GC/TSS/chromatin bins). | Unit test verifies that each SNP receives an `ld_block_id` and `stratum_id`, and that label shuffling respects block and stratum boundaries. |
| **T004** | End‑to‑end pipeline orchestration (`main.py`). | Integration test checks that `results_summary.csv` conforms to `contracts/enrichment_result_schema.schema.yaml`. |
| **T005** | Limit analysis to the top 200 PWMs (information‑content ≥ 1.5 bits) and optionally sub‑sample SNPs to 500 k if full set exceeds memory budget. | Runtime profiling confirms ≤ 6 h on 2 CPU CI runner. |
| **T006** | Permutation count increased to **500** for robust West‑Stephens max‑T FDR correction with stratified shuffling (preserve LD blocks and GC/TSS/chromatin strata). | Empirical null distribution stable; minimal p‑value = 0.002. |
| **T007** | Sensitivity analysis for \\|Δ Score\\| threshold (1.5, 2, 2.5 bits). | Generates supplemental tables reporting stability of enrichment results. |
| **T008** | KS test performed on block‑aware, stratified permutation null (computes KS on each shuffled label set, preserving LD blocks and GC/TSS/chromatin bins) against GC‑matched control set. | Verified by unit test that p‑values are derived from permutation distribution and that control set is used as reference. |
| **T009** | Tail‑enrichment test with Fisher's exact, including covariate adjustment for DNase‑I hypersensitivity (optional). | Unit test confirms correct contingency table construction. |
| **T010** | Report & artefact generation – final CSV/MD files. | `results_summary.csv` passes schema validation. |

### Updated Methodology to Address Panel Concerns
* **Control of Genomic Confounds (methodology-35e2fac0)** – Permutations are stratified not only by LD block but also by GC‑content bins, distance‑to‑TSS bins, and optionally by DNase‑I hypersensitivity scores (when available). This ensures that chromatin accessibility, TF expression proxies, and positional biases do not drive spurious enrichment. Each SNP is assigned a `stratum_id` (composite of GC bin + TSS distance bin + optional chromatin bin), and within each permutation iteration, GWAS labels are shuffled **only within each LD block and stratum pair**, preserving local genomic structure and baseline regulatory enrichment.
* **Reference Distribution for KS Test (methodology-2777032d)** – The primary KS comparison is **GWAS‑lead SNPs vs. the GC‑matched non‑regulatory control set**. The "outside GWAS" SNPs are explicitly excluded from the KS test to avoid contaminating the reference with regulatory enrichment. The control set is matched for GC content and LD structure, providing an unbiased baseline. A secondary KS comparison using the GC‑matched control set is performed for robustness and is reported in the results summary.

## Spec Alignment & Requirement Traceability
| Requirement | Plan Element(s) | Coverage |
|------------|----------------|----------|
| FR‑001 | `data_ingestion/fetch_dbsnp.py`, `filter_regions.py` | ✅ |
| FR‑002 | `scoring/pwm_scorer.py` | ✅ |
| FR‑003 | `scoring/delta_calculator.py` | ✅ |
| FR‑004 | `analysis/enrichment_test.py` (stratified label shuffle within LD blocks and GC/TSS/chromatin strata) | ✅ |
| FR‑005 | `analysis/enrichment_test.py` (KS on GC‑matched control set, not outside-GWAS SNPs) | ✅ |
| FR‑006 | `analysis/fdr_correction.py` (West‑Stephens max‑T, **500** permutations, stratified shuffling) | ✅ |
| FR‑007 | `analysis/enrichment_test.py` (per‑TF p‑value output) | ✅ |
| FR‑008 | `analysis/fdr_correction.py` (α = 0.05) | ✅ |
| SC‑001 | Logging in `filter_regions.py` + `score.parquet` row counts | ✅ |
| SC‑002 | Post‑hoc verification of corrected p‑values | ✅ |
| SC‑003 | Enrichment ratio computed in `enrichment_test.py` | ✅ |

## Phase Breakdown (≈ 10 tasks)
1. **Fetch raw dbSNP VCF** – T002 (streamed, checksum).  
2. **Fetch ENCODE/Roadmap BED, GWAS Catalog BED, JASPAR PWMs** – T005.  
3. **LD pruning & block assignment with stratification (GC/TSS/chromatin bins)** – T003.  
4. **Regulatory filtering & GC‑matched control generation** – T007.  
5. **PWM loading & dynamic‑window scoring** – T008.  
6. **Δ Score computation & flagging** – T009.  
7. **Permutation (N=500, stratified by LD block and stratum) & West‑Stephens FDR** – T006.  
8. **KS testing (block‑aware, stratified, control‑set reference) & tail‑enrichment testing** – T010.  
9. **Report & artefact generation** – T011.  

All tasks are deterministic, schema‑validated, and run within the CPU‑first budget.

---