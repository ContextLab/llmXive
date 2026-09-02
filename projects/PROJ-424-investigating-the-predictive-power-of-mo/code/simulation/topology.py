"""
Topology generation for MARTINI coarse-grained simulations.

Generates .gro and .top files for water, ethanol, and acetone
based on the MARTINI force field parameters.
"""
import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple

# Import project configuration
from config import Solvent, SimulationConfig, AnalysisConfig
from utils.logging import get_logger

logger = get_logger(__name__)

# MARTINI 3.0 Water bead parameters (approximate for standard CG water)
# Bead type: W (Water), Qa (Polar), etc.
# Standard MARTINI water is often modeled as 4 real water molecules per bead.
# For a simple liquid box, we use the standard W bead.
MARTINI_WATER = {
    "resname": "SOL",
    "atomname": "W",
    "atype": "W",
    "mass": 72.06,  # 4 * 18.015 g/mol
    "charge": 0.0,
    "x0": 0.0,
    "y0": 0.0,
    "z0": 0.0,
}

# Ethanol (CG): 3 beads typically (CH3-CH2-OH -> C-C-O or similar mapping)
# Mapping: CH3 (C1) - CH2 (C2) - OH (O1)
# Bead types: C1 (apolar), C2 (apolar), O1 (polar)
# Masses: CH3 (15) + CH2 (14) + OH (17) = 46 g/mol.
# In MARTINI, beads represent ~4 heavy atoms or equivalent mass.
# Ethanol is often 3 beads: C1-C2-O1
# C1 (CH3): mass ~12+3=15 -> scaled? MARTINI beads are usually ~4 real atoms.
# Let's use standard MARTINI ethanol mapping:
# Residue: ETH
# Atom 1: C1 (CH3) -> type C1, mass 15.035 (scaled to represent 4 atoms? No, mass is real mass of group)
# Actually, MARTINI bead mass is the mass of the chemical group it represents.
# CH3 group: 15.035 g/mol. CH2: 14.027. OH: 17.007.
# Total: ~46 g/mol.
# Bead types for ethanol in MARTINI 2.2/3.0:
# C1 (C), C2 (C), O1 (O)
MARTINI_ETHANOL_BEADS = [
    {"atomname": "C1", "atype": "C1", "mass": 15.035, "charge": -0.05, "resname": "ETH"},
    {"atomname": "C2", "atype": "C2", "mass": 14.027, "charge": -0.10, "resname": "ETH"},
    {"atomname": "O1", "atype": "O1", "mass": 17.007, "charge": -0.35, "resname": "ETH"},
]
# Bonds for ethanol
MARTINI_ETHANOL_BONDS = [
    ("C1", "C2", 0.47, 1250.0),  # dist (nm), force const (kJ/mol/nm^2)
    ("C2", "O1", 0.47, 1250.0),
]

# Acetone (CG): 3 beads (CH3-CO-CH3)
# Mapping: C1 (CH3) - C2 (C=O) - C3 (CH3)
# Bead types: C1 (apolar), C3 (polar, carbonyl), C1 (apolar)
# Actually, Carbonyl is often a polar bead (e.g., O2 or Qa depending on version).
# Standard MARTINI Acetone: C1 - C3 - C1 (C3 is the carbonyl carbon with O)
# Wait, Acetone is (CH3)2CO.
# Beads: C1 (CH3), C3 (C=O), C1 (CH3).
# Masses: C1 (15), C3 (12+16=28), C1 (15). Total = 58.
MARTINI_ACETONE_BEADS = [
    {"atomname": "C1", "atype": "C1", "mass": 15.035, "charge": 0.05, "resname": "ACT"},
    {"atomname": "C3", "atype": "C3", "mass": 28.010, "charge": -0.10, "resname": "ACT"}, # Carbonyl group mass approx
    {"atomname": "C1", "atype": "C1", "mass": 15.035, "charge": 0.05, "resname": "ACT"},
]
MARTINI_ACETONE_BONDS = [
    ("C1", "C3", 0.47, 1250.0),
    ("C3", "C1", 0.47, 1250.0),
]

