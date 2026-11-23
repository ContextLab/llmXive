# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/analysis/exploratory.py`
- `python code/download/knot_info_loader.py`
- `python code/main.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/main.py; python code/download/knot_info_loader.py; 1 command(s) failed: python code/analysis/exploratory.py (rc=1); 3 declared deliverable(s) absent: data/checksums.csv; data/processed/knot_filtered.csv; data/raw/knot_atlas_raw.json

## Failing / missing run-book commands

- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/main.py': [Errno 2] No such file or directory
- python code/download/knot_info_loader.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/download/knot_info_loader.py': [Errno 2] No such file or directory
- python code/analysis/exploratory.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis/exploratory.py", line 115, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis/exploratory.py", line 110, in main
    generate_exploratory_plots(plot_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis/exploratory.py", line 97, in generate_exploratory_plots
    df = load_cleaned_knots()
         ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis/exploratory.py", line 48, in load_cleaned_knots
    raise FileNotFoundError(
FileNotFoundError: Cleaned knot data not found at 'data/processed/knots_cleaned.csv'.

## Declared deliverables still missing

- data/checksums.csv
- data/processed/knot_filtered.csv
- data/raw/knot_atlas_raw.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `database-knotinfo` to the project's `requirements.txt` and `pip install database-knotinfo`.
- **Verified**: this loads **12967** real records with fields: name, name_anon, category, category_anon, alternating, alternating_anon, name_rank, name_rank_anon, dt_name, dt_name_anon, dt_rank, dt_rank_anon, dt_notation, dt_notation_anon, classical_conway_name, classical_conway_name_anon, conway_notation, conway_notation_anon, two_bridge_notation, two_bridge_notation_anon, fibered, fibered_anon, gauss_notation, gauss_notation_anon, enhanced_gauss_notation, enhanced_gauss_notation_anon, pd_notation, pd_notation_anon, crossing_number, crossing_number_anon, tetrahedral_census_name, tetrahedral_census_name_anon, unknotting_number, unknotting_number_anon, three_genus, three_genus_anon, crosscap_number, crosscap_number_anon, bridge_index, bridge_index_anon, braid_index, braid_index_anon, braid_length, braid_length_anon, braid_notation, braid_notation_anon, signature, signature_anon, nakanishi_index, nakanishi_index_anon, super_bridge_index, super_bridge_index_anon, thurston_bennequin_number, thurston_bennequin_number_anon, arc_index, arc_index_anon, polygon_index, polygon_index_anon, tunnel_number, tunnel_number_anon, morse_novikov_number, morse_novikov_number_anon, alexander_polynomial, alexander_polynomial_anon, alexander_polynomial_vector, alexander_polynomial_vector_anon, jones_polynomial, jones_polynomial_anon, jones_polynomial_vector, jones_polynomial_vector_anon, conway_polynomial, conway_polynomial_anon, conway_polynomial_vector, conway_polynomial_vector_anon, kauffman_polynomial, kauffman_polynomial_anon, kauffman_polynomial_vector, kauffman_polynomial_vector_anon, a_polynomial, a_polynomial_anon, smooth_four_genus, smooth_four_genus_anon, topological_four_genus, topological_four_genus_anon, smooth_4d_crosscap_number, smooth_4d_crosscap_number_anon, topological_4d_crosscap_number, topological_4d_crosscap_number_anon, smooth_concordance_genus, smooth_concordance_genus_anon, topological_concordance_genus, topological_concordance_genus_anon, smooth_concordance_crosscap_number, smooth_concordance_crosscap_number_anon, topological_concordance_crosscap_number, topological_concordance_crosscap_number_anon, algebraic_concordance_order, algebraic_concordance_order_anon, smooth_concordance_order, smooth_concordance_order_anon, topological_concordance_order, topological_concordance_order_anon, ribbon, ribbon_anon, determinant, determinant_anon, seifert_matrix, seifert_matrix_anon, rasmussen_invariant, rasmussen_invariant_anon, ozsvath_szabo_tau_invariant, ozsvath_szabo_tau_invariant_anon, volume, volume_anon, maximum_cusp_volume, maximum_cusp_volume_anon, longitude_translation, longitude_translation_anon, meridian_translation, meridian_translation_anon, longitude_length, longitude_length_anon, meridian_length, meridian_length_anon, other_short_geodesics, other_short_geodesics_anon, symmetry_type, symmetry_type_anon, full_symmetry_group, full_symmetry_group_anon, chern_simons_invariant, chern_simons_invariant_anon, volume_imaginary_part, volume_imaginary_part_anon, arf_invariant, arf_invariant_anon, turaev_genus, turaev_genus_anon, signature_function, signature_function_anon, monodromy, monodromy_anon, small_large, small_large_anon, positive_braid, positive_braid_anon, positive, positive_anon, strongly_quasipositive, strongly_quasipositive_anon, quasipositive, quasipositive_anon, positive_braid_notation, positive_braid_notation_anon, positive_pd_notation, positive_pd_notation_anon, strongly_quasipositive_braid_notation, strongly_quasipositive_braid_notation_anon, quasipositive_braid_notation, quasipositive_braid_notation_anon, fd_clasp_number, fd_clasp_number_anon, width, width_anon, torsion_numbers, torsion_numbers_anon, td_clasp_number, td_clasp_number_anon, l_space, l_space_anon, nu, nu_anon, epsilon, epsilon_anon, quasi_alternating, quasi_alternating_anon, almost_alternating, almost_alternating_anon, adequate, adequate_anon, montesinos_notation, montesinos_notation_anon, boundary_slopes, boundary_slopes_anon, pretzel_notation, pretzel_notation_anon, double_slice_genus, double_slice_genus_anon, unknotting_number_algebraic, unknotting_number_algebraic_anon, khovanov_unreduced_integral_polynomial, khovanov_unreduced_integral_polynomial_anon, khovanov_unreduced_integral_vector, khovanov_unreduced_integral_vector_anon, khovanov_reduced_integral_polynomial, khovanov_reduced_integral_polynomial_anon, khovanov_reduced_integral_vector, khovanov_reduced_integral_vector_anon, khovanov_reduced_rational_polynomial, khovanov_reduced_rational_polynomial_anon, khovanov_reduced_rational_vector, khovanov_reduced_rational_vector_anon, khovanov_reduced_mod2_polynomial, khovanov_reduced_mod2_polynomial_anon, khovanov_reduced_mod2_vector, khovanov_reduced_mod2_vector_anon, khovanov_odd_integral_polynomial, khovanov_odd_integral_polynomial_anon, khovanov_odd_integral_vector, khovanov_odd_integral_vector_anon, khovanov_odd_mod2_polynomial, khovanov_odd_mod2_polynomial_anon, khovanov_odd_mod2_vector, khovanov_odd_mod2_vector_anon, khovanov_odd_rational_polynomial, khovanov_odd_rational_polynomial_anon, khovanov_odd_rational_vector, khovanov_odd_rational_vector_anon, hfk_polynomial, hfk_polynomial_anon, hfk_polynomial_vector, hfk_polynomial_vector_anon, mosaic_tile_number, mosaic_tile_number_anon, ropelength, ropelength_anon, homfly_polynomial, homfly_polynomial_anon, homfly_polynomial_vector, homfly_polynomial_vector_anon, grid_notation, grid_notation_anon, almost_strongly_qp, almost_strongly_qp_anon, almost_strongly_qp_braid, almost_strongly_qp_braid_anon, ribbon_number, ribbon_number_anon, geometric_type, geometric_type_anon, cosmetic_crossing, cosmetic_crossing_anon, q_polynomial, q_polynomial_anon, minkowski_units, minkowski_units_anon.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import database_knotinfo as dk

data = dk.link_list()
records = len(data)
if records == 0:
    raise ValueError("No records loaded")
print(f"RECORDS={records}")
print("FIELDS=" + ",".join(data[0].keys()))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_logger` — defined in `code/reproducibility/logs.py`; called 25 way(s):

