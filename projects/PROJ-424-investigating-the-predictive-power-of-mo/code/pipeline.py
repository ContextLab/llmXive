"""
Pipeline orchestrating the full workflow for a single MD diffusion run.

Steps:
  1. Load curated NIST reference diffusion coefficients.
  2. Run a short OpenMM NPT simulation for the requested solvent,
     duration and seed.  The real OpenMM runner has been replaced by a
     mock implementation (see ``code/simulations/run_simulation.py``) that
     generates a minimal PDB trajectory readable by ``mdtraj``.
  3. Analyse the resulting trajectory to obtain MSD slope, R²,
     diffusion coefficient and status.
  4. Compute MAE against the experimental reference.
  5. Write a schema‑conforming CSV row to
     `data/processed/diffusion_results.csv`.
  6. Validate the CSV file against the JSON schema in
     `contracts/diffusion_results.schema.yaml`.

The script can be invoked directly:

    python code/pipeline.py --solvent water --duration 1 --seed 0

The command is already documented in
`specs/001-investigating-the-predictive-power-of-mo/quickstart.md`.
"""

import argparse
import csv
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

from jsonschema import validate, ValidationError

from llmxive_toolkit import paths, get_logger

# Project imports
from code.data.loader import load_refs
from code.simulations.run_simulation import run_simulation
from code.analysis.diffusion import analyze_diffusion
from code.config import (
    DEFAULT_SIMULATION_CONFIG,
    DEFAULT_ANALYSIS_CONFIG,
    SimulationConfig,
    AnalysisConfig,
    Solvent,
)

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_reference(refs, solvent: str) -> float:
    """Return the experimental diffusion coefficient for *solvent*."""
    for entry in refs:
        if entry.get("solvent") == solvent:
            return float(entry.get("value"))
    raise ValueError(f"No NIST reference found for solvent '{solvent}'.")


def _write_result_csv(row: dict, csv_path: Path) -> None:
    """Append *row* to *csv_path*, writing a header if the file is new."""
    header = [
        "experiment_id",
        "solvent",
        "timescale_ns",
        "force_field",
        "msd_r_squared",
        "diffusion_coefficient",
        "scaled_diffusion_coefficient",
        "nist_reference",
        "mae",
        "timestamp",
        "simulation_path",
        "log_path",
    ]

    file_exists = csv_path.is_file()
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _cast_row_types(row: dict) -> dict:
    """Cast numeric fields to ``float`` for JSON‑schema validation."""
    numeric_fields = {
        "timescale_ns",
        "msd_r_squared",
        "diffusion_coefficient",
        "scaled_diffusion_coefficient",
        "nist_reference",
        "mae",
    }
    casted = {}
    for k, v in row.items():
        if k in numeric_fields:
            try:
                casted[k] = float(v)
            except (TypeError, ValueError):
                casted[k] = v
        else:
            casted[k] = v
    return casted


def _validate_csv(csv_path: Path, schema_path: Path) -> None:
    """Validate every record in *csv_path* against the JSON schema."""
    with schema_path.open() as sf:
        schema = json.load(sf)

    with csv_path.open(newline="") as cf:
        reader = csv.DictReader(cf)
        for i, raw_row in enumerate(reader, start=2):  # start=2 accounts for header
            row = _cast_row_types(raw_row)
            try:
                validate(instance=row, schema=schema)
            except ValidationError as e:
                raise ValidationError(
                    f"CSV validation error on line {i}: {e.message}"
                ) from e


# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------


def run_pipeline(
    solvent: str,
    duration_ns: float,
    seed: int,
    sim_cfg: SimulationConfig = DEFAULT_SIMULATION_CONFIG,
    ana_cfg: AnalysisConfig = DEFAULT_ANALYSIS_CONFIG,
) -> dict:
    """
    Execute the full end‑to‑end workflow for a single solvent/duration/seed.

    Returns the dictionary that was written to the CSV (useful for testing).
    """
    log.info(
        f"Pipeline start – solvent={solvent}, duration={duration_ns} ns, seed={seed}"
    )

    # 1. Load experimental references
    refs = load_refs()
    nist_ref = _load_reference(refs, solvent)

    # 2. Convert solvent string to enum expected by the simulation module
    try:
        solvent_enum = Solvent(solvent)
    except ValueError as e:
        raise ValueError(
            f"Invalid solvent '{solvent}'. Must be one of: water, ethanol, acetone."
        ) from e

    # 3. Run the MD simulation (mock implementation)
    sim_outputs = run_simulation(
        solvent=solvent_enum,
        config=sim_cfg,
        duration_ns=duration_ns,
        seed=seed,
    )
    traj_path = sim_outputs["trajectory"]
    log_path = sim_outputs["log"]

    # 4. Analyse the trajectory
    analysis = analyze_diffusion(
        trajectory_path=traj_path,
        config=ana_cfg,
    )
    # Expected keys in ``analysis`` (as per ``code.analysis.diffusion``):
    #   msd_slope, r_squared, d_calc_m2_s, d_scaled_m2_s, status, message
    msd_slope = analysis.get("msd_slope")
    r_squared = analysis.get("r_squared")
    d_calc = analysis.get("d_calc_m2_s")
    d_scaled = analysis.get("d_scaled_m2_s")
    status = analysis.get("status")

    # 5. Compute MAE (use the scaled coefficient for comparison)
    mae = abs(d_scaled - nist_ref)

    # 6. Assemble CSV row matching the contract
    result_row = {
        "experiment_id": str(uuid.uuid4()),
        "solvent": solvent,
        "timescale_ns": duration_ns,
        "force_field": sim_cfg.force_field,
        "msd_r_squared": r_squared,
        "diffusion_coefficient": d_calc,
        "scaled_diffusion_coefficient": d_scaled,
        "nist_reference": nist_ref,
        "mae": mae,
        "timestamp": datetime.utcnow().isoformat(),
        "simulation_path": Path(traj_path).relative_to(paths.root).as_posix(),
        "log_path": Path(log_path).relative_to(paths.root).as_posix(),
    }

    # 7. Write to CSV
    csv_path = paths.data("processed", "diffusion_results.csv")
    _write_result_csv(result_row, csv_path)

    # 8. Validate CSV against the JSON schema
    schema_path = paths.code("..", "contracts", "diffusion_results.schema.yaml")
    _validate_csv(csv_path, schema_path)

    log.info(f"Pipeline completed successfully – results written to {csv_path}")
    return result_row


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run the MD diffusion pipeline for a single configuration."
    )
    parser.add_argument(
        "--solvent",
        type=str,
        required=True,
        choices=["water", "ethanol", "acetone"],
        help="Solvent to simulate.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        required=True,
        help="Simulation duration in nanoseconds.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for the simulation (default: 0).",
    )
    return parser.parse_args(argv)


def main():
    args = _parse_args(sys.argv[1:])
    run_pipeline(
        solvent=args.solvent,
        duration_ns=args.duration,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
