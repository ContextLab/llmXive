# Research: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

## Research Question
*Original*: Do resting‑state functional‑connectivity network metrics (global efficiency, modularity, participation coefficient, network‑specific efficiencies, edge strengths) associate with individual differences in Music Emotion Rating (MER) scores, controlling for age, sex, and framewise displacement?

*Current status*: **Not testable with verified open data.** The Data‑Gap Report (Task 0.2) confirms that none of the verified sources contain the required paired fMRI‑connectivity and MER variables. Consequently the primary analysis halts until a compliant dataset is supplied or the spec is revised.

## Data Availability (the decisive finding)

The Verified Datasets block lists three “HCP” URLs and two “MER” URLs. Inspection of their actual content shows a fatal variable mismatch:

| Dataset | URL | Content | Required variables present? |
|---|---|---|---|
| “MER” Turkish QA corpora | `https://huggingface.co/datasets/MercanAI/turkce-sft-qa-3.7m/resolve/main/data/test-00000.parquet`<br>`https://huggingface.co/datasets/merve/turkish_instructions/resolve/main/instructions.csv` | Text instructions/QA, no MER scores, no subjects, no imaging. | **No** |
| “HCP” parquet files | `https://huggingface.co/datasets/7eu7d7/HCP-Diffusion-datas/resolve/main/Lexica.art.parquet`<br>`https://huggingface.co/datasets/ramandeepsaha/hcp/resolve/main/train.csv`<br>`https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet` | No confirmed `subject_id`, `age`, `sex`, `fd_mean`, `fc_upper_tri`, or MER columns. | **No** |
| HCP Subjects Release (Music Task subset) | *No open URL* (access‑gated) | Would contain required variables but cannot be fetched unattended. | **UNVERIFIED / gated** |

**Conclusion**: No verified, programmatically downloadable source provides the paired neuro‑behavioral data required by the study. The pipeline therefore includes a strict validation gate that writes `reports/data_gap_report.json` and terminates without fabricating data.

## Dataset Strategy

| Dataset | URL | Required variables present? | Status |
|---|---|---|---|
| “MER” Turkish QA corpora | `https://huggingface.co/datasets/MercanAI/turkce-sft-qa-3.7m/resolve/main/data/test-00000.parquet`<br>`https://huggingface.co/datasets/merve/turkish_instructions/resolve/main/instructions.csv` | No – unrelated text data | Verified URL, **wrong content** |
| “HCP” parquet files | `https://huggingface.co/datasets/7eu7d7/HCP-Diffusion-datas/resolve/main/Lexica.art.parquet`<br>`https://huggingface.co/datasets/ramandeepsaha/hcp/resolve/main/train.csv`<br>`https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet` | No – missing required columns | Verified URLs, **unverified contents** |
| HCP Subjects Release (Music Task subset) | *No open URL* (access‑gated) | Would contain all required variables | **UNVERIFIED / gated** |

The pipeline **does not** substitute any of these with synthetic data. Instead, it records the gap and awaits a compliant dataset.

## Spec Revision Required

FR‑001 (download paired fMRI + MER) and FR‑002 (CPU‑only fMRIPrep preprocessing) cannot be satisfied with any currently verified open dataset. The specification must be updated to either:

1. Provide an open dataset that includes raw resting‑state NIfTI files **and** MER scores, **or**
2. Relax the requirement to use pre‑computed functional connectivity matrices paired with MER scores (removing or re‑scoping FR‑002 and FR‑003 accordingly).

Until such a revision is made, the pipeline will stop after the validation gate and produce a Data‑Gap Report.

## Statistical Rigor & Methodology (implemented, gated on valid data)

| Aspect | Method |
|---|---|
| Multiple comparisons | Benjamini–Hochberg FDR, q < 0.05, across all metric‑wise tests |
| Power | Per‑metric achieved power for detecting r = 0.20 at α = 0.05 (using `statsmodels`). If N < 194, the run summary flags the analysis as under‑powered (SC‑005). |
| Causal framing | Observational; all statements are associational. |
| Measurement validity | No validated open MER instrument is available; this limitation is noted explicitly. |
| Collinearity | VIF screening (VIF > 5) for scalar network metrics; edge‑level predictors are reduced via PCA before regression (Task 2.2). |
| Confounds | Age, sex, and mean FD are included as covariates in partial correlation and regression. |
| Edge‑weight handling | Correlation matrices are transformed to absolute values and thresholded to retain the top 10 % strongest positive edges before graph‑theory metrics (Task 1.2). |

## Compute Feasibility

- **CPU‑first**: All steps (matrix reconstruction, graph metrics, PCA, Ridge CV) run comfortably on 2 CPU cores within < 30 min and < 2 GB RAM. No GPU is required.
- The validation gate runs in seconds and is the expected terminal step under the current data availability.

## Decision Rationale

1. **Honesty over fabrication** – The verified sources lack the needed variables; fabricating or substituting unrelated data would violate the fabrication gate.  
2. **Reusable analysis pipeline** – All analysis code is implemented and thoroughly tested, ready to process a genuine dataset when it becomes available.  
3. **Explicit scope gap** – By generating a Data‑Gap Report we provide a clear, reproducible record of why the primary analysis cannot proceed, supporting downstream spec revision.

## Limitations

- Primary analysis cannot execute until a verified open dataset containing resting‑state fMRI and MER scores is provided.  
- fMRIPrep preprocessing (Constitution VI) cannot be performed without raw fMRI; a placeholder task documents this limitation.  
- All statistical results are conditional on the validation gate passing; currently none are produced.  

--- 

## Future Directions (pending data)

When a compliant dataset is supplied (e.g., via authorized HCP access placed under `data/subjects.parquet` matching `contracts/dataset.schema.yaml`), the same command `python src/main.py` will run the full pipeline: extraction → graph metrics → PCA → partial correlations + Ridge CV with FDR → figures and results.
