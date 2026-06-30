# Implementation Plan: Reproduce & Validate EmbFilter

**Branch**: `682-reproduce-embfilter` | **Date**: 2024-05-21 | **Spec**: `specs/682-reproduce-embfilter/spec.md`
**Input**: Feature specification from `specs/682-reproduce-embfilter/spec.md`

## Summary
- **Reproduction Success (SC‑001)**: Measured by comparing the filtered Spearman score against the baseline and checking that the direction of improvement matches the paper’s claim (or that degradation is ≤ 2 %). **Addressed by SC-001**
- **Computational Feasibility (SC‑002)**: Ensured by sampling ≤ 100 examples, using a CPU‑compatible model that fits < 14 GB disk, and constraining runtime to ≤ 6 h on 2 CPU cores. **Addressed by SC-002**
- **Methodological Transparency (SC‑003)**: All hyper‑parameters (frequency threshold, dimensionality reduction) are logged; the report contains an explicit “Associational Analysis” statement; and a Methodology Enforcement step guarantees associational phrasing. **Addressed by SC-003**
- **Dimensionality Reduction Efficiency (SC‑004)**: The ratio of output to input embedding size is recorded; performance drop is reported and must be < 2 % to be considered negligible. **Addressed by SC-004**
- **Artifact Generation (SC‑005)**: The pipeline must produce non‑empty `.pt` embedding files and a JSON report (`report.json`) that conforms to the schema in `contracts/output-report.schema.yaml`. **Addressed by SC-005**

## Technical Context
- **Language/Version**: Python 3.9+  
- **Primary Dependencies**: `transformers` (CPU‑only), `torch` (CPU wheel), `datasets`, `numpy`, `scikit-learn`  
- **Storage**: Local ephemeral disk (≈ 14 GB limit)  
- **Testing**: `pytest` for script execution and schema validation  
- **Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7 GB RAM)  

**Requirement Mapping**  
- **Addressed by FR‑001** – All dependencies are CPU‑only; the pipeline forces `torch.device("cpu")` and disables any CUDA flags.  
- **Addressed by FR‑002** – The pipeline invokes `run4llama_echo.py` with the `--apply_embfilter` flag to perform the linear frequency‑based transformation.  
- **Addressed by FR‑003** – Evaluation script (`eval.py`) is run after filtering to compute downstream metrics.  
- **Addressed by FR‑004** – The wrapper writes `report.json` (and optional CSV) adhering to the output schema.  
- **Addressed by FR‑005** – `freq_threshold` and `dim_reduction` are recorded in the `parameters` section of the report, together with a brief rationale derived from the paper (Section 3.2).  
- **Addressed by FR‑006** – No quantization libraries (e.g., `bitsandbytes`) are installed; attempts to import them raise an error caught by the wrapper, causing an early abort with a clear message.  
- **Addressed by FR‑007** – The report template includes a mandatory “Associational Analysis” note; the linter enforces this.

## Methodology Enforcement
1. **Report Template** – A fixed Jinja2 template contains the exact phrasing: “This study is an *observational* (associational) analysis; results reflect correlations, not causation.”  
2. **Causal‑Verb Linter** – Implemented as a pre‑commit hook (`pre-commit run causal-verb-lint`) that scans **all** textual outputs (report JSON fields, console logs, generated markdown) for prohibited causal verbs (`cause`, `lead to`, `drive`). The CI job runs this hook automatically after the pipeline finishes. If any violation is detected, the CI step fails and the developer must edit the report/template.  
3. **Automated Parameter Logging** – All hyper‑parameters (`freq_threshold`, `dim_reduction`, `max_samples`, etc.) are written to the `parameters` field of `report.json`.  
4. **Multiple‑Comparison Policy** – If more than one downstream task is evaluated, **Bonferroni correction** is applied to the p‑values; otherwise a warning is logged that results are presented uncorrected but with a clear note. This policy is documented here and enforced in the evaluation script.  

## Constitution Check
1. **Reproducibility** – Exact vendored scripts are executed with deterministic seeds; logs capture full command‑line arguments.  
2. **Transparency** – Hyper‑parameter values and the associational framing statement are logged; the Methodology Enforcement steps (above) guarantee they appear in the final report.  
3. **Feasibility** – CPU‑only dependencies, data sampling, and model size checks keep resource usage within the free‑tier limits.  
4. **Scientific Rigor** – Performance is compared against the paper’s baseline using Spearman correlation; multiple‑comparison correction is applied when needed; collinearity is acknowledged in the discussion section of the report. **Addressed by SC-003**  

## Project Structure

### Documentation (this feature)

```text
specs/682-reproduce-embfilter/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── output-report.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── embfilter_repro/
│   ├── __init__.py
│   ├── run_pipeline.py      # Wrapper to orchestrate execution
│   └── utils.py             # Logging and validation helpers
├── data/                    # Ephemeral data storage (sampled)
└── outputs/                 # Artifacts (.pt, .json)
```

**Structure Decision** – A thin wrapper isolates the vendored `EmbFilter` scripts, ensuring clean CPU‑only invocation and centralized logging.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | The project scope is strictly limited to running existing code and validating outputs. No complex architectural patterns are introduced. | N/A |