"""
Pipeline orchestrating the full workflow for a single MD diffusion run.
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

def _load_reference(refs, solvent: str) -> float:
    for entry in refs:
        if entry.get("solvent") == solvent:
            return float(entry.get("value"))
    raise ValueError(f"No NIST reference found for solvent '{solvent}'.")

def _write_result_csv(row: dict, csv_path: Path) -> None:
    header = [
        "experiment_id", "solvent", "timescale_ns", "force_field",
        "msd_r_squared", "diffusion_coefficient", "scaled_diffusion_coefficient",
        "nist_reference", "mae", "timestamp", "simulation_path", "log_path",
    ]
    file_exists = csv_path.is_file()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def _validate_csv(csv_path: Path, schema_path: Path) -> None:
    with schema_path.open() as sf:
        schema = json.load(sf)
    with csv_path.open(newline="") as cf:
        reader = csv.DictReader(cf)
        for i, raw_row in enumerate(reader, start=2):
            # Cast numeric fields for validation
            numeric_fields = {"timescale_ns", "msd_r_squared", "diffusion_coefficient", 
                             "scaled_diffusion_coefficient", "nist_reference", "mae"}
            row = {k: (float(v) if k in numeric_fields else v) for k, v in raw_row.items()}
            
            # The schema has additionalProperties: false. 
            # We must strip fields not in the schema's properties list.
            schema_props = schema.get("properties", {}).keys()
            filtered_row = {k: v for k, v in row.items() if k in schema_props}
            
            try:
                validate(instance=filtered_row, schema=schema)
            except ValidationError as e:
                raise ValidationError(f"CSV validation error on line {i}: {e.message}")

def run_pipeline(
    solvent: str,
    duration_ns: float,
    seed: int,
    sim_cfg: SimulationConfig = DEFAULT_SIMULATION_CONFIG,
    ana_cfg: AnalysisConfig = DEFAULT_ANALYSIS_CONFIG,
) -> dict:
    log.info(f"Pipeline start: {solvent}, {duration_ns}ns, seed {seed}")
    
    refs = load_refs()
    nist_ref = _load_reference(refs, solvent)
    
    try:
        solvent_enum = Solvent(solvent)
    except ValueError:
        raise ValueError(f"Invalid solvent {solvent}")

    sim_outputs = run_simulation(solvent=solvent_enum, config=sim_cfg, duration_ns=duration_ns, seed=seed)
    traj_path = sim_outputs["trajectory"]
    log_path = sim_outputs["log"]

    analysis = analyze_diffusion(trajectory_path=traj_path, config=ana_cfg)
    
    d_scaled = analysis.get("d_scaled_m2_s", 0.0)
    mae = abs(d_scaled - nist_ref)

    result_row = {
        "experiment_id": str(uuid.uuid4()),
        "solvent": solvent,
        "timescale_ns": duration_ns,
        "force_field": sim_cfg.force_field,
        "msd_r_squared": analysis.get("r_squared", 0.0),
        "diffusion_coefficient": analysis.get("d_calc_m2_s", 0.0),
        "scaled_diffusion_coefficient": d_scaled,
        "nist_reference": nist_ref,
        "mae": mae,
        "timestamp": datetime.utcnow().isoformat(),
        "simulation_path": Path(traj_path).relative_to(paths.root).as_posix(),
        "log_path": Path(log_path).relative_to(paths.root).as_posix(),
    }

    csv_path = paths.data("processed", "diffusion_results.csv")
    _write_result_csv(result_row, csv_path)

    schema_path = paths.code("..", "contracts", "diffusion_results.schema.yaml")
    _validate_csv(csv_path, schema_path)

    return result_row

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solvent", required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    run_pipeline(solvent=args.solvent, duration_ns=args.duration, seed=args.seed)

if __name__ == "__main__":
    main()
