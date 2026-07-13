from __future__ import annotations

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def handle_missing_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies and removes molecules with missing or invalid 3D coordinates.
    Generates an exclusion report.
    
    Args:
        df: DataFrame with molecule data
        
    Returns:
        DataFrame with valid molecules only
    """
    output_dir = PROJECT_ROOT / "data" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    excluded_records = []
    valid_records = []
    timestamp = datetime.now().isoformat()
    
    for _, row in df.iterrows():
        mol_id = row['molecule_id']
        coords = row.get('coordinates')
        atoms = row.get('atoms')
        
        # Check for missing coordinates
        if coords is None or len(coords) == 0:
            excluded_records.append({
                'molecule_id': mol_id,
                'exclusion_reason': 'missing_3d',
                'exclusion_timestamp': timestamp
            })
            continue
        
        # Check for invalid structure (e.g., mismatched atom/coord lengths)
        if atoms is None or len(atoms) != len(coords):
            excluded_records.append({
                'molecule_id': mol_id,
                'exclusion_reason': 'invalid_structure',
                'exclusion_timestamp': timestamp
            })
            continue
        
        valid_records.append(row)
    
    # Save exclusion report
    if excluded_records:
        exclusion_df = pd.DataFrame(excluded_records)
        exclusion_path = output_dir / "excluded_molecules.csv"
        exclusion_df.to_csv(exclusion_path, index=False)
        print(f"Excluded {len(excluded_records)} molecules. Report saved to {exclusion_path}")
    else:
        print("No molecules excluded.")
    
    return pd.DataFrame(valid_records)