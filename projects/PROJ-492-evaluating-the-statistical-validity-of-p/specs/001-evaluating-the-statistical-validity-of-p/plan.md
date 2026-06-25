# Implementation Plan: Evaluating the Statistical Validity of Public A/B Test Summaries  

**Branch**: `001-eval-ab-test-validity` | **Date**: 2026-06-24 | **Spec**: [link]  
**Input**: Feature specification from `/specs/001-eval-ab-test-validity/spec.md`

## Summary
The project will deliver a reproducible, CPU‑only audit pipeline that (1) ingests a user‑provided list of URLs to public A/B test summaries, (2) extracts required metrics with explicit conversion rules, (3) reconstructs statistical tests (two‑proportion z/Fisher for binary outcomes, Welch’s t for continuous outcomes), (4) flags inconsistencies per **FR‑004** with justified thresholds and optional sensitivity analysis, (5) computes aggregate analyses (**FR‑005**) using hierarchical/cluster‑robust methods, (6) renders an HTML dashboard (**FR‑010**), (7) exports a Docker‑based reproducibility package (**FR‑006**), and (8) runs reliably on the default GitHub Actions runner (**FR‑009**).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `requests`, `beautifulsoup4`, `pandas`, `numpy`, `scipy>=1.14`, `statsmodels>=0.14`, `jinja2`, `plotly`, `pytest`, `jsonschema`, `psutil`, `playwright`, `docker` (for CI packaging)  
- **Storage**: CSV/JSON files under `data/` (raw URLs, extracted tables, synthetic validation set) and `outputs/` (audit JSON, dashboard HTML, manifest).  
- **Testing**: `pytest` + contract validation via `jsonschema` for **both** `audit_record.schema.yaml` **and** `extracted_summary.schema.yaml`.  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goals**: Process ≥ 100 summaries within the 6 h CI window, ≤ 7 GB RAM, ≤ 2 CPU cores  
- **Constraints**: CPU‑only, no GPU libraries or large‑model inference, satisfying the free‑tier CI constraints.  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | All scripts are deterministic; random seeds are pinned (`np.random.seed(42)`). Dockerfile reproduces the exact environment. |
| **II. Verified Accuracy** | No external citations beyond the verified datasets (none required for the core audit). |
| **III. Data Hygiene** | Raw URL list is checksum‑ed (`sha256`). Every transformation writes a new file; original CSV is never overwritten. |
| **IV. Single Source of Truth** | Every figure in the dashboard references a row in `outputs/audit_report.json`. |
| **V. Versioning Discipline** | Phase 0 computes SHA‑256 hashes for **all** output artifacts and writes them to `outputs/manifest.json`. The manifest is version‑controlled and used by downstream checks, satisfying the non‑negotiable requirement. |
| **VI. Statistical Consistency Verification** | All reconstructed statistics use SciPy and are cross‑checked with Statsmodels, meeting the non‑negotiable requirement. |
| **VII. Source Provenance & Transparency** | The extracted record stores `url`, `source_domain`, and retrieval timestamp; these fields are persisted in `data/extracted_summaries.csv` and referenced in any derived tables or visualizations. |

## Project Structure
```text
specs/001-eval-ab-test-validity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── audit_record.schema.yaml
    └── extracted_summary.schema.yaml

src/
├── audit/
│   ├── __init__.py
│   ├── cli.py               # entry point `python -m audit.run`
│   ├── ingest.py            # download & checksum URLs
│   ├── extract.py           # HTML parsing & field extraction
│   ├── reconstruct.py       # statistical reconstruction
│   ├── consistency.py       # flagging logic (FR‑004)
│   ├── aggregates.py        # FR‑005 calculations (hierarchical)
│   ├── dashboard.py         # HTML generation (FR‑010)
│   └── reproducibility.py   # Dockerfile writer, MD5 checks, manifest
├── utils/
│   ├── logging.py
│   └── schema.py
tests/
├── unit/
│   └── test_*.py
├── integration/
│   └── test_full_pipeline.py
└── contract/
    └── test_contracts.py
```

## Phase‑wise Plan & FR/SC Mapping
| Phase | Description | Key Tasks (FR) | Success Checks (SC) |
|-------|-------------|----------------|---------------------|
| **0. Versioning & Manifest** | Compute SHA‑256 for every output file (`outputs/*.json`, `*.csv`, `*.html`) and write `outputs/manifest.json`. Record artifact hashes in the project state. | FR‑009, FR‑006, **Principle V** | SC‑008, SC‑004, SC‑009 |
| **1. Data Ingestion** | Read CSV of URLs, download HTML, compute SHA‑256 checksums, log failures. | FR‑001, FR‑007 | SC‑005 |
| **2. Extraction** | Parse each HTML with BeautifulSoup, detect metric unit, and extract `variant_a_n`, `variant_b_n`, `effect_size`, `reported_p`/`confidence_interval`. **Conversion Rules**: <ul><li>**Lift %** → absolute difference = baseline × lift / 100 (baseline inferred from reported control conversion rate).</li><li>**Odds Ratio** / **Relative Risk** → convert to absolute risk difference using reported control conversion rate.</li><li>Unsupported or ambiguous units → flag as “missing metric”.</li></ul> Populate rows conforming to the `ABSummary` entity and **validate against `extracted_summary.schema.yaml`**. | FR‑002, FR‑007 | SC‑001 |
| **3. Synthetic Validation Set (FR‑008)** | Programmatically generate N = 200 synthetic A/B scenarios with ground‑truth statistics **and** realistic reporting quirks: <ul><li>Rounded p‑values to 2‑3 decimals.</li><li>Inequality bounds (`p < 0.001`).</li><li>Missing confidence intervals for a random subset.</li><li>Mixed effect‑size units (lift %, odds ratio, mean difference).</li><li>Intentional sample‑size mismatches up to 10 %.</li></ul> Store as `data/synthetic_validation.csv`. | FR‑008 | SC‑011 |
| **4. Reconstruction** | For each record, select test (binary → two‑proportion z or Fisher; continuous → Welch’s t). Compute reconstructed p‑value, effect size, and per‑variant sample sizes using **SciPy**. **Cross‑validate** p‑values with **Statsmodels** to avoid circular validation. | FR‑003 | SC‑003 |
| **5. Consistency Flagging** | Apply FR‑004 tolerance rules: <ul><li>abs(p‑diff) > 0.05</li><li>rel‑effect‑size > 5 %</li><li>rel‑sample‑size > 5 %</li><li>CI mismatch</li></ul> Record `diff_abs_p`, `diff_rel_effect`, `diff_rel_n`, `flag_inconsistent`, `category`, and notes. **Threshold Rationale**: 0.05 aligns with conventional α = 0.05; 5 % reflects typical reporting variability. **Sensitivity Analysis**: optional `--thresholds` CLI flag sweeps these values and reports impact on prevalence. | FR‑004 | SC‑002, SC‑011 |
| **6. Aggregate Analyses** | <ul><li>**Overall inconsistency proportion** `π̂` estimated via a **mixed‑effects logistic regression** with `source_domain` as a random effect (Statsmodels `MixedLM`).</li><li>Perform a **cluster‑robust binomial test** (source as clustering factor) against H₀: π = 0.05 using `statsmodels.stats.proportion.proportion_ztest` with robust variance.</li><li>Calculate **Wilson 95 % CI** (`stats.proportion_confint` method=`wilson`).</li><li>**Source‑wise rates**: for each source with ≥ 10 summaries, compute rate and a **Fisher’s exact test** comparing that subgroup’s inconsistency count to the overall count.</li><li>**Temporal trends**: month‑wise proportions; test using a **cluster‑robust proportion‑difference test** (source‑clustered) at α = 0.05.</li><li>**Power analysis** for the binomial test: given N audited summaries, compute achieved power to detect a deviation of 0.10 from the null (π = 0.05) using `statsmodels.stats.power.GofChisquarePower`. Report power; if < 0.80, emit a warning and suggest larger corpus.</li></ul> | FR‑005 | SC‑003 |
| **7. Dashboard Generation** | Use Plotly + Jinja2 to create `outputs/dashboard.html` with required charts and statistical test results. Validate with headless Chrome (Playwright) for console‑error‑free rendering (SC‑010). | FR‑010 | SC‑010 |
| **8. Reproducibility Package** | Bundle raw extracted CSV, synthetic CSV, analysis scripts, Dockerfile, JSON audit, HTML dashboard, and `manifest.json`. Compute MD5 checksums for each artifact; store in `outputs/checksums.txt`. | FR‑006, FR‑009 | SC‑004, SC‑009 |
| **9. CI Integration** | GitHub Actions workflow (`.github/workflows/ci.yml`) runs the full pipeline on a sample corpus, captures runtime (`time`), memory (`psutil`), and asserts limits (SC‑008) and parsing‑error rate (SC‑005). | FR‑009 | SC‑008, SC‑005 |

## Risk Mitigation
- **Missing Metrics**: Extraction logs “missing metric” and flags entry; such entries are excluded from aggregate calculations (edge case).  
- **Rounded / Inequality p‑values**: Parser interprets “p < 0.001” as upper bound 0.001; flag only if reconstructed > bound.  
- **Non‑binary Outcomes**: Test selector automatically switches to Welch’s t per FR‑003.  
- **Parsing Failures**: All HTTP errors and HTML parsing exceptions are caught; entry is recorded in `parsing_errors.log` and contributes to SC‑005.  
- **Threshold Sensitivity**: Optional `--thresholds` CLI flag runs a sweep; results are reported in the dashboard for transparency.  
- **Power Considerations**: If achieved power is <80 %, the pipeline emits a warning and recommends expanding the URL list.  

## Compute Feasibility
All libraries are CPU‑only and installable on the GitHub Actions free tier. The most intensive step (full extraction & reconstruction of ~100 summaries) comfortably fits within ≤ 7 GB RAM and ≤ 2 CPU cores. No GPU or large‑model inference is required.

---

