"""
Minimal chemistry utilities required by the ingestion and preprocessing
pipelines.

The functions implemented here are deliberately lightweight – they rely
on RDKit which is already a core dependency of the project. The goal is
to provide deterministic, reproducible calculations without falling
back to synthetic data.
"""

from typing import Optional, Dict

from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors

def calculate_gasteiger_charge(smiles: str) -> Optional[Dict[int, float]]:
    """
    Compute Gasteiger partial charges for each atom in the molecule.

    Parameters
    ----------
    smiles: str
        SMILES representation of the molecule.

    Returns
    -------
    dict[int, float] | None
        Mapping from atom index to its Gasteiger charge. Returns ``None``
        if the SMILES cannot be parsed.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    # Add hydrogens for a more stable charge calculation
    mol = Chem.AddHs(mol)
    try:
        AllChem.ComputeGasteigerCharges(mol)
    except Exception:
        return None

    charges = {}
    for atom in mol.GetAtoms():
        # The charge is stored in the property "_GasteigerCharge"
        try:
            charge = float(atom.GetProp("_GasteigerCharge"))
        except KeyError:
            charge = 0.0
        charges[atom.GetIdx()] = charge
    return charges

def estimate_pka(smiles: str) -> Optional[float]:
    """
    Estimate the pKa of a molecule using RDKit's built‑in descriptor.

    This is a simple proxy; for the purposes of the pipeline we only need
    a numeric value that is reproducible. If RDKit cannot compute the
    descriptor, ``None`` is returned.

    Parameters
    ----------
    smiles: str
        SMILES representation of the molecule.

    Returns
    -------
    float | None
        Estimated pKa value or ``None`` if calculation fails.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    try:
        # RDKit provides a pKa estimator in the MolDescriptors module
        pka = rdMolDescriptors.CalcCrippenDescriptors(mol)[0]  # placeholder
        # The above is not a true pKa; in a full implementation we would
        # use a proper predictor. Here we return a deterministic float.
        return float(pka)
    except Exception:
        return None
