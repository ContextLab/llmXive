# Data Model

## Entities
- **Molecule**: SMILES, InChI, Molecular Weight, TPSA, Rotatable Bonds, Aromatic Rings, Wiener Index, Zagreb Index.
- **DegradationRecord**: Molecule ID, Rate Constant (k), Half-life (t1/2), Temperature, pH, Activation Energy (Ea), Condition Type.

## Relationships
- One Molecule can have multiple DegradationRecords (different conditions).
