# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/derived/auditory_trials.csv: header only, ZERO data rows — the analysis produced no rows
- data/derived/trial_data.csv: column(s) confidence_rating are EMPTY in every one of 150 rows — that measure was never recorded
- data/derived/visual_trials.csv: column(s) confidence_rating are EMPTY in every one of 150 rows — that measure was never recorded
- data/results/correlation_metrics.json: metric is null/NaN (d_prime) — not a real measurement

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 hollow-result signal(s) — the analysis ran but computed nothing: data/derived/auditory_trials.csv: header only, ZERO data rows — the analysis produced no rows; data/derived/trial_data.csv: column(s) confidence_rating are EMPTY in every one of 150 rows — that measure was never recorded; data/derived/visual_trials.csv: column(s) confidence_rating are EMPTY in every one of 150 rows — that measure was never recorded

## Failing / missing run-book commands

- (no per-command failures; the run produced no real data/figure artifacts — ensure scripts WRITE their declared outputs under data/ and figures/)

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `AppConfig` (in `code/config/env_config.py`) — accessed via method/attribute names this round: `get`

`AppConfig` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config/env_config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `AppConfig` across the codebase must stop raising `AttributeError`/`TypeError`.

`AppConfig.get` call sites (25):
- code/src/analysis/filter.py: return [row for row in trial_rows if row.get("stimulus_modality") == modality]
- code/src/analysis/diagnostics.py: base_dir = Path(config.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
- code/src/analysis/diagnostics.py: results_dir = Path(base_dir) / config.get("paths", {}).get("results", "data/results")
- code/src/analysis/diagnostics.py: derived_dir = Path(base_dir) / config.get("paths", {}).get("derived_data", "data/derived")
- code/src/analysis/diagnostics.py: residuals = regression_results.get("residuals", [])
- code/src/analysis/diagnostics.py: y_values = regression_results.get("y_values", [])
- code/src/analysis/diagnostics.py: "normality_passed": normality_result.get("is_normal", False),
- code/src/analysis/diagnostics.py: "homoscedasticity_passed": homoscedasticity_result.get("is_homoscedastic", False),
- code/src/analysis/diagnostics.py: "collinearity_flagged": vif_result.get("collinearity_flag", False),
- code/src/analysis/diagnostics.py: normality_result.get("is_normal", False) and
- code/src/analysis/diagnostics.py: homoscedasticity_result.get("is_homoscedastic", False) and
- code/src/analysis/diagnostics.py: not vif_result.get("collinearity_flag", False)
- code/src/analysis/diagnostics.py: logger.error(f"Diagnostics failed: {results.get('reason', 'Unknown error')}")
- code/src/report/generate.py: float(item.get("p_value", 0.0))
- code/models/data_models.py: modality_str = str(row.get('stimulus_modality', 'unknown')).lower()
- code/models/data_models.py: source_str = str(row.get('source_label', 'unknown')).lower()
- code/models/data_models.py: trial_id=str(row.get('trial_id', str(uuid.uuid4()))),
- code/models/data_models.py: participant_id=str(row.get('participant_id')),
- code/models/data_models.py: participant_response=str(row.get('participant_response', '')),
- code/models/data_models.py: confidence_rating=float(row.get('confidence_rating', 0.0)),
- code/models/data_models.py: reaction_time=float(row.get('reaction_time')) if row.get('reaction_time') is not None else None
- code/config/env_config.py: return self.get(key)
- code/config/env_config.py: return super().get(key, default)
- code/config/env_config.py: config.get("paths.base", "projects/PROJ-179-the-influence-of-metacognitive-awareness")
- code/config/env_config.py: current = current.get(part, default)
