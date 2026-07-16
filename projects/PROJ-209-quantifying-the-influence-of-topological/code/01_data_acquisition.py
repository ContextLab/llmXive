import os
import csv
import time
import json
import hashlib
import subprocess
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

def get_git_hash() -> str:
    """Get the current git commit hash."""
    try:
        result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "no-git"

def ensure_output_directories() -> Path:
    """Ensure all required output directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_RAW_DIR

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def serialize_structure(structure_dict: Dict[str, Any]) -> str:
    """Serialize a structure dictionary to a JSON string for hashing."""
    return json.dumps(structure_dict, sort_keys=True)

class MaterialsProjectClient:
    """Client for interacting with the Materials Project REST API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the client.
        
        Args:
            api_key: Materials Project API key. If None, tries to read from 
                    MP_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("MP_API_KEY")
        if not self.api_key:
            logger.warning("No Materials Project API key provided. "
                         "Set MP_API_KEY environment variable or pass api_key.")
        
        self.base_url = "https://api.materialsproject.org"
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        } if self.api_key else {}

    def query_pristine_structures(self, chemical_systems: List[str], 
                                min_results: int = 50) -> List[Dict[str, Any]]:
        """
        Query Materials Project API for pristine structures.
        
        Args:
            chemical_systems: List of chemical formulas to query (e.g., ['Graphene', 'MoS2'])
            min_results: Minimum number of structures to retrieve
            
        Returns:
            List of structure dictionaries with required fields
        """
        structures = []
        
        # Map chemical systems to MP chemical formulas
        # Graphene -> C, MoS2 -> MoS2
        formula_map = {
            "Graphene": "C",
            "MoS2": "MoS2"
        }
        
        target_formulas = []
        for system in chemical_systems:
            if system in formula_map:
                target_formulas.append(formula_map[system])
            else:
                target_formulas.append(system)
        
        # Try to fetch from API
        if self.api_key:
            try:
                for formula in target_formulas:
                    # Query for crystals with this formula
                    url = f"{self.base_url}/v2/documents/materials"
                    params = {
                        "formula": formula,
                        "fields": "materials_id,formula_pretty,nsites,symmetry,structure,properties",
                        "limit": 100
                    }
                    
                    response = requests.get(url, headers=self.headers, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "data" in data:
                            for item in data["data"]:
                                # Extract structure info
                                structure_info = self._extract_structure_info(item)
                                if structure_info:
                                    structures.append(structure_info)
                                    if len(structures) >= min_results:
                                        break
                    elif response.status_code == 401:
                        logger.error("API key invalid or missing.")
                        break
                    else:
                        logger.warning(f"API returned status {response.status_code} for {formula}")
                        
            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")
        else:
            logger.warning("No API key provided, skipping API query.")
        
        # If we don't have enough structures, we'll need to handle this in the main logic
        # For now, return whatever we got
        return structures[:min_results]

    def _extract_structure_info(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract relevant structure information from an API response item."""
        try:
            structure = item.get("structure", {})
            properties = item.get("properties", {})
            
            # Extract lattice parameters if available
            lattice = structure.get("lattice", {})
            
            return {
                "materials_id": item.get("materials_id"),
                "formula": item.get("formula_pretty"),
                "nsites": item.get("nsites"),
                "space_group": item.get("symmetry", {}).get("space_group_number"),
                "lattice_a": lattice.get("a"),
                "lattice_b": lattice.get("b"),
                "lattice_c": lattice.get("c"),
                "lattice_alpha": lattice.get("alpha"),
                "lattice_beta": lattice.get("beta"),
                "lattice_gamma": lattice.get("gamma"),
                "num_atoms": len(structure.get("sites", [])),
                "energy_per_atom": properties.get("energy_per_atom"),
                "formation_energy_per_atom": properties.get("formation_energy_per_atom"),
                "structure_json": json.dumps(structure)  # Store full structure as JSON
            }
        except Exception as e:
            logger.warning(f"Failed to extract structure info: {e}")
            return None

def load_cached_pristine_structures(file_path: Path) -> List[Dict[str, Any]]:
    """Load previously cached pristine structures from CSV."""
    structures = []
    if not file_path.exists():
        return structures
    
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            numeric_fields = ['nsites', 'space_group', 'lattice_a', 'lattice_b', 'lattice_c',
                            'lattice_alpha', 'lattice_beta', 'lattice_gamma', 'num_atoms',
                            'energy_per_atom', 'formation_energy_per_atom']
            for field in numeric_fields:
                if field in row and row[field]:
                    try:
                        if field in ['lattice_a', 'lattice_b', 'lattice_c', 'lattice_alpha', 
                                   'lattice_beta', 'lattice_gamma', 'energy_per_atom', 
                                   'formation_energy_per_atom']:
                            row[field] = float(row[field])
                        else:
                            row[field] = int(row[field])
                    except ValueError:
                        pass
            
            # Parse structure JSON
            if 'structure_json' in row:
                try:
                    row['structure_json'] = json.loads(row['structure_json'])
                except json.JSONDecodeError:
                    pass
            
            structures.append(row)
    
    return structures

def save_structures_to_csv(structures: List[Dict[str, Any]], file_path: Path) -> None:
    """Save structures to CSV file."""
    if not structures:
        logger.warning("No structures to save.")
        return
    
    # Define fieldnames
    fieldnames = ['materials_id', 'formula', 'nsites', 'space_group', 'lattice_a', 
                 'lattice_b', 'lattice_c', 'lattice_alpha', 'lattice_beta', 'lattice_gamma',
                 'num_atoms', 'energy_per_atom', 'formation_energy_per_atom', 'structure_json']
    
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for structure in structures:
            writer.writerow(structure)
    
    logger.info(f"Saved {len(structures)} structures to {file_path}")

def download_2022_defect_dataset(output_path: Path) -> bool:
    """
    Attempt to download the 2022 Supplementary Defect Dataset.
    
    Returns:
        True if successful, False otherwise
    """
    # Placeholder for actual download logic
    # In a real implementation, this would fetch from a specific URL
    logger.info("Attempting to download 2022 Defect Dataset...")
    return False  # Currently returns False as dataset is not available

def verify_defect_dataset(file_path: Path) -> bool:
    """
    Verify the defect dataset has required columns and row count.
    
    Args:
        file_path: Path to the defect dataset CSV
        
    Returns:
        True if valid, False otherwise
    """
    required_columns = ['defect_type', 'defect_density', 'conductivity', 
                      'elastic_tensor', 'fracture_energy']
    
    if not file_path.exists():
        logger.warning(f"Defect dataset file not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                logger.warning("Empty CSV file or no headers")
                return False
            
            # Check for required columns
            missing_cols = [col for col in required_columns if col not in headers]
            if missing_cols:
                logger.warning(f"Missing required columns: {missing_cols}")
                return False
            
            # Check row count
            row_count = sum(1 for _ in reader)
            if row_count == 0:
                logger.warning("Dataset has no data rows")
                return False
            
            logger.info(f"Defect dataset verified: {row_count} rows, all required columns present")
            return True
            
    except Exception as e:
        logger.error(f"Error verifying defect dataset: {e}")
        return False

def run_fallback_synthetic_generation(output_dir: Path) -> bool:
    """
    Trigger synthetic data generation if real data is unavailable.
    
    Args:
        output_dir: Directory to save synthetic data
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("Triggering fallback synthetic data generation...")
    try:
        # Import and run synthetic generator
        from generators.synthetic_data_generator import generate_synthetic_data, save_to_csv
        
        # Generate synthetic data
        synthetic_data = generate_synthetic_data(n_samples=150, seed=42)
        
        # Save to file
        output_path = output_dir / "synthetic_defect_fallback.csv"
        save_to_csv(synthetic_data, output_path)
        
        logger.info(f"Generated {len(synthetic_data)} synthetic entries")
        return True
    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}")
        return False

def run_acquisition(chemical_systems: List[str] = ["Graphene", "MoS2"], 
                   min_structures: int = 50,
                   api_key: Optional[str] = None) -> bool:
    """
    Main acquisition function to query and cache pristine structures.
    
    Args:
        chemical_systems: List of chemical systems to query
        min_structures: Minimum number of structures to retrieve
        api_key: Materials Project API key
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directories exist
        output_dir = ensure_output_directories()
        output_path = output_dir / "pristine_structures.csv"
        
        # Check if we have cached data
        cached_structures = load_cached_pristine_structures(output_path)
        
        if len(cached_structures) >= min_structures:
            logger.info(f"Using cached {len(cached_structures)} structures (>= {min_structures})")
            return True
        
        # Initialize client and query API
        client = MaterialsProjectClient(api_key=api_key)
        
        # Query for structures
        structures = client.query_pristine_structures(chemical_systems, min_structures)
        
        if not structures:
            logger.warning("No structures retrieved from API")
            # Try to use cached data if available
            if cached_structures:
                logger.info(f"Using {len(cached_structures)} cached structures")
                return True
            return False
        
        # Combine with cached data if needed
        if cached_structures:
            # Avoid duplicates
            existing_ids = {s['materials_id'] for s in cached_structures}
            new_structures = [s for s in structures if s['materials_id'] not in existing_ids]
            all_structures = cached_structures + new_structures
        else:
            all_structures = structures
        
        # Save to CSV
        save_structures_to_csv(all_structures, output_path)
        
        # Compute and log checksum
        checksum = compute_sha256(output_path)
        logger.info(f"Saved {len(all_structures)} structures to {output_path} (SHA-256: {checksum})")
        
        return True
        
    except Exception as e:
        logger.error(f"Acquisition failed: {e}")
        return False

def main():
    """Main entry point for data acquisition."""
    logger.info("Starting data acquisition...")
    
    # Get API key from environment or command line
    api_key = os.getenv("MP_API_KEY")
    
    # Run acquisition
    success = run_acquisition(
        chemical_systems=["Graphene", "MoS2"],
        min_structures=50,
        api_key=api_key
    )
    
    if success:
        logger.info("Data acquisition completed successfully")
    else:
        logger.error("Data acquisition failed")
        
    return success

if __name__ == "__main__":
    main()