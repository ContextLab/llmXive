"""
Handles manual extraction of literature data.
"""
import os
import logging
import pandas as pd
from typing import Optional, List, Dict, Any
from pathlib import Path
from ingestion.models import PolymerRecord

logger = logging.getLogger(__name__)

def load_manual_csv() -> Optional[pd.DataFrame]:
    """
    Loads the manual CSV file.
    """
    file_path = Path("data/raw/manual_literature.csv")
    if file_path.exists():
        return pd.read_csv(file_path)
    return None

def parse_manual_records(df: pd.DataFrame) -> List[PolymerRecord]:
    """
    Parses the DataFrame into a list of PolymerRecord objects.
    """
    records = []
    for _, row in df.iterrows():
        record = PolymerRecord(
            polymer_name=row.get('polymer_name'),
            smiles=row.get('smiles'),
            permeability=row.get('permeability'),
            permeability_unit=row.get('permeability_unit'),
            selectivity=row.get('selectivity'),
            selectivity_gas_pair=row.get('selectivity_gas_pair'),
            synthesis_method=row.get('synthesis_method'),
            source='manual',
            reference=row.get('reference')
        )
        records.append(record)
    return records

def extract_manual_literature_data() -> Optional[pd.DataFrame]:
    """
    Main entry point for manual extraction.
    """
    df = load_manual_csv()
    if df is None:
        logger.warning("No manual data found.")
        return None
    
    # Ensure standard columns
    standard_cols = ['polymer_name', 'smiles', 'permeability', 'permeability_unit', 'selectivity', 'source']
    for col in standard_cols:
        if col not in df.columns:
            df[col] = None
    df['source'] = 'manual'
    return df

def main():
    df = extract_manual_literature_data()
    if df is not None:
        print(df.head())
    else:
        print("No manual data available.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
