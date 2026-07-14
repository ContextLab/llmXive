# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…"""Synthetic Data Generator for Developmen…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…> Dict[str, Any]:     """Generate a single synthetic respondent record for te…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…-> pd.DataFrame:     """Generate the full synthetic dataset."""     records…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…ation def main():     """Generate and save synthetic data (FALLBACK ONLY)."""…”
- code/01_download_data.py: synthetic/fake INPUT data not authorized by the spec — “…APIs, with a fallback to synthetic data generation if real sourc…”
- code/01_download_data.py: synthetic/fake INPUT data not authorized by the spec — “…unavailable. Fallback to synthetic data will be used.")…”
- code/01_download_data.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic data as a fallback when…”
- code/01_download_data.py: synthetic/fake INPUT data not authorized by the spec — “…gs:         n: Number of synthetic records to generate         seed…”

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/05_generate_report.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 29 fabricated/simulated-result signal(s) — results are not real measurements: code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…"""Synthetic Data Generator for Developmen…”; code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…> Dict[str, Any]:     """Generate a single synthetic respondent record for te…”; code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…-> pd.DataFrame:     """Generate the full synthetic dataset."""     records…”; 6 command(s) failed: python code/01_download_data.py --synthetic (rc=1); python code/02_clean_data.py (rc=1); python code/03_engineer_features.py (rc=1); 1 declared deliverable(s) absent: data/processed/cleaned_data.csv

## Failing / missing run-book commands

- python code/01_download_data.py --synthetic -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/01_download_data.py", line 336, in <module>
    @log_operation("data_acquisition_main")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'LogEntry' object is not callable
- python code/02_clean_data.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/02_clean_data.py", line 327, in <module>
    @log_operation("data_cleaning_main")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'LogEntry' object is not callable
- python code/03_engineer_features.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/03_engineer_features.py", line 41, in <module>
    @log_operation("load_config")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'LogEntry' object is not callable
- python code/04_model_analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/04_model_analysis.py", line 198, in <module>
    @log_operation("model_analysis_main")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'LogEntry' object is not callable
