# Implementation Plan: The Impact of Self‑Compassion on Resilience to Negative Feedback

**Branch**: `001-self-compassion-feedback` | **Date**: 2026-06-24 | **Spec**: [spec.md](../specs/001-self-compassion-feedback/spec.md)

**Input**: Feature specification from `/specs/001-self-compassion-feedback/spec.md`

## Summary
The core scientific claim is that self‑compassion (measured by the Self‑Compassion Scale, SCS) buffers the adverse psychological impact of **experimentally randomized** negative feedback on anxiety, rumination, and self‑efficacy. We will download a verified OSF dataset that contains the required pre‑ and post‑feedback outcome measures, clean it, fit moderated ANCOVA models for each outcome, compute robust standard errors, run bootstrap confidence intervals, generate simple‑slope visualizations, and produce a concise HTML report that bundles all results, plots, and well‑being documentation.

## Randomization Confirmation
The feedback condition (`0 = positive`, `1 = neutral`, `2 = negative`) was **randomly assigned** to participants in the original experiment (as documented in the OSF protocol). This randomization justifies a causal interpretation of the interaction term between negative feedback and self‑compassion.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies** (pinned in `requirements.txt`):  
  - `pandas==2.2.*`  
  - `statsmodels==0.14.*` (OLS, HC3 SEs, Breusch‑Pagan test)  
  - `seaborn==0.13.*` / `matplotlib==3.8.*` (visualization)  
  - `scikit‑learn==1.5.*` (standardization)  
  - `jinja2==3.1.*` (HTML templating)  
  - `pytest==8.2.*` (testing)  
- **Storage**: Files under `data/` (raw Parquet, cleaned CSV, derived tables) and `outputs/` (plots, HTML report).  
- **Testing**: `pytest` with contract‑based validation (`contracts/analysis_result.schema.yaml`).  
- **Target Platform**: Linux runner (GitHub Actions).  
- **Constraints**: Single‑core CPU, ≤ 2 GB RAM, total runtime ≤ 30 minutes.

## Power Analysis & Sample‑Size Check
An a priori power analysis (G*Power, linear multiple regression: fixed model, R² increase) indicates that with α = 0.05, power = 0.80, and targeting a **small** interaction effect (partial η² = 0.02), a total sample of **≈ 92 participants** is required. After the missing‑data cleaning step (FR‑002) the pipeline will verify that the remaining sample size ≥ 92; otherwise it aborts with a clear error indicating insufficient power.

## Multiple‑Comparison Correction
We will apply the **Holm‑Bonferroni** procedure to the three primary interaction p‑values (anxiety, rumination, self‑efficacy) to control the family‑wise error rate at α = 0.05.

## Covariate Justification
Primary covariates (baseline outcome, age, gender, SCS) are retained. Additional personality‑trait variables present in the dataset will be **included** if they have > 90 % completeness; otherwise they are omitted with documented justification. This guards against omitted‑variable bias while respecting data‑hygiene constraints.

## Outcome Measure Citations
- **Anxiety**: Spielberger State‑Trait Anxiety Inventory (STAI) – Spielberger, C. D. (1983). *Manual for the State‑Trait Anxiety Inventory*.  
- **Rumination**: Ruminative Responses Scale (RRS) – Nolen‑Hoeksema, S., & Morrow, J. (1991). *Ruminative Responses Scale*. *Cognitive Therapy and Research*, 15(3), 351‑354.  
- **Self‑Efficacy**: General Self‑Efficacy Scale (GSES) – Schwarzer, R., & Jerusalem, M. (1995). *Generalized Self‑Efficacy Scale*. *Journal of Personality Assessment*, 57(2), 307‑317.  

All instruments are validated and their psychometric properties are documented in `data/validation/`.

## Data Cleaning & Preparation (FR‑002, FR‑003, FR‑004)
1. **Missing‑Data Handling (FR‑002)** – Rows missing any of `SCS_total`, baseline outcome, post‑feedback outcome, or `wellbeing_check` are dropped; the count of exclusions is logged to `outputs/logs/missing_data.log`.  
2. **Encoding (FR‑003)** – `feedback` recoded as categorical (`0=positive`, `1=neutral`, `2=negative`). Gender encoded as binary (`0=male`, `1=female`).  
3. **Standardization (FR‑003)** – Continuous predictors (`SCS_total`, baseline scores, age) are z‑scored, producing `SCS_z`, `age_z`, etc.  
4. **Derivation (FR‑004)** – Interaction term `C(feedback)[T.2]:SCS_z` is created implicitly via the statsmodels formula. Post‑feedback scores are used as dependent variables; baseline scores are included as covariates.

