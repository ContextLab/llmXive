from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from rdkit import Chem

class Molecule(BaseModel):
    """
    Pydantic model for a molecule.
    """
    smi: str
    lambda_max: float
    scaffold_id: Optional[str] = None

    @field_validator('smi')
    @classmethod
    def validate_smi(cls, v: str) -> str:
        """
        Validate SMILES string.
        
        Args:
            v: SMILES string.
            
        Returns:
            Validated SMILES string.
        """
        mol = Chem.MolFromSmiles(v)
        if mol is None:
            raise ValueError(f"Invalid SMILES: {v}")
        return Chem.MolToSmiles(mol)

class Scaffold(BaseModel):
    """
    Pydantic model for a scaffold.
    """
    scaffold_id: str
    molecule_count: int = 0
    molecules: List[Molecule] = []
