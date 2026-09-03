# Implementation Plan: Quantifying the Impact of Code Authorship Diversity on Software Security

**Branch**: `PROJ-166-quantifying-the-impact-of-code-authorshi` | **Date**: 2026-06-25 | **Spec**: `specs/PROJ-166/spec.md`
**Input**: Feature specification from `specs/PROJ-166/spec.md`

## Summary

This project implements a statistical research pipeline to quantify the relationship between code authorship diversity (defined as **unique author count**) and software security vulnerabilities. The system ingests public GitHub repositories, matches them to NVD CVE records using substring matching, calculates authorship and code size metrics, and fits a multivariate Negative Binomial GLM. 

**Critical Constitutional Note**: The plan explicitly requires an amendment to the Project Constitution (Principle VI) to replace `git clone --depth=1` with `git clone --shallow-since=2015-01-01`. The current Constitution text is factually incompatible with FR-001 (retrieve commit history) and FR-003 (calculate unique authors). The pipeline will **BLOCK** execution until this amendment is ratified.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (for NVD/GitHub data handling), `statsmodels` (for Negative Binomial GLM), `pandas`, `numpy`, `scikit-learn` (for `OneHotEncoder` mapping to FR-004 `C(primary_language)`), `requests`, `pyyaml`, `scipy` (for ZINB comparison)  
**Storage**: Local file system (`data/` directory) for JSON/CSV artifacts; no external database required.  
**Testing**: `pytest` for unit tests; `jsonschema` for contract validation.  
**Target Platform**: Linux (GitHub Actions Free Tier: Multi-core CPU, 7GB RAM, 14GB Disk).  
**Project Type**: Data Science Research Pipeline / CLI  
**Performance Goals**: Process ≥500 repositories within 6 hours on CPU.  
**Constraints**: Memory usage <6GB; no synthetic data; strict checksum verification for NVD data.  
**Scale/Scope**: A substantial number of repositories; NVD CVE feed (historical).

