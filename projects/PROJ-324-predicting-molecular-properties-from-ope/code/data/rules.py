"""
Chemical rules and SMARTS patterns for substructure identification.
"""

SMARTS_PATTERNS = [
    {"name": "hydroxyl", "smarts": "[OX2H]"},
    {"name": "carbonyl", "smarts": "[CX3](=[OX1])"},
    {"name": "aromatic", "smarts": "a"},
    {"name": "amine", "smarts": "[NX3]"},
    {"name": "carboxyl", "smarts": "C(=O)O"}
]
