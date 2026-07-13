from __future__ import annotations

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def handle_missing_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing 3D coordinates in the dataframe.
    Generates a report of excluded molecules.
    """
    data_dir = PROJECT_ROOT / "data" / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    excluded_rows = []
    valid_rows = []
    
    for idx, row in df.iterrows():
        coords = row.get('coordinates')
        if coords is None or (isinstance(coords, list) and len(coords) == 0):
            excluded_rows.append({
                'molecule_id': row['molecule_id'],
                'exclusion_reason': 'missing_3d',
                'exclusion_timestamp': datetime.now().isoformat()
            })
        else:
            valid_rows.append(row)
    
    # Write report
    if excluded_rows:
        report_df = pd.DataFrame(excluded_rows)
        report_path = data_dir / "excluded_molecules.csv"
        report_df.to_csv(report_path, index=False)
        print(f"Excluded {len(excluded_rows)} molecules with missing coordinates. Report saved to {report_path}")
    
    return pd.DataFrame(valid_rows)