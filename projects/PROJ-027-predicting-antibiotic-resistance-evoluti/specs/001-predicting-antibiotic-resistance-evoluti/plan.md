# Implementation Plan: Predicting Antibiotic Resistance Evolution from Genomic Sequences

**Branch**: `001-predict-antibiotic-resistance` | **Date**: 2026-10-19 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-predict-antibiotic-resistance/spec.md`

## Summary
The plan now fulfills **FR‑001** by programmatically downloading *E. coli* whole‑genome FASTA sequences **and** paired susceptibility phenotypes from the open NCBI Pathogen Detection API. The primary outcome is the **binary phenotypic resistance label** (Resistant = 1, Susceptible = 0) for each antibiotic class, preserving the original research question and SC‑001. All other functional requirements (FR‑002 – FR‑009) and success criteria (SC‑001 – SC‑004) are retained and explicitly mapped to pipeline phases.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `biopython`, `dendropy`, `statsmodels`, `pyyaml`, `datasets`, `requests` (for NCBI API)  
- **Storage**: Local file system (`data/` hierarchy)  
- **Testing**: `pytest` (unit, contract, integration)  
- **Target Platform**: Linux (GitHub Actions free‑tier runner)  
- **Constraints**: CPU‑only, ≤ 7 GB RAM, ≤ 6 h runtime, ≤ 5000 isolates – the CI run will use **N = 1000** isolates to guarantee feasibility.  

## Constitution Check
| Principle | Status | How the plan satisfies it |
|-----------|--------|---------------------------|
| **I. Reproducibility** | ✅ | Fixed random seeds, deterministic data‑fetch via NCBI Pathogen Detection API and 🤗 datasets, `requirements.txt` pins all packages. |
| **II. Verified Accuracy** | ✅ | All external data sources are verified open URLs (NCBI API, CARD download, HuggingFace GenBank parquet). No speculative citations. |
| **III. Data Hygiene** | ✅ | Raw downloads are checksummed; every transformation writes a new file under `data/processed/`; no in‑place edits. |
| **IV. Single Source of Truth** | ✅ | **`data-model.md`** is designated as the SSoT for all downstream artifacts (see Constitution Check entry). |
| **V. Versioning Discipline** | ✅ | `hash_artifacts.py` computes SHA‑256 hashes for every file in `data/` and `code/` after each major stage. |
| **VI. Genomic Feature Traceability** | ✅ | Feature extraction logs map each SNP/gene to its source isolate ID and the tool (`Snippy`/`ARIBA`). |
| **VII. Statistical Significance Verification** | ✅ | Implements 1000 phylogenetically‑aware **label permutation** tests; p‑value threshold < 0.05 enforced. |

## Project Structure
```
specs/001-predict-antibiotic-resistance/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── feature_matrix.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md   # generated later by /speckit-tasks

code/
├── 01_ingest/
│   ├── download_genbank.py
│   └── ingest_phenotype.py
├── 02_process/
│   ├── run_snippy.sh
│   ├── run_ariba.sh
│   └── build_feature_matrix.py
├── 03_model/
│   ├── train_models.py
│   └── evaluate.py
├── 04_validate/
│   ├── phylo_permutation.py        # label permutation preserving clades
│   ├── sensitivity_analysis.py
│   └── verify_results.py
├── 05_viz/
│   └── generate_plots.py
├── utils/
│   ├── logging.py
│   ├── config.py
│   └── hash_artifacts.py
├── main.py
└── requirements.txt

tests/
├── contract/
│   ├── test_feature_matrix_schema.py
│   └── test_model_output_schema.py
├── integration/
│   └── test_pipeline.py
└── unit/
    ├── test_ingest.py
    └── test_feature_extraction.py

data/
├── raw/            # downloaded GenBank parquet + phenotype CSV
├── processed/      # feature matrices, phylogeny trees, class_to_genes.json, feature_ranking.csv, verification_summary.json
└── models/         # sklearn model pickles, metrics.json
```

## Workflow & Gates
1. **Ingestion (FR‑001 – satisfied)** –  
   - Download the **NCBI GenBank parquet** dataset via 🤗 datasets (`datasets.load_dataset("pulmo/ncbi-genbank-complete", split="train")`).  
   - Filter for the taxon ID of Escherichia coli (E. coli).  
   - For each isolate, fetch susceptibility metadata (AST) from the **NCBI Pathogen Detection API** (`https://www.ncbi.nlm.nih.gov/pathogens/`).  
   - Output: `data/raw/isolates_manifest.csv` (FASTA paths, phenotype CSV, checksums).  

2. **Contract Validation (mandatory gate)** – Run `pytest tests/contract/`. Failure aborts the pipeline.  

3. **Processing** – Run Snippy (SNP calling) and ARIBA (CARD gene detection) on each isolate (batch‑processed, ≤ 2 threads).  
   - **SNP‑derived numeric features**: counts per gene region.  
   - **Gene‑presence binary features**: all CARD genes (including the target gene).  

4. **Feature Matrix Assembly** (`build_feature_matrix.py`) –  
   - Merge SNP counts and gene‑presence flags.  
   - Apply **VIF filtering** (remove features with VIF > 5).  
   - **Mechanism‑blind filter**: for each target antibiotic class, **remove the canonical resistance gene column *and* any SNPs whose genomic coordinates fall within that gene’s locus**.  
   - Output: `data/processed/feature_matrix_filtered.csv`.  