# Bonded parameters file content (placeholder for standard MARTINI)
# In a real scenario, this would point to martini_v3.0.0.itp
MARTINI_FORCEFIELD = """
; MARTINI Force Field
; This is a simplified reference. In production, include the full .itp file.
#include "martini_v3.0.0.itp"
"""

@dataclass
class TopologyConfig:
    solvent: Solvent
    n_molecules: int
    box_size: float  # nm
    density_target: float  # g/cm3 (for estimation)

def _generate_gro_content(config: TopologyConfig) -> str:
    """Generate .gro file content for a single solvent box."""
    lines = []
    lines.append(f"Generated MARTINI box for {config.solvent.value}")
    lines.append(f"{config.n_molecules}")

    # Box dimensions (nm)
    # For water, we want ~1 g/cm3. For organics, use their densities.
    # Approximate densities: Water 1.0, Ethanol 0.789, Acetone 0.784
    # Volume V = N * M / (rho * N_A)
    # But for CG, we just need a reasonable box.
    # Let's use a fixed box size for simplicity as requested, or calculate based on density.
    # Task says "generate topology files", implies a standard setup.
    # We will place molecules in a simple grid.

    box_dims = [config.box_size, config.box_size, config.box_size]
    
    # Bead definitions
    if config.solvent == Solvent.WATER:
        beads = [MARTINI_WATER] * config.n_molecules
        resname = "SOL"
        atomname = "W"
        mass = 72.06
    elif config.solvent == Solvent.ETHANOL:
        beads = []
        for i in range(config.n_molecules):
            for j, b in enumerate(MARTINI_ETHANOL_BEADS):
                beads.append({
                    "resid": i + 1,
                    "resname": b["resname"],
                    "atomname": b["atomname"],
                    "atype": b["atype"],
                    "mass": b["mass"],
                    "charge": b["charge"]
                })
        resname = "ETH"
        atomname = None # Variable
        mass = None
    elif config.solvent == Solvent.ACETONE:
        beads = []
        for i in range(config.n_molecules):
            for j, b in enumerate(MARTINI_ACETONE_BEADS):
                beads.append({
                    "resid": i + 1,
                    "resname": b["resname"],
                    "atomname": b["atomname"],
                    "atype": b["atype"],
                    "mass": b["mass"],
                    "charge": b["charge"]
                })
        resname = "ACT"
        atomname = None
    else:
        raise ValueError(f"Unsupported solvent: {config.solvent}")

    # Simple grid placement
    # Determine grid dimensions
    n_beads_per_mol = 1 if config.solvent == Solvent.WATER else 3
    total_beads = config.n_molecules * n_beads_per_mol
    
    # Estimate grid size
    import math
    grid_n = int(math.ceil(total_beads ** (1/3)))
    spacing = config.box_size / grid_n
    
    bead_idx = 0
    for i in range(config.n_molecules):
        if config.solvent == Solvent.WATER:
            # Single bead
            bx = (bead_idx % grid_n) * spacing + spacing/2
            by = ((bead_idx // grid_n) % grid_n) * spacing + spacing/2
            bz = ((bead_idx // (grid_n*grid_n)) % grid_n) * spacing + spacing/2
            
            # Clamp to box
            bx = min(bx, config.box_size - 0.001)
            by = min(by, config.box_size - 0.001)
            bz = min(bz, config.box_size - 0.001)

            lines.append(f"{i+1:5d}{resname:5s}{atomname:5s}{bead_idx+1:5d}{bx:8.3f}{by:8.3f}{bz:8.3f}")
            bead_idx += 1
        else:
            # Multi-bead molecule
            for j, b in enumerate(MARTINI_ETHANOL_BEADS if config.solvent == Solvent.ETHANOL else MARTINI_ACETONE_BEADS):
                # Simple placement: center of mass at grid point, beads offset slightly
                base_x = (bead_idx % grid_n) * spacing + spacing/2
                base_y = ((bead_idx // grid_n) % grid_n) * spacing + spacing/2
                base_z = ((bead_idx // (grid_n*grid_n)) % grid_n) * spacing + spacing/2
                
                # Offset beads to avoid overlap (simple linear offset along X)
                offset = j * 0.15 # nm
                bx = base_x + offset
                if bx > config.box_size: bx -= config.box_size
                
                by = base_y
                bz = base_z

                lines.append(f"{i+1:5d}{b['resname']:5s}{b['atomname']:5s}{bead_idx+1:5d}{bx:8.3f}{by:8.3f}{bz:8.3f}")
                bead_idx += 1

    lines.append(f"{box_dims[0]:10.5f}{box_dims[1]:10.5f}{box_dims[2]:10.5f}")
    return "\n".join(lines)

def _generate_top_content(config: TopologyConfig) -> str:
    """Generate .top file content."""
    lines = []
    lines.append("; MARTINI Topology File")
    lines.append("; Generated by topology.py")
    lines.append("")
    
    # Includes
    lines.append("#include \"martini_v3.0.0.itp\"")
    lines.append("")
    
    # System
    lines.append("[ system ]")
    lines.append(f"{config.solvent.value} box")
    lines.append("")
    
    # Molecules
    lines.append("[ molecules ]")
    lines.append(f"{config.solvent.value.upper()}    {config.n_molecules}")
    lines.append("")
    
    # Bonded definitions (if needed, though usually in .itp)
    # For ethanol/acetone, we might need to define bonds if not in the main itp
    # But standard MARTINI .itp files handle this via [ moleculetype ]
    # We assume the .itp includes the definitions for ETH and ACT.
    # If we were generating a self-contained top, we'd need [ atomtypes ], [ nonbond_params ], etc.
    # Here we generate a minimal top assuming external .itp availability as per GROMACS convention.
    
    return "\n".join(lines)

def _generate_itp_content(solvent: Solvent) -> str:
    """Generate a minimal .itp for the specific solvent if not in standard FF."""
    # In a real project, we would link to the actual MARTINI .itp files.
    # This function generates a placeholder .itp for the specific molecule to ensure
    # the simulation can run if the standard FF is missing or if we need custom params.
    # For this task, we assume standard MARTINI includes exist, but we generate a 
    # molecule-specific .itp to be safe and self-contained for the test.
    
    lines = []
    lines.append(f"; {solvent.value} MARTINI ITP")
    lines.append("")
    
    if solvent == Solvent.WATER:
        lines.append("[ moleculetype ]")
        lines.append("SOL 3")
        lines.append("")
        lines.append("[ atoms ]")
        lines.append(";   nr       type  resnr residue  atom   cgnr     charge       mass  typeB    chargeB      massB")
        lines.append("     1        W      1    SOL     W      1      0.0000    72.06")
        lines.append("")
        lines.append("[ virtual_sites1 ]")
        lines.append(";  v  type  a b c")
        # Water is often a virtual site in MARTINI? No, standard W is a bead.
        
    elif solvent == Solvent.ETHANOL:
        lines.append("[ moleculetype ]")
        lines.append("ETH 3")
        lines.append("")
        lines.append("[ atoms ]")
        lines.append(";   nr       type  resnr residue  atom   cgnr     charge       mass")
        for i, b in enumerate(MARTINI_ETHANOL_BEADS):
            lines.append(f"     {i+1:2d}   {b['atype']:6s}      1    ETH   {b['atomname']:4s}   {i+1:2d}   {b['charge']:8.4f}   {b['mass']:8.3f}")
        lines.append("")
        lines.append("[ bonds ]")
        lines.append(";  ai    aj  funct         length          force.c. ")
        for a, b, l, k in MARTINI_ETHANOL_BONDS:
            # Find indices
            idx_a = next(i+1 for i, bead in enumerate(MARTINI_ETHANOL_BEADS) if bead["atomname"] == a)
            idx_b = next(i+1 for i, bead in enumerate(MARTINI_ETHANOL_BEADS) if bead["atomname"] == b)
            lines.append(f"  {idx_a:3d}   {idx_b:3d}    1    {l:8.4f}    {k:10.2f}")

    elif solvent == Solvent.ACETONE:
        lines.append("[ moleculetype ]")
        lines.append("ACT 3")
        lines.append("")
        lines.append("[ atoms ]")
        lines.append(";   nr       type  resnr residue  atom   cgnr     charge       mass")
        for i, b in enumerate(MARTINI_ACETONE_BEADS):
            lines.append(f"     {i+1:2d}   {b['atype']:6s}      1    ACT   {b['atomname']:4s}   {i+1:2d}   {b['charge']:8.4f}   {b['mass']:8.3f}")
        lines.append("")
        lines.append("[ bonds ]")
        lines.append(";  ai    aj  funct         length          force.c. ")
        for a, b, l, k in MARTINI_ACETONE_BONDS:
            idx_a = next(i+1 for i, bead in enumerate(MARTINI_ACETONE_BEADS) if bead["atomname"] == a)
            idx_b = next(i+1 for i, bead in enumerate(MARTINI_ACETONE_BEADS) if bead["atomname"] == b)
            lines.append(f"  {idx_a:3d}   {idx_b:3d}    1    {l:8.4f}    {k:10.2f}")
    
    return "\n".join(lines)

def generate_topology(solvent: Solvent, n_molecules: int = 1000, box_size: float = 5.0, output_dir: Path = None) -> Dict[str, Path]:
    """
    Generate MARTINI topology files (.gro, .top, .itp) for a given solvent.
    
    Args:
        solvent: The solvent to generate topology for.
        n_molecules: Number of molecules in the box.
        box_size: Box size in nm.
        output_dir: Directory to save files. Defaults to data/raw/topologies.
        
    Returns:
        Dictionary mapping file type to Path.
    """
    if output_dir is None:
        output_dir = Path("data/raw/topologies")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    config = TopologyConfig(solvent=solvent, n_molecules=n_molecules, box_size=box_size)
    
    # Generate .gro
    gro_content = _generate_gro_content(config)
    gro_path = output_dir / f"{solvent.value}.gro"
    with open(gro_path, "w") as f:
        f.write(gro_content)
    logger.info(f"Generated {gro_path}")
    
    # Generate .itp (molecule definition)
    itp_content = _generate_itp_content(solvent)
    itp_path = output_dir / f"{solvent.value}.itp"
    with open(itp_path, "w") as f:
        f.write(itp_content)
    logger.info(f"Generated {itp_path}")
    
    # Generate .top
    # Update the include to point to the local .itp we just created
    top_content_lines = [
        "; MARTINI Topology File",
        "; Generated by topology.py",
        "",
        f'#include "{solvent.value}.itp"',
        "",
        "[ system ]",
        f"{solvent.value} box",
        "",
        "[ molecules ]",
        f"{solvent.value.upper()}    {n_molecules}",
        ""
    ]
    top_content = "\n".join(top_content_lines)
    top_path = output_dir / f"{solvent.value}.top"
    with open(top_path, "w") as f:
        f.write(top_content)
    logger.info(f"Generated {top_path}")
    
    return {
        "gro": gro_path,
        "top": top_path,
        "itp": itp_path
    }

def main():
    """Entry point to generate topologies for all target solvents."""
    logger.info("Starting topology generation for US1 solvents.")
    
    # Use default parameters or read from config if extended
    # Hardcoded for T014 scope
    solvents = [Solvent.WATER, Solvent.ETHANOL, Solvent.ACETONE]
    n_mols = 1000
    box_size = 5.0 # nm
    
    results = {}
    for solv in solvents:
        try:
            paths = generate_topology(solv, n_mols, box_size)
            results[solv.value] = {str(k): str(v) for k, v in paths.items()}
        except Exception as e:
            logger.error(f"Failed to generate topology for {solv}: {e}")
            raise
    
    # Write a manifest for the generated files
    manifest_path = Path("data/raw/topologies/manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Topology manifest written to {manifest_path}")
    
    return results

if __name__ == "__main__":
    main()
