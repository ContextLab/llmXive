import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple
from config import Solvent, SimulationConfig, AnalysisConfig

@dataclass
class TopologyConfig:
    solvent: Solvent
    n_molecules: int = 1000
    box_size: float = 5.0 # nm

def generate_topology(solvent: Solvent, config: SimulationConfig, output_dir: str) -> str:
    """Generate MARTINI topology files for the solvent."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Create .gro file (mock structure)
    gro_path = Path(output_dir) / f"{solvent.value}.gro"
    with open(gro_path, 'w') as f:
        f.write(f"{solvent.value} MARTINI\n")
        f.write(f"{config.n_steps}\n")
        # Write dummy coordinates
        for i in range(100):
            f.write(f"{i:5d}WAT{i:5d}O    {i*0.1:8.3f}{i*0.1:8.3f}{i*0.1:8.3f}\n")
        f.write(f"{config.box_size:10.5f}{config.box_size:10.5f}{config.box_size:10.5f}\n")
    
    # Create .top file
    top_path = Path(output_dir) / f"{solvent.value}.top"
    with open(top_path, 'w') as f:
        f.write(f"[ defaults ]\n")
        f.write(f"; nbfunc        comb-rule       gen-pairs       fudgeLJ fudgeQQ\n")
        f.write(f"1               1               yes             1.0     1.0\n\n")
        f.write(f"[ moleculetype ]\n")
        f.write(f"{solvent.value}    3\n\n")
        f.write(f"[ atoms ]\n")
        f.write(f"; nr  type  resnr residue  atom   cgnr     charge       mass\n")
        f.write(f"1    W1      1     {solvent.value}    OW      1      -0.84        18.0\n")
    
    # Create .mdp file
    mdp_path = Path(output_dir) / f"{solvent.value}.mdp"
    with open(mdp_path, 'w') as f:
        f.write(f"; Run parameters\n")
        f.write(f"integrator              = md\n")
        f.write(f"nsteps                  = {config.n_steps}\n")
        f.write(f"dt                      = {config.time_step}e-15\n")
        f.write(f"nstxout                 = 1000\n")
        f.write(f"nstvout                 = 1000\n")
        f.write(f"nstlog                  = 1000\n")
        f.write(f"nstenergy               = 1000\n")
        f.write(f"nstxtcout               = 1000\n")
        f.write(f"tcoupl                  = V-rescale\n")
        f.write(f"tc-grps                 = System\n")
        f.write(f"tau_t                   = 0.1\n")
        f.write(f"ref_t                   = {config.temperature}\n")
    
    return str(gro_path)

def main():
    """Test topology generation."""
    from config import SIMULATION_CONFIG, Solvent
    generate_topology(Solvent.WATER, SIMULATION_CONFIG, "data/raw/topologies")
    print("Topology generated.")

if __name__ == "__main__":
    main()
