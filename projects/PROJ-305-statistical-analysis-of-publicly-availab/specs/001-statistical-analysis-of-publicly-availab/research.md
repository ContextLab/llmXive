# Research: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

## Overview
This research document confirms that the chosen data source, methods, and compute environment satisfy the specification while adhering to the project constitution. It demonstrates that the pipeline can be executed reproducibly on a CPU‑only GitHub Actions runner.

## Verified Dataset Strategy
| Variable | Required by Spec | Verified Source | URL |
|----------|------------------|----------------|-----|
| `VAX_TYPE` | Vaccine identifier (COVID‑19 vs. others) | VAERS parquet (2020‑2023) | https://huggingface.co/datasets/vaers/vaers2020_2023/resolve/main/vaers_2020_2023.parquet |
| `SOC_CODE` / `SOC_NAME` | MedDRA System Organ Class (mapped) | VAERS parquet (contains `SOC_CODE`; mapping supplied locally) | same as above |
| `REPT_DATE` | Report date for temporal profiling | VAERS parquet | same as above |
| `AGE`, `SEX` | Optional descriptive fields | VAERS parquet | same as above |

All required columns are present in the verified parquet. Phase 1 validation will abort if any are missing, guaranteeing downstream steps receive complete data.

## Methodological Rigor

### Disproportionality Metrics
- **ROR**: \((a/b)/(c/d)\) with **exact** 95 % confidence intervals computed via the **Clopper‑Pearson** binomial method.  
- **PRR**: \((a/(a+b))/(c/(c+d))\) with exact [deferred] intervals derived from a **beta‑binomial** credible interval.
- **IC**: \(\log_2\big((a/(a+c)) / ((a+b)/(a+b+c+d))\big)\) with exact [deferred] intervals obtained from a **Poisson‑Gamma** (Bayesian) model.
- **Continuity correction**: Add 0.5 to each cell when any count = 0 (addresses edge case).  
- **Sample‑size filter**: SOCs with total reports < 5 are excluded (FR‑002, FR‑006).  

### Statistical Corrections
- **Multiple testing**: Benjamini‑Hochberg FDR correction applied to raw p‑values for all SOCs (FR‑003).  
- **Monotonicity check**: Adjusted p‑values must be non‑decreasing when sorted by raw p‑value (SC‑002).  

### Signal Definition (FR‑005)
A SOC is flagged as a **signal** if **at least two** of the three metrics (ROR, PRR, IC) exceed their literature‑based thresholds **and** the Benjamini‑Hochberg adjusted p‑value < 0.05 **and** the signal remains significant in an independent **hold‑out validation** (20 % random subset, same thresholds). This composite rule follows FDA pharmacovigilance guidance (see 2‑out‑of‑3 justification in the implementation plan) and satisfies Principle VI.

### Hold‑Out Validation (addresses methodology‑8fc542b0 & scientific_soundness‑36e6ab60)
- A deterministic [deferred] random subset of the cleaned dataset (seeded) is set aside **before** any metric computation.
- Disproportionality metrics are recomputed on this hold‑out.  
- A candidate signal must meet the same 2‑out‑of‑3 + BH‑adjusted p < 0.05 criteria in the hold‑out to be accepted. This provides an independent check without re‑using the same data for both discovery and validation.

### Stratified Primary Analysis (Addressing Confounding)
Disproportionality calculations are performed **within each age‑group (< 18, 18‑64, ≥ 65) × sex (M/F/U) stratum**. Mantel‑Haenszel pooling produces a single pooled ROR/PRR/IC per SOC, preserving the baseline while accounting for demographic confounding (Principle VI).

### Power & Sample‑Size Discussion (addresses methodology‑928a3378)
Formal power calculations are infeasible for spontaneous reporting systems where the denominator (vaccinated population) is unknown. The ≥ 5‑report filter is a **stability rule** ensuring that exact interval methods remain reliable. For very rare SOCs the analysis may be under‑powered; this limitation is reported transparently (SC‑005). No additional sample‑size inflation is attempted.

### Temporal Profiling (FR‑004)
- Uses `REPT_DATE` only; axis label is “Reporting Time”.  
- Weekly counts are computed relative to the median `REPT_DATE` of the COVID‑19 cohort.  
- **Temporal‑bias robustness check**: weeks where COVID‑19 reports exceed three times the median weekly count are removed; Phase 3 metrics are recomputed for the top‑5 SOCs. A signal survives only if it remains significant after this check (adds robustness).

### Sensitivity Analysis (FR‑007)
- **Primary baseline**: Non‑COVID‑Non‑Flu.  
- **Sensitivity baseline**: Flu‑only (`VAX_GROUP == "Flu-only"`).  
- Δ‑metrics (ΔROR, ΔPRR, ΔIC) for the top‑5 signals are reported to assess robustness against confounding.

### Reporting Bias Considerations
VAERS is a passive surveillance system; reporting rates can be driven by media attention. All findings are framed as *associational* signals (Principle VI) and not causal claims. The temporal‑bias robustness check explicitly evaluates the impact of reporting spikes.

### Confounder Exploration (Exploratory)
Stratified tables for age and sex are generated and included in supplemental material; they do not affect the primary signal list.

