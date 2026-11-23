# Research: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase‑Change Materials

## Overview
This document outlines the research design, data‑source verification, and methodological choices that will drive the implementation plan. All references are limited to the URLs listed in the “Verified datasets” block of the spec.

## Dataset Strategy

| Role | Dataset | Source (Verified URL) | Access Method | Variables Provided | Fit to FR/SC |
|------|---------|-----------------------|---------------|--------------------|--------------|
| Primary training & feature generation | **PCM (parquet)** | https://huggingface.co/datasets/stefania-radu/rendered_wikipedia_pcm/resolve/main/data/train-00000-of-00001.parquet | `datasets.load_dataset("stefania-radu/rendered_wikipedia_pcm", split="train", streaming=False)` | `composition`, `latent_heat_J_per_g`, `melting_point_K`, `heat_capacity_J_per_mol_K`, optional `structure_id` (rare). | Supplies melting point, heat capacity, latent heat → satisfies FR‑001. Provides compositional info for elemental descriptors (FR‑002). |
| Crystal‑structure source (graph features) | **OMDB Structures** | https://huggingface.co/datasets/omdb/structures | `datasets.load_dataset("omdb/structures")` | CIF files for a subset of compounds; enables `pymatgen` `StructureGraph` construction. | Enables FR‑002 for compounds with available CIFs; missing‑structure rows will receive `has_structure=0`. |
| External validation (independent) | **NIST PCM** | https://huggingface.co/datasets/pcmoraesmenezes/incorrect_records/resolve/main/incorrect_records.jsonl | `datasets.load_dataset("pcmoraesmenezes/incorrect_records", split="train")` | Same thermodynamic variables as primary dataset, curated from NIST experimental measurements. | Provides ≥ 50 literature PCMs distinct from the primary PCM source → satisfies Principle VII and FR‑005/FR‑006. |
| Auxiliary (optional imputation check) | **NIST PCM (small subset)** | Same URL as above | Same loader | Contains latent heat values for a small set of compounds. | Used only for imputation‑rate reporting (FR‑003 edge case). |

*No open Materials Project API is required; crystal‑graph representations are built from the OMDB structures dataset. Missing structures are handled via a binary indicator (`has_structure`) and logged (see Risk & Mitigation).*

## Methodological Choices

| Question | Decision | Rationale (Constitution‑linked) |
|----------|----------|---------------------------------|
| **Modeling framework** | Classical tree‑based models (RandomForest, XGBoost) + shallow MLP (CPU) + SHAP + PySR | CPU‑friendly, deterministic, reproducible (Principle I). |
| **Symbolic regression** | PySR (CPU mode, max 500 generations, population 100) | Provides interpretable formulas; runs within 4 h on free runner (FR‑003, SC‑002). |
| **Label definition** | Binary “phase‑change‑suitable” = latent heat > 150 J/g (primary); sensitivity sweep {[deferred]} J/g | Directly sourced from literature (Reference [1]) → satisfies FR‑008, SC‑007. |
| **Class imbalance handling** | Stratified train‑test split + `class_weight='balanced'` in tree models | Guarantees fair evaluation (SC‑005). |
| **Multiple‑comparison correction** | Bonferroni correction for the five label thresholds and three feature‑importance cut‑offs when performing paired t‑tests (SC‑001). |
| **Power justification** | Minimum 5 000 compounds yields > 80 % power to detect an R² ≥ 0.05 at α = 0.05 (effect size f² = 0.0526, Several predictors, calculated via `statsmodels.stats.power.FTestPower`). If fewer rows are available, the limitation is reported (SC‑005). |
| **Collinearity diagnostics** | Compute Pearson correlation matrix among all elemental descriptors; flag pairs with |r| > 0.9, compute VIF, and report descriptive relationships (FR‑006). |
| **Causal stance** | All claims are framed as *predictive associations*; no causal language is used (Principle VII). |

## Decision Log

| Decision | CPU vs GPU | Reasoning |
|----------|------------|-----------|
| Use CPU‑only tree models, MLP, and PySR | CPU | All methods have faithful CPU implementations; fits free‑tier runner budget. |
| No GPU escape hatch required | N/A | No method demands CUDA; avoids unnecessary off‑load. |
| Fallback to composition‑only descriptors for missing CIFs | CPU | OMDB provides CIFs for only a subset; missing‑structure rows receive `has_structure=0` and are included in models to avoid systematic bias. |
| Perform MCAR assessment on missing structures | CPU | Ensures that missingness does not bias results (addresses methodology‑10b4ca7c). |

---


## Statistical Rigor Checklist (per SC)

- **Multiple‑comparison correction**: Bonferroni for 5 label thresholds and 3 feature‑importance cut‑offs.  
- **Sample‑size / power**: Minimum 5 000 rows → > 80 % power for detecting R² ≥ 0.05 (see Power Justification).  
- **Causal‑inference stance**: Observational dataset; all findings framed as associative (Principle VII).  
- **Measurement validity**: Latent‑heat values come from peer‑reviewed literature (PCM dataset) – validated by the dataset’s provenance.  
- **Collinearity handling**: Correlation matrix, variance inflation factor (VIF) computed; high VIF rows flagged and interpreted descriptively.  

## Missing‑Data Analysis (new)

- Compute the proportion of compounds without a matching CIF in OMDB.  
- Run Little’s MCAR test (via `statsmodels.stats.diagnostic.little_test`).  
- Add binary column `has_structure` (1 = CIF present, 0 = absent) to the merged dataset; include it as a feature in all models.  
