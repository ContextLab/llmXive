import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

# Import from existing API surface
from code.utils.logger import setup_logger, handle_exception, log_critical_failure
from code.utils.smiles_parser import SMILESParser, BaseDataLoader, load_smiles_file, parse_smiles
from code.config import get_config

# Setup logger
logger = setup_logger(__name__)

class EASFilter:
    """Filters reactions based on Electrophilic Aromatic Substitution patterns."""
    
    def __init__(self):
        self.parser = SMILESParser()
        # Simplified pattern for EAS: aromatic ring with at least one substituent
        # In a real implementation, this would use RDKit SMARTS for specific EAS patterns
        self.eas_pattern = self._load_eas_pattern()
    
    def _load_eas_pattern(self):
        """Loads the EAS pattern definition."""
        # Placeholder for actual SMARTS pattern logic
        # This would be defined in a spec or config file
        return "c1ccccc1" # Benzene ring as base

    def is_eas_reaction(self, smiles: str) -> bool:
        """
        Determines if a reaction SMILES represents an EAS reaction.
        
        Args:
            smiles: Reaction SMILES string
            
        Returns:
            True if EAS reaction, False otherwise
        """
        try:
            if not smiles or not isinstance(smiles, str):
                return False
            
            # Basic check: contains aromatic ring and reaction arrow
            if '>' not in smiles:
                return False
            
            # Parse reactants
            parts = smiles.split('>')
            if len(parts) != 3:
                return False
            
            reactants = parts[0].split('.')
            if not reactants:
                return False
            
            # Check if any reactant is aromatic
            has_aromatic = False
            for r in reactants:
                if r and 'c' in r.lower(): # Simple heuristic for aromatic carbon
                    mol = self.parser.parse_smiles(r)
                    if mol and mol.HasSubstructMatch(self.parser.get_aromatic_ring()):
                        has_aromatic = True
                        break
            
            return has_aromatic
        except Exception as e:
            logger.debug(f"Error checking EAS pattern for {smiles}: {e}")
            return False

class IngestionPipeline:
    """Main pipeline for ingesting and filtering reaction data."""
    
    def __init__(self):
        self.config = get_config()
        self.filter = EASFilter()
        self.logger = setup_logger(__name__)
        self.raw_dir = Path(self.config.get('raw_data_dir', 'data/raw'))
        self.processed_dir = Path(self.config.get('processed_data_dir', 'data/processed'))
        
        # Ensure directories exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def load_uspto_data(self, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Loads USPTO-50k data.
        
        Args:
            file_path: Path to the data file. If None, uses config default.
            
        Returns:
            List of reaction records
        """
        path = Path(file_path) if file_path else self.raw_dir / "uspto_50k.json"
        
        if not path.exists():
            # In a real scenario, T011 would have downloaded this
            # For this task, we assume it exists or raise an error
            raise FileNotFoundError(f"USPTO data file not found: {path}")
        
        records = []
        with open(path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict) and 'reactions' in data:
                records = data['reactions']
            else:
                raise ValueError("Invalid data format in USPTO file")
        
        return records

    def filter_eas(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filters records to keep only EAS reactions.
        
        Args:
            records: List of reaction records
            
        Returns:
            Filtered list of EAS reaction records
        """
        eas_records = []
        for record in records:
            smiles = record.get('smiles', '')
            if self.filter.is_eas_reaction(smiles):
                eas_records.append(record)
        
        return eas_records

    def calculate_checksum(self, data: str) -> str:
        """Calculates SHA-256 checksum of data."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def write_to_csv(self, records: List[Dict[str, Any]], output_path: Path):
        """
        Writes filtered records to CSV and generates checksum.
        
        Args:
            records: List of reaction records
            output_path: Path to output CSV file
        """
        if not records:
            self.logger.warning("No records to write")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write CSV
        df.to_csv(output_path, index=False)
        self.logger.info(f"Wrote {len(records)} records to {output_path}")
        
        # Calculate checksum
        with open(output_path, 'r') as f:
            content = f.read()
            checksum = self.calculate_checksum(content)
        
        # Write checksum file
        checksum_path = output_path.with_suffix('.sha256')
        with open(checksum_path, 'w') as f:
            f.write(f"{checksum}  {output_path.name}\n")
        
        self.logger.info(f"Generated checksum: {checksum}")
        
        return checksum

    def run(self, input_file: Optional[str] = None, output_file: Optional[str] = None) -> bool:
        """
        Runs the full ingestion pipeline.
        
        Args:
            input_file: Path to input USPTO file
            output_file: Path to output CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load data
            self.logger.info("Loading USPTO data...")
            records = self.load_uspto_data(input_file)
            self.logger.info(f"Loaded {len(records)} total records")
            
            # Filter EAS
            self.logger.info("Filtering for EAS reactions...")
            eas_records = self.filter_eas(records)
            n_eas = len(eas_records)
            self.logger.info(f"Found {n_eas} EAS reactions")
            
            # Gate logic from T014
            if n_eas < 100:
                log_critical_failure(
                    f"Insufficient EAS reactions found: {n_eas} < 100. "
                    "Pipeline halted to prevent invalid modeling."
                )
                return False
            
            # Write output
            output_path = Path(output_file) if output_file else self.processed_dir / "eas_reactions.csv"
            self.logger.info(f"Writing filtered dataset to {output_path}...")
            self.write_to_csv(eas_records, output_path)
            
            self.logger.info("Ingestion pipeline completed successfully")
            return True
            
        except Exception as e:
            handle_exception(e, "Ingestion pipeline failed")
            return False

def main():
    """Entry point for the ingestion script."""
    pipeline = IngestionPipeline()
    success = pipeline.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