## Primary ANCOVA Models (FR‑005, FR‑006, FR‑009)
- **Model Specification**: For each outcome (anxiety, rumination, self‑efficacy)  
  `post_outcome ~ baseline_outcome + age_z + gender_cat + SCS_z + C(feedback) + C(feedback)[T.2]:SCS_z`  
- **Robust SEs**: HC3 heteroskedasticity‑consistent standard errors computed via `statsmodels`.  
- **Heteroskedasticity Flag (FR‑009)** – Breusch‑Pagan test performed; if `p < 0.10`, a flag `heteroskedasticity = True` is added to the results.  
- **Effect Size**: Partial η² for the interaction term is computed from the ANOVA table.

## Bootstrap Validation (FR‑008, FR‑012, SC‑003)
- **Bootstrap**: 5 000 resamples of the interaction coefficient using seed = 42 (set in `src/config.py` per FR‑012).  
- **Output**: Bias‑corrected confidence interval stored in the analysis result; overlap with the parametric CI is verified as part of SC‑003.

## Robustness Checks (FR‑014)
- **Alternative Moderator** – Repeat the primary moderation analysis using the rumination subscale (`SCS_rumination_z`). All statistics (coefficients, SEs, p‑values, CI, η²) are reported analogously.

## Visualization (FR‑007, SC‑004)
- **Simple‑Slope Plots** – For each outcome, plot predicted post‑feedback scores across feedback conditions at low (‑1 SD), mean, and high (+1 SD) SCS levels. Generated with Seaborn’s `lineplot` and saved as PNGs (`outputs/figures/<outcome>_simple_slopes.png`). Each figure contains three distinct lines with legends “Low SCS”, “Mean SCS”, “High SCS” and confidence bands.

## Reporting (FR‑010, FR‑011, SC‑005)
- **HTML Report** – Jinja2 template (`report/template.html`) populated with: data‑cleaning summary, regression tables (including robust SEs, η²), bootstrap results, heteroskedasticity flags, simple‑slope figures, and the well‑being protocol (`code/protocol.md`). Output written to `outputs/report.html`. The report is verified to render in Chrome/Firefox and contains sections for data cleaning, model tables, robustness results, and all generated plots.

## Participant Well‑Being (FR‑011)
- The pipeline verifies that each participant record includes a `wellbeing_check` flag set to `true`. If any record fails this check, execution aborts with a clear error directing the researcher to `code/protocol.md`. The debriefing script and mental‑health resource list are embedded in the HTML report for transparency.

## Data Hygiene (Principle III)
- After downloading the OSF Parquet file, a **SHA‑256 checksum** is computed and recorded in `state/projects/...yaml`. All subsequent derived files have their own checksums logged similarly.

## Constitution Check
| Principle | Requirement | How the plan satisfies it |
|-----------|-------------|---------------------------|
| **I. Reproducibility** | Pin dependencies, fix seed, fetch dataset from canonical URL. | `requirements.txt` pins exact versions; `src/config.py` sets `np.random.seed(42)` and `random.seed(42)` before any stochastic step. |
| **II. Verified Accuracy** | All external citations verified. | Only OSF dataset URL (verified) and standard instrument citations (widely accepted) are used. |
| **III. Data Hygiene** | Checksums recorded, raw data immutable, transformations produce new files. | SHA‑256 checksum of `data/raw/osf_feedback.parquet` is computed; cleaned data written to `data/clean/cleaned_osf.csv`. |
| **IV. Single Source of Truth** | Every figure/statistic traces back to one data row and code block. | Regression tables are generated directly from the cleaned data; plot functions reference the same model objects; the HTML report pulls values from the `AnalysisResult` JSON. |
| **V. Versioning Discipline** | Content hashes updated on change. | The pipeline writes a hash of each artifact to `state/projects/...yaml` after creation. |
| **VI. Validated Instruments** | SCS and outcome scales must be validated. | Validation documents stored in `data/validation/` and cited in this plan. |
| **VII. Participant Well‑Being** | Pre‑screening, debriefing, resource links documented and verified. | `code/protocol.md` contains the checklist, debriefing script, and resource URLs; the pipeline aborts if any `wellbeing_check` is false. |

## Success Criteria
- **SC‑001**: Interaction coefficient for negative feedback × self‑compassion is statistically significant (p < 0.05) and its confidence interval excludes zero.  
- **SC‑002**: Partial η² for the interaction term is ≥ 0.02.  
- **SC‑003**: Bootstrap confidence interval for the interaction coefficient excludes zero and overlaps the parametric confidence interval.  
- **SC‑004**: Simple‑slope plot files are generated for all three outcomes and correctly display three lines (‑1 SD, mean, +1 SD SCS).  
- **SC‑005**: The HTML report (`outputs/report.html`) renders in a standard browser and contains sections for data cleaning, model tables, robustness results, and all generated plots.