> **Note on Data Strategy**: The NVD feed is large. The plan utilizes streaming or chunked processing where possible, or downloads the specific yearly JSON files required for the matched repositories to stay within available disk limits.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`. NVD data fetched from canonical source every run. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | PASS | All NVD and GitHub URLs verified. No synthetic data. Citations checked against primary sources. |
| **III. Data Hygiene** | PASS | NVD JSON files checksummed (`sha256`) and stored in `data/nvd/`. No in-place modifications; derivations are new files. PII scan enforced. |
| **IV. Single Source of Truth** | PASS | All statistics trace to `data/` artifacts. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | PASS | Artifacts carry content hashes. State file updated on changes. |
| **VI. Authorship Diversity Metric** | **BLOCKED (Amendment Required)** | **Conflict**: Constitution mandates `--depth=1`, which prevents `unique_authors` calculation for >90% of repos. **Resolution**: Plan requires a Constitutional Amendment to replace `--depth=1` with `--shallow-since=2015-01-01`. Until ratified, execution is blocked. The metric is defined as `unique_authors` (count), NOT a ratio. |
| **VII. Vulnerability Data Sourcing** | PASS | NVD JSON feed downloaded to `data/nvd/`, checksummed, and matched by substring URL. **Outcome**: `cve_count` (raw count) as per FR-004. `cve_density` is calculated **only** for descriptive reporting, never as a model input. Strict checksum verification acts as a **blocking gate**; if the checksum does not match the official NVD manifest, the pipeline aborts. |

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-166-quantifying-the-impact-of-code-authorshi/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-166-quantifying-the-impact-of-code-authorshi/
├── data/
│   ├── nvd/                 # Raw NVD JSON files + checksums
│   ├── repos/               # Cloned repos (temp) or metadata
│   └── processed/           # Merged datasets, model outputs
├── code/
│   ├── __init__.py
│   ├── config.py            # Paths, seeds, constants
│   ├── ingestion.py         # GitHub/NVD download logic
│   ├── metrics.py           # Author count, KLOC, entropy
│   ├── modeling.py          # GLM fitting, robustness checks
│   ├── reporting.py         # JSON/Report generation
│   └── main.py              # Orchestration script
├── tests/
│   ├── test_ingestion.py
│   ├── test_metrics.py
│   └── test_modeling.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure (Option 1) is selected. The pipeline is a linear research workflow (Ingest -> Process -> Model -> Report) best suited for a modular script-based approach in a single directory, avoiding the overhead of microservices for a batch research task.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Negative Binomial GLM** | Required by FR-004 to handle over-dispersed count data (vulnerabilities are rare events with high variance). | Poisson GLM would fail to model the variance correctly, leading to invalid p-values. |
| **Zero-Inflated NB (ZINB) Comparison** | Required to address the skewed/zero-inflated distribution of `author_count` and `cve_count` (FR-004 robustness). | Standard NB may not capture excess zeros. ZINB is a mandatory fallback if AIC/BIC improves significantly. |
| **Log(KLOC) as Covariate** | Required by FR-004 (Spec Amendment) to avoid bias in the size-CVE slope. | Using KLOC as an offset forces a fixed 1:1 relationship between size and CVEs, which is empirically false. |
| **Benjamini-Hochberg Correction** | Required by FR-006 to control False Discovery Rate across multiple robustness tests. | Uncorrected p-values would inflate Type I errors due to multiple comparisons. |
| **Ridge Regression Fallback** | Required if VIF > 5 (Collinearity between `author_count` and `log(kloc)`). | Simply reporting VIF leaves coefficients unstable. Ridge regression provides stable estimates via cross-validated penalty. |
| **Substring Matching** | Required to address construct validity threat of exact URL matching (NVD links often point to tags/issues). | Exact matching results in massive false negatives, biasing the outcome variable towards zero for mature projects. |
| **`--shallow-since` Clone** | Required by **FR-001/FR-003** to capture full author history. | `--depth=1` (Constitution VI literal) only captures the latest commit, making `unique_authors` calculation impossible for older repos. **Constitution must be amended** to allow this. |

## Data Availability & Integrity

*   **NVD Feed**: Verified as open and downloadable. The plan includes a checksum verification step (`sha256`) to ensure data integrity (Constitution Principle III).
*   **GitHub Repos**: Publicly accessible. No authentication required for read-only access to public repos.
*   **No Synthetic Data**: The plan strictly forbids synthetic data generation. If a repo cannot be cloned or matched, it is excluded and logged.

## Statistical Rigor & Assumptions

*   **Over-dispersion**: Negative Binomial is chosen specifically because vulnerability counts are typically over-dispersed (variance > mean), violating Poisson assumptions.
*   **Collinearity**: `log(kloc)` and `author_count` may be correlated. The model will report Variance Inflation Factors (VIF). **If VIF > 5, the plan will automatically switch to Ridge Penalized Negative Binomial regression** (using `glmnet` or `statsmodels` with penalty) with the penalty parameter selected via cross-validation. The Ridge coefficients will be reported as the primary result for that subsample.
*   **Causal Claims**: The study is **observational**. Claims will be framed as "associations" or "correlations," not causal effects.
*   **Power**: With a sufficiently large number of observations, the study has sufficient power to detect moderate effect sizes, provided the number of CVEs is not zero-inflated beyond the Negative Binomial's capacity.
*   **Distributional Assumptions**: A robustness check treating `author_count` as a categorical factor (binned) will be performed regardless of model convergence to test for skew/zero-inflation effects. **Additionally, a Zero-Inflated Negative Binomial (ZINB) model will be fitted. If ZINB AIC/BIC is significantly lower, ZINB results will be reported as the primary robustness finding.**
*   **Circularity Prevention**: The model formula **explicitly excludes `cve_density`**. The code validates that the outcome variable is strictly `cve_count` (integer) and never `cve_density`.
*   **Causal Assumption Justification**: `log(kloc)` is treated as a **confounder** (project size drives both author count and CVE count), not a mediator. The hypothesis is that diversity reduces CVEs *independently* of size. If `kloc` were a mediator, the estimate would represent only the direct effect. This distinction is explicitly reported.

## Bias Mitigation Strategy

*   **Matching Bias**: Substring matching may introduce bias if diverse projects have better documentation (more CVE matches). To mitigate:
    1.  A stratified random sample of matches will be manually verified to estimate the false-positive rate.
    2.  A sensitivity analysis will re-run the model excluding the top tier of projects with the most CVE matches. If the authorship effect disappears, the result is flagged as potentially driven by documentation bias.
*   **Definition Clarity**: 'Diversity' is defined as **Author Count (Breadth)** for the primary hypothesis. 'Evenness' (Shannon Entropy) is a secondary hypothesis. Contradictory results will be reported as evidence that Breadth and Evenness have different effects.

## Compute Feasibility (CPU-first)

*   **Cloning**: `git clone` is I/O bound but CPU light. Sequential processing ensures memory safety (<7GB RAM).
*   **Statistics**: `statsmodels` runs efficiently on CPU for N=500. No GPU required for GLM fitting.
*   **Data Processing**: Pandas operations on a 500-row dataset are instantaneous.
*   **Disk**: A large number of repos with substantial average storage per repository result in a significant total storage requirement. Fits within 14GB limit. NVD JSON files (streamed or partial) fit within remaining space.

## GPU Escape Hatch

*   **Not Required**: This project does not involve deep learning, transformers, or large-scale matrix factorization that requires a GPU. The "GPU escape hatch" is not needed for this specific methodology.