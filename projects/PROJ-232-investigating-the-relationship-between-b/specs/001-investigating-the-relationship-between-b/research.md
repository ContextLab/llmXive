# Research: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

## Research Question
*Original*: Do resting‑state functional‑connectivity network metrics (global efficiency, modularity, participation coefficient, network‑specific efficiencies, edge strengths) associate with individual differences in Music Emotion Rating (MER) scores, controlling for age, sex, and framewise displacement?

*Current status*: **Not testable with verified open data.** The Data‑Gap Report (Task 0.1) confirms that none of the verified sources contain the required paired fMRI‑connectivity and MER variables. Consequently the primary analysis halts until a compliant dataset is supplied or the spec is revised.

## Data Availability (decisive finding)

The **Verified Datasets** block supplies three HCP parquet sources and three MER‑related CSV/parquet sources. None contain the required columns (`subject_id`, `age`, `sex`, `fd_mean`, `mer_score`, `fc_upper_tri`). The HCP “Music Task” subset is gated and thus unavailable for unattended download.

| Dataset | URL | Required variables present? | Status |
|---|---|---|---|
| HCP parquet #1 | `https://huggingface.co/datasets/7eu7d7/HCP-Diffusion-datas/resolve/main/Lexica.art.parquet` | No (`subject_id`, `age`, `sex`, `fd_mean`, `mer_score`, `fc_upper_tri` missing) | Verified URL, **wrong content** |
| HCP parquet #2 | `https://huggingface.co/datasets/ramandeepsaha/hcp/resolve/main/train.csv` | No | Verified URL, **wrong content** |
| HCP parquet #3 | `https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet` | No | Verified URL, **wrong content** |
| MER CSV #1 | `https://huggingface.co/datasets/mercor/apex-accounting-harbor/resolve/main/tasks/world-9-task-26-33d90130/environment/task_files/filesystem/billing_realization_summary_fy2024.csv` | No (billing data) | Verified URL, **wrong content** |
| MER CSV #2 | `https://huggingface.co/datasets/Celiadraw/text-to-mermaid/resolve/main/true_clean.csv` | No (text‑to‑mermaid) | Verified URL, **wrong content** |
| MER parquet #3 | `https://huggingface.co/datasets/TOBEAI/KOR_Merged_data/resolve/main/data/train-00000-of-00003.parquet` | No | Verified URL, **wrong content** |
| HCP Music‑Task Subset | *No open URL* (access‑gated) | Would contain needed variables but cannot be fetched unattended. | **UNVERIFIED / gated** |

**Conclusion**: No open, programmatically downloadable dataset provides the paired neuro‑behavioral data required. The pipeline therefore writes `reports/data_gap_report.json` and stops, preserving reproducibility and avoiding fabrication.

## Dataset Strategy

| Dataset | URL | Required variables present? | Status |
|---|---|---|---|
| HCP parquet #1 | `https://huggingface.co/datasets/7eu7d7/HCP-Diffusion-datas/resolve/main/Lexica.art.parquet` | No | Verified, **mismatch** |
| HCP parquet #2 | `https://huggingface.co/datasets/ramandeepsaha/hcp/resolve/main/train.csv` | No | Verified, **mismatch** |
| HCP parquet #3 | `https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet` | No | Verified, **mismatch** |
| MER CSV #1 | `https://huggingface.co/datasets/mercor/apex-accounting-harbor/resolve/main/tasks/world-9-task-26-33d90130/environment/task_files/filesystem/billing_realization_summary_fy2024.csv` | No | Verified, **mismatch** |
| MER CSV #2 | `https://huggingface.co/datasets/Celiadraw/text-to-mermaid/resolve/main/true_clean.csv` | No | Verified, **mismatch** |
| MER parquet #3 | `https://huggingface.co/datasets/TOBEAI/KOR_Merged_data/resolve/main/data/train-00000-of-00003.parquet` | No | Verified, **mismatch** |
| HCP Music‑Task Subset | *No open URL* | Would meet all requirements | **Gated – unavailable** |

The pipeline **does not** fabricate or substitute any dataset; it records the gap and awaits a compliant source.

## Spec Revision Required
FR‑001 (download paired fMRI + MER) and FR‑002 (CPU‑only fMRIPrep) cannot be satisfied with any currently verified open dataset. The specification must be updated to either:

1. Provide an open dataset that includes raw resting‑state NIfTI files **and** MER scores, **or**  
2. Relax the requirement to accept pre‑computed connectivity matrices paired with MER scores (removing/re‑scoping FR‑002 and FR‑003).

Until such a revision, the pipeline stops after the validation gate and emits a Data‑Gap Report.

## Statistical Rigor & Methodology (implemented, gated on valid data)

| Aspect | Method |
|--------|--------|
| Multiple comparisons | Benjamini–Hochberg FDR, q < 0.05 (Task 2.3) |
| Power | `statsmodels.stats.power` computes achieved power for detecting `r = 0.20` at α = 0.05; if `N < required_N` the pipeline aborts primary modeling and labels results as exploratory (Task 2.1). |
| Causal framing | Observational; all statements are associational (Constitution VII) |
| Measurement validity | **Limitation**: The MER instrument used in the external datasets has not been independently validated for musical‑emotion perception in the current open sources. This limitation is explicitly noted. |
| Collinearity | VIF screening (VIF > 5) for scalar metrics; edge‑level predictors reduced via PCA before regression (Task 2.2). |
| Confounds | Age, sex, and mean FD included as covariates in both partial correlation and regression |
| Edge‑weight handling | Correlation matrices transformed to absolute values; top [deferred] positive edges retained before graph‑theory calculations (Task 1.2) |

## Compute Feasibility
- **CPU‑first**: All analyses (matrix reconstruction, graph metrics, PCA, Ridge CV) run comfortably on 2 CPU cores, < 2 GB RAM, < 30 min total. No GPU is required.
- The validation gate executes in seconds and is the expected terminal step under current data availability.

## Decision Rationale
1. **Honesty over fabrication** – The verified sources lack required variables; fabricating data would violate Constitution I & III.  
2. **Reusable pipeline** – All analysis code is fully implemented and tested, ready for a compliant dataset.  
3. **Explicit scope gap** – The Data‑Gap Report provides a reproducible, auditable record of why the primary analysis cannot proceed, supporting downstream spec revision.

## Limitations
- Primary analysis cannot run without an open paired dataset.  
- fMRIPrep preprocessing (Constitution VI) is pending raw fMRI availability.  
- All statistical results are conditional on the validation gate passing; currently none are produced.

## Future Directions (pending data)
When a compliant dataset is supplied (e.g., placed at `data/subjects.parquet` conforming to `contracts/dataset.schema.yaml`), the same command `python src/main.py` will execute the full pipeline: extraction → graph metrics → PCA → partial correlations + Ridge CV → FDR → figures → `results/analysis_results.csv`.

---