5. **Model Training (FR‑004, FR‑009)** –  
   - Algorithms: L1‑regularized Logistic Regression (`solver='saga'`, `penalty='l1'`) and Random Forest (`n_estimators=200`).  
   - **Cross‑validation**: 5‑fold **phylogenetically‑blocked CV** – isolates are grouped by clade (derived from the core‑SNP tree) and whole clades are held out per fold.  
   - **Edge‑case handling**: Classes with **< 50 resistant isolates** are excluded with warning W001. If *all* classes are excluded, pipeline aborts with error **E004**.  
   - **Outputs**:  
     - `data/models/{gene}_logreg.pkl` and `data/models/{gene}_rf.pkl`  
     - `data/models/metrics.json` (AUC‑ROC, PR, CV stats per class)  
     - `data/processed/feature_ranking.csv` (global feature importance)  
     - `data/processed/class_to_genes.json` (list of gene‑presence features used per class)  

6. **Statistical Validation (FR‑005, FR‑006, SC‑002, SC‑003)** –  
   - **Permutation Test**: 1000 **phylogenetically‑aware label permutations** – shuffle phenotypic labels **within each clade** to preserve population structure, then recompute AUC.  
   - **Threshold Sweep**: evaluate thresholds {0.4, 0.45, 0.5, 0.55, 0.6}; record FP/FN rates.  
   - **Power Analysis**: For each retained antibiotic class compute a post‑hoc power estimate using observed effect size (Cohen’s d) and sample size; report in `verification_summary.json`.  
   - **Outputs**: `data/results/{gene}_perm_test.json`, `data/results/{gene}_sensitivity.json`.  

7. **Versioning** – Run `hash_artifacts.py` to update `state/` hashes after each major stage.  

8. **Visualization (FR‑007)** – Generate ROC, PR, and feature‑importance plots; save under `data/figures/`.  

9. **Verification Summary** (`04_validate/verify_results.py`) –  
   - Consumes `data/models/metrics.json`, `data/processed/feature_ranking.csv`, and `data/processed/class_to_genes.json`.  
   - Writes `data/processed/verification_summary.json` containing AUC, p‑value, top‑10 feature table, and FP/FN rates across thresholds.  
   - CI fails if any required metric is missing or if the permutation p‑value ≥ 0.05.  

## Mapping FR / SC to Phases
| FR / SC | Pipeline Phase | Notes |
|--------|----------------|-------|
| FR‑001 | **Ingestion** – downloads FASTA *and* phenotype via NCBI API. |
| FR‑002 | **Processing** – Snippy + ARIBA produce SNP counts & gene presence. |
| FR‑003 | **Processing** – `build_feature_matrix.py` creates stratified, phylogenetically‑blocked splits. |
| FR‑004 | **Model Training** – scikit‑learn Logistic Regression & Random Forest (CPU‑only). |
| FR‑005 | **Statistical Validation** – 1000 phylogenetically‑aware label permutations. |
| FR‑006 | **Statistical Validation** – threshold sweep {0.4‑0.6}. |
| FR‑007 | **Visualization** – `generate_plots.py`. |
| FR‑008 | **Not needed** – outcome is phenotypic; all genomic features are permissible after mechanism‑blind filter. |
| FR‑009 | **Model Training** – separate model per antibiotic class. |
| SC‑001 | **Model Training / Evaluation** – report AUC‑ROC on held‑out test set. |
| SC‑002 | **Permutation Test** – p < 0.05 required. |
| SC‑003 | **Sensitivity Analysis** – report FP/FN variation across thresholds. |
| SC‑004 | **Compute Feasibility** – CI run limited to N = 1000 isolates; memory & time budgets respected. |

## Compute Feasibility Assessment
- **Memory**: Feature matrix (on the order of a thousand rows × ~12 k features) ≈ 100 MB; intermediate VCFs streamed; peak RAM < 3 GB.  
- **CPU**: Snippy/ARIBA limited to 2 threads; total wall‑time for a batch of 1000 isolates is ≈ 3–4 h on the free runner; remaining stages < 1 h.  
- **Runtime Buffer**: < 6 h total, satisfying SC‑004.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing phenotype data for some isolates | Medium | Skip isolates lacking AST; log exclusion count (W002). |
| Snippy/ARIBA runtime > 6 h | High | Batch processing; abort batch if > 10 min per 50 isolates. |
| Extreme class imbalance (e.g., < 5 % resistant) | Medium | Skip classes with < 50 resistant isolates; report warning. |
| Memory OOM due to large VCFs | Medium | Delete raw FASTA/VCF after extraction; stream files. |
| Circularity between gene presence and phenotype | Low (addressed) | Mechanism‑blind filter removes target gene *and* SNPs within its locus. |
| Invalid permutation null | High | Permute phenotypic labels **within clades**, preserving structure. |

## Edge‑Case Handling (as per spec)
- **Insufficient isolates for a class (< 50 resistant)** → Log warning W001, skip training for that class.  
- **All classes insufficient** → Exit with error code **E004** and no model output.  
- **Missing phenotype metadata for an isolate** → Drop isolate, log exclusion count (W002).  
- **Feature extraction failure for an isolate** → Skip isolate, log isolate ID, continue.  

---