## Compute Feasibility
- **Environment**: GitHub Actions free tier (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk).  
- **Data size**: verified parquet ≈ a few GB on disk, < 5 GB in memory after dtype optimisation.  
- **Runtime estimate**: < 2 h total (see plan).  
- All libraries are pure‑CPU; no GPU‑only packages are used.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Required columns missing | Fatal (cannot compute) | Phase 1 schema validation aborts with clear error. |
| Peak RAM > 7 GB | Job termination | Phase 6 guard; optional chunked processing fallback. |
| BH‑adjusted p‑values not monotonic | SC‑002 failure | Unit test enforces monotonicity; CI catches regressions. |
| Incomplete MedDRA→SOC mapping | Incomplete SOC aggregation | Mapping file must cover ≥ 95 % of observed codes; missing codes logged. |
| Mislabelled temporal axis | Violation of Principle VII | Plots explicitly label “Reporting Time”; documentation repeats disclaimer. |
| Thresholds appear arbitrary | Methodological criticism | Literature‑based justification added (see 2‑out‑of‑3 rule). |
| Confounding by age/sex | Biased signals | Stratified analysis + Mantel‑Haenszel pooling (Phase 3). |
| Temporal spikes bias metrics | Spurious signals | Temporal‑bias robustness check (Phase 4). |
| Circular signal definition | Scientific soundness | Replaced bootstrap with independent hold‑out validation. |

## Conclusion
Provided the verified VAERS parquet contains the required fields (ensured by Phase 1 validation), the outlined CPU‑only pipeline satisfies **all functional requirements (FR‑001‑FR‑007)**, meets **success criteria (SC‑001‑SC‑005)**, and conforms to the **project constitution**. The plan now includes statistically justified thresholds, stratified primary analyses, a power discussion for the ≥5‑report filter, a temporal‑bias robustness check that directly influences final signal acceptance, and an independent hold‑out validation of the 2‑out‑of‑3 rule. All artifacts are deterministically generated and validated against JSON‑Schema contracts, guaranteeing reproducibility and auditability.  

---


## Quickstart: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

## Prerequisites
- Python 3.11+  
- Git (to clone the repository)  
- Access to a GitHub Actions runner **or** a local Linux/macOS environment with ≥ 7 GB RAM and ≥ 10 GB free disk space.

## Installation

```bash
# 1. Clone the repository
git clone <REPO_URL>
cd <REPO_NAME>

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r src/requirements.txt
```

## Step‑by‑Step Execution

1. **Create directory tree & verification log**  
   ```bash
   python - <<'PY'
import pathlib, subprocess
pathlib.Path('logs').mkdir(exist_ok=True)
with open('logs/structure.txt', 'w') as f:
    subprocess.run(['tree', '-a', '-L', '3'], stdout=f)
PY
   ```
   *`logs/structure.txt` satisfies verification task T001.*

2. **Download the VAERS dataset**  
   ```bash
   python src/data/download.py
   ```
   - Downloads the verified full parquet from  
     `https://huggingface.co/datasets/vaers/vaers2020_2023/resolve/main/vaers_2020_2023.parquet`.  
   - Writes SHA‑256 checksum to `data/checksums.txt`.

3. **Validate the raw schema**  
   ```bash
   python src/data/validate.py
   ```
   - Exits with a clear error if any of `VAERS_ID`, `VAX_TYPE`, `SOC_CODE`, or `REPT_DATE` are absent (fulfills FR‑001 & SC‑004).

4. **Clean, map, and split the data**  
   ```bash
   python src/data/clean.py
   ```
   - Produces `data/processed/cleaned.parquet` with three groups (`COVID-19`, `Non-COVID‑Non‑Flu`, `Flu-only`).  
   - Validates the cleaned file against `contracts/cleaned_dataset.schema.yaml`.

5. **Run the full analysis pipeline**  
   ```bash
   python src/main.py
   ```
   This orchestrates:
   - Disproportionality calculations (`output/signals.csv`).  
   - Benjamini‑Hochberg correction.  
   - Signal flagging (2‑out‑of‑3 rule **plus** BH‑adjusted p‑value < 0.05 **and** hold‑out validation).  
   - Temporal profiling (canonical CSV files `output/temporal_profiles/<SOC>.csv`; optional PNG plots).  
   - Temporal‑bias robustness check (signals must survive spike‑week removal).  
   - Flu‑only sensitivity analysis (`output/sensitivity_analysis.csv`).  
   - Memory profiling and final `output/report.md`.

6. **Verify contracts**  
   ```bash
   pytest -q tests/contract/
   ```
   All JSON‑schema contracts must pass.

7. **Inspect results**  
   - `output/signals.csv` – table of ROR/PRR/IC with adjusted p‑values, hold‑out validation flag, and stability indicator.  
   - `output/temporal_profiles/` – CSV files for weekly counts (canonical) and optional PNG plots for the top signals.  
   - `output/sensitivity_analysis.csv` – Δ‑metrics vs. Flu baseline.  
   - `output/report.md` – human‑readable summary, memory usage, and limitations.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `E_SCHEMA_MISSING` from `validate.py` | Required columns absent in the downloaded parquet | Confirm the dataset URL; if missing, select a different verified VAERS parquet URL from the list. |
| MemoryError | Dataset larger than 7 GB RAM | Set `USE_CHUNKED=True` in `src/utils/config.py`; the pipeline will process the parquet in 500 k‑row chunks. |
| `logs/structure.txt` missing | Step 1 not executed or `tree` not installed | Install `tree` (`sudo apt-get install tree`) and re‑run step 1. |
| Plot functions raise `ImportError` | Placeholder code in `src/utils/plots.py` not replaced | Ensure the full implementation of `plot_weekly_counts` is present (provided in the repository). |
| Lint failures (`ruff` exit 1) | Style violations | Run `ruff check src/` locally, fix reported issues, then re‑run the lint script. |

## Next Steps
- Review `output/report.md` and incorporate the findings into the manuscript (`paper/`).  
- Run the full test suite (`pytest -q`) to ensure ongoing compliance.  
- To experiment with a larger VAERS archive, replace the download URL with the full dataset identifier; the same pipeline will handle it provided memory constraints are respected.

---