- code/reproducibility/derivation_validator.py: get_logger().log(
- code/reproducibility/derivation_validator.py: get_logger().log("derivation_notes_all_sections_present", path=str(default_path))
- code/reproducibility/derivation_validator.py: get_logger().log("derivation_validator_error", error=str(exc))
- code/reproducibility/quickstart_validator.py: ``get_logger('quickstart_validator')`` which failed because ``get_logger`` did not
- code/reproducibility/quickstart_validator.py: self.logger = get_logger("quickstart_validator")
- code/reproducibility/operation_logs_generator.py: logger = get_logger()
- code/reproducibility/logs.py: return get_logger().log(op, **kwargs)
- code/reproducibility/run_checksums.py: logger = get_logger()
- code/reproducibility/citation_validator.py: logger = get_logger()
- code/reproducibility/tie_breaking_validator.py: logger = get_logger(__name__)
- code/reproducibility/linting_report.py: logger = get_logger("linting")
- code/reproducibility/generate_derivation_notes.py: get_logger().log("derivation_notes_generated", path=str(output_path))
- code/analysis/regression.py: logger = get_logger(__name__)
- code/analysis/coverage_reporting.py: logger = get_logger(__name__)
- code/analysis/group_comparison.py: logger = get_logger(__name__)
- code/analysis/correlation.py: logger = get_logger(__name__)
- code/analysis/model_reporting.py: logger = get_logger(__name__)
- code/analysis/validation_reporting.py: logger = get_logger(__name__)
- code/analysis/data_quality.py: logger = get_logger("data_quality")
- code/analysis/_utils.py: logger = get_logger()
- code/analysis/residual_analysis.py: logger = get_logger(__name__)
- code/analysis/dataset_counts.py: logger = get_logger()
- code/analysis/invariant_coverage.py: logger = get_logger(__name__)
- code/analysis/plotting.py: logger = get_logger(__name__)
- code/analysis/oeis_validation.py: self.logger_instance = get_logger() if logger is None else logger

Make `get_logger` in `code/reproducibility/logs.py` accept ALL of the above.

### `log_operation` — defined in `code/reproducibility/logs.py`; called 25 way(s):

- code/reproducibility/derivation_validator.py: @log_operation
- code/reproducibility/logs.py: """Dual-purpose: a decorator (@log_operation) OR a direct logging call.
- code/reproducibility/run_checksums.py: log_operation(
- code/reproducibility/citation_validator.py: log_operation(
- code/reproducibility/citation_validator.py: log_operation(operation="citation_validator_start", logger=logger)
- code/reproducibility/citation_validator.py: log_operation(operation="citation_validator_end", logger=logger)
- code/reproducibility/tie_breaking_validator.py: @log_operation
- code/reproducibility/linting_report.py: log_operation(
- code/reproducibility/generate_derivation_notes.py: @log_operation
- code/analysis/regression.py: @log_operation
- code/analysis/coverage_reporting.py: log_operation(
- code/analysis/group_comparison.py: @log_operation
- code/analysis/correlation.py: @log_operation
- code/analysis/model_reporting.py: @log_operation
- code/analysis/validation_reporting.py: log_operation("report_generation", "Hyperbolic Volume Report", {
- code/analysis/validation_reporting.py: log_operation("report_generation_complete", "Hyperbolic Volume Report", {"status": "success"})
- code/analysis/data_quality.py: log_operation(
- code/analysis/residual_analysis.py: @log_operation
- code/analysis/dataset_counts.py: @log_operation
- code/analysis/invariant_coverage.py: log_operation(
- code/analysis/plotting.py: @log_operation
- code/analysis/oeis_validation.py: log_operation(
- code/analysis/model_fitting.py: @log_operation
- code/analysis/validation.py: log_operation("validation_start", "Hyperbolic Volume Validation", {"input": str(input_path)})
- code/analysis/validation.py: log_operation("validation_end", "Hyperbolic Volume Validation", {

Make `log_operation` in `code/reproducibility/logs.py` accept ALL of the above.

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/reproducibility/logs.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/reproducibility/logs.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

```python
"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    Do NOT subclass or delegate to the stdlib ``logging`` module: its
    ``log(level, msg)`` needs an integer level and has no ``to_json`` — that is
    exactly what keeps breaking. This logger is self-contained.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None


def get_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual-purpose: a decorator (@log_operation) OR a direct logging call.

    The direct-call path ALWAYS returns a LogEntry (callers use .to_json());
    decorator use returns the wrapped function. Never return a bare function
    from the direct-call path.
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)
```

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checksums.csv` is declared but was NOT written. Scripts referencing it:
    - `code/reproducibility/validation_status.py` — NOT invoked by the run-book
    - `code/reproducibility/checksums_recorder.py` — NOT invoked by the run-book
    - `code/reproducibility/run_checksums.py` — NOT invoked by the run-book
    - `code/reproducibility/checksum_generator.py` — NOT invoked by the run-book
    - `code/reproducibility/validation_status_generator.py` — NOT invoked by the run-book
    - `code/reproducibility/checksums.py` — IS a run-book command
  Make ONE of these WRITE `data/checksums.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/knot_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/verify_invariants.py` — NOT invoked by the run-book
    - `code/data/additional_completeness.py` — NOT invoked by the run-book
    - `code/data/computed_invariants.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/knot_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/knot_atlas_raw.json` is declared but was NOT written. Scripts referencing it:
    - `code/reproducibility/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/_utils.py` — NOT invoked by the run-book
    - `code/data/parser.py` — IS a run-book command
    - `code/data/data_saver.py` — NOT invoked by the run-book
    - `code/download/knot_atlas_loader.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/knot_atlas_raw.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/knots_cleaned.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/reproducibility/hashing.py`, `code/analysis/coverage_reporting.py`, `code/analysis/data_quality.py`, `code/analysis/dataset_counts.py`, `code/analysis/oeis_validation.py`, `code/analysis/model_fitting.py`, `code/analysis/validation.py`, `code/filter/hyperbolic_filter.py`, `code/data/parser.py`, `code/data/validator.py`, `code/data/data_saver.py`, `code/download/knot_atlas_loader.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/knots_cleaned.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/reproducibility/quickstart_validator.py`, `code/reproducibility/hashing.py`, `code/analysis/coverage_reporting.py`, `code/analysis/data_quality.py`, `code/analysis/_utils.py`, `code/analysis/novel_exploratory.py`, `code/analysis/dataset_counts.py`, `code/analysis/invariant_coverage.py`, `code/analysis/plotting.py`, `code/analysis/oeis_validation.py`, `code/analysis/model_fitting.py`, `code/analysis/validation.py`, `code/analysis/interactive_knot_family_map.py`, `code/analysis/data_quantities.py`, `code/analysis/data_quality_report.py`, `code/analysis/exploratory.py`, `code/filter/hyperbolic_filter.py`, `code/data/parser.py`, `code/data/validator.py`, `code/data/data_saver.py`, `code/download/knot_atlas_loader.py`.