- python code/05_generate_report.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/05_generate_report.py", line 51, in <module>
    PROJECT_ROOT = Path(get_config("project_root", "."))
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_config() takes 0 positional arguments but 2 were given
- python code/02_clean_data.py --input data/raw/survey_data.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/02_clean_data.py", line 327, in <module>
    @log_operation("data_cleaning_main")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'LogEntry' object is not callable

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_config` — defined in `code/config.py`; called 5 way(s):

- code/03_engineer_features.py: return get_config()
- code/06_finalize_results.py: config = get_config()
- code/05_generate_report.py: PROJECT_ROOT = Path(get_config("project_root", "."))
- code/validate_quickstart.py: config = get_config()
- code/04_model_analysis.py: config = get_config()

Make `get_config` in `code/config.py` accept ALL of the above.

### `update_log_section` — defined in `code/02_clean_data.py`; called 13 way(s):

- code/02_clean_data.py: update_log_section("data_cleaning", {"status": "started", "timestamp": datetime.utcnow().isoformat()})
- code/02_clean_data.py: update_log_section("data_cleaning", {
- code/02_clean_data.py: update_log_section("data_cleaning", {"status": "failed", "error": "Validation failed"})
- code/02_clean_data.py: update_log_section("data_cleaning", {"status": "failed", "error": str(e)})
- code/03_engineer_features.py: update_log_section("feature_engineering", {"status": "failed", "error": str(e)})
- code/logging_config.py: - update_log_section("name", {"key": "value"})
- code/logging_config.py: - update_log_section("name", status="failed", error="msg")
- code/05_generate_report.py: update_log_section("report_generation", {"status": "failed", "error": str(e)})
- code/05_generate_report.py: update_log_section("report_generation", {"status": "completed", "output": str(pdf_path)})
- code/00_generate_synthetic_data.py: update_log_section("data_source_metadata", {"synthetic_fallback": {"status": "used", "reason": "Real data sources unavailable"}})
- code/01_download_data.py: update_log_section("data_acquisition", {"status": "started", "source": "attempting_real"})
- code/01_download_data.py: update_log_section(
- code/01_download_data.py: update_log_section("data_acquisition", {"status": "completed", "source": source_used})
- code/01_download_data.py: update_log_section("data_acquisition", {"status": "validation_failed", "missing_variables": missing})
- code/04_model_analysis.py: update_log_section("model_analysis", {"status": "started", "timestamp": datetime.utcnow().isoformat()})
- code/04_model_analysis.py: update_log_section("model_analysis", log_entry)
- code/04_model_analysis.py: update_log_section("model_analysis", {"status": "failed", "error": error_msg})

Make `update_log_section` in `code/02_clean_data.py` accept ALL of the above.

### class `Config` (in `code/02_clean_data.py`) — accessed via method/attribute names this round: `get`

`Config` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/02_clean_data.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `Config` across the codebase must stop raising `AttributeError`/`TypeError`.

`Config.get` call sites (25):
- code/code_00_generate_synthetic_data.py: random.seed(config.get("random_seed", 42))
- code/code_00_generate_synthetic_data.py: n = config.get("n_respondents", 1000)
- code/config.py: return self.get(key)
- code/config.py: return [(k, self.get(k)) for k in self.keys()]
- code/03_engineer_features.py: input_path = Path(config.get("processed_data_path", "data/processed")) / "cleaned_data.csv"
- code/03_engineer_features.py: "cronbach_alpha": metrics.get("cronbach_alpha"),
- code/03_engineer_features.py: "convergent_validity_status": "passed" if metrics.get("convergent_validity", {}).get("passed", False) else "skipped",
- code/03_engineer_features.py: "factors_retained": metrics.get("efa", {}).get("factors_retained"),
- code/03_engineer_features.py: "rotation": metrics.get("efa", {}).get("rotation"),
- code/03_engineer_features.py: "extraction": metrics.get("efa", {}).get("extraction")
- code/03_engineer_features.py: log_path = Path(config.get("project_root", ".")) / "modeling_log.yaml"
- code/03_engineer_features.py: output_dir = Path(config.get("processed_data_path", "data/processed"))
- code/03_engineer_features.py: results_dir = Path(config.get("results_path", "results"))
- code/logging_config.py: self.name = args[0] if args else kwargs.get("name", "reproducibility")
- code/logging_config.py: op = args[0] if args else kwargs.get("operation", "")
- code/06_finalize_results.py: "random_seed": config.get("random_seed"),
- code/06_finalize_results.py: "data_source": config.get("data_source", "unknown"),
- code/06_finalize_results.py: "seed_value": config.get("random_seed"),
- code/06_finalize_results.py: set_random_seed(config.get("random_seed", 42))
- code/06_finalize_results.py: project_root = Path(config.get("project_root", "."))
- code/05_generate_report.py: reg_data = results.get("regression", {})
- code/05_generate_report.py: coeffs = reg_data.get("coefficients", [])
- code/05_generate_report.py: var_name = row.get('variable', 'Unknown')
- code/05_generate_report.py: coef = row.get('coef', 0)
- code/05_generate_report.py: std_err = row.get('std_err', 0)

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `engineered_data.csv`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[results_dir]`
- PRODUCER(s) to edit: `code/03_engineer_features.py`, `code/06_finalize_results.py`, `code/04_model_analysis.py`
- CONSUMER(s) that read it: `code/03_engineer_features.py`, `code/06_finalize_results.py`, `code/05_generate_report.py`, `code/validate_quickstart.py`, `code/04_model_analysis.py`
  → Edit the producer so every required name [results_dir] is in `engineered_data.csv`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).

### `data/processed/cleaned_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/02_clean_data.py`, `code/03_engineer_features.py`, `code/06_finalize_results.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/cleaned_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/02_clean_data.py`, `code/03_engineer_features.py`, `code/06_finalize_results.py`, `code/05_generate_report.py`, `code/validate_quickstart.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/cleaned_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/02_clean_data.py`, `code/03_engineer_features.py`, `code/06_finalize_results.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/cleaned_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/02_clean_data.py`, `code/03_engineer_features.py`, `code/06_finalize_results.py`, `code/05_generate_report.py`, `code/validate_quickstart.py`.
