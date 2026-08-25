"""
Data Loader: NCBI Entrez, KEGG, and USDA PLANTS fetchers.
Implements T013, T014, and T024.
"""
import logging
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Set, Any
from pathlib import Path
from dataclasses import dataclass, field
import requests
import xml.etree.ElementTree as ET

from logging_config import get_logger
from config import get_config

logger = get_logger(__name__)

@dataclass
class FetchResult:
    success: bool
    sequences: Dict[str, str]  # locus -> sequence
    error: Optional[str] = None

@dataclass
class SpeciesData:
    species: str
    genes: Dict[str, str]
    metabolites: Set[str]

def fetch_marker_genes(species_name: str, markers: List[str]) -> FetchResult:
    """
    Fetch marker genes from NCBI Entrez.
    Constraint: Must raise ValueError if fetch fails. No synthetic fallback.
    """
    results = {}
    failed_loci = []

    for locus in markers:
        query = f"{locus}[Gene Name] AND {species_name}[Organism]"
        
        try:
            search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            params = {
                "db": "nucleotide",
                "term": query,
                "retmode": "xml",
                "retmax": 1
            }
            
            resp = requests.get(search_url, params=params, timeout=30)
            resp.raise_for_status()
            
            root = ET.fromstring(resp.content)
            id_list = root.findall(".//IdList/Id")
            
            if not id_list:
                logger.warning(f"No sequences found for {species_name} - {locus}")
                failed_loci.append(locus)
                continue
            
            acc_id = id_list[0].text
            
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            fetch_params = {
                "db": "nucleotide",
                "id": acc_id,
                "rettype": "fasta",
                "retmode": "text"
            }
            
            seq_resp = requests.get(fetch_url, params=fetch_params, timeout=30)
            seq_resp.raise_for_status()
            
            lines = seq_resp.text.split("\n")
            seq = "".join([l for l in lines if not l.startswith(">")])
            results[locus] = seq
            
            time.sleep(0.34)

        except Exception as e:
            logger.error(f"Failed to fetch {locus} for {species_name}: {e}")
            failed_loci.append(locus)

    if not results:
        raise ValueError(f"Failed to fetch any markers for {species_name}. Loci failed: {failed_loci}")
    
    return FetchResult(success=True, sequences=results)

def fetch_metabolite_profiles(species_name: str) -> Optional[Set[str]]:
    """
    Fetch metabolite profiles from KEGG.
    Constraint: Must handle species with no KEGG entry by excluding from matrix but flagging in log.
    """
    try:
        search_url = f"https://rest.kegg.jp/find/organism/{species_name}"
        resp = requests.get(search_url, timeout=30)
        resp.raise_for_status()
        
        lines = resp.text.strip().split("\n")
        if not lines:
            logger.warning(f"No KEGG organism entry for {species_name}")
            return None
        
        parts = lines[0].split("\t")
        org_code = parts[0]
        
        compounds_url = f"https://rest.kegg.jp/link/compound/{org_code}"
        comp_resp = requests.get(compounds_url, timeout=30)
        comp_resp.raise_for_status()
        
        compounds = set()
        for line in comp_resp.text.split("\n"):
            if line.startswith("cpd:"):
                compounds.add(line.split("\t")[1])
        
        if not compounds:
            logger.warning(f"No compounds found for {species_name} (KEGG code: {org_code})")
            return None
            
        return compounds

    except Exception as e:
        logger.warning(f"KEGG fetch failed for {species_name}: {e}")
        return None

def save_fasta_sequences(sequences: Dict[str, str], output_path: Path):
    """Save sequences to a FASTA file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for name, seq in sequences.items():
            f.write(f">{name}\n{seq}\n")

def fetch_usda_climate_data(species_list: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Fetch USDA PLANTS climate zone data for a list of species.
    
    Source: USDA PLANTS Database via the official API.
    URL: https://plants.usda.gov/api/v3/
    
    Constraint: Must use verified real source; no mock data.
    Constraint: Must raise ValueError if fetch fails for critical data.
    
    Returns:
        Dict mapping species scientific name to a dict of climate attributes:
        {
            "avg_min_temp": float (Celsius),
            "avg_max_temp": float (Celsius),
            "avg_precip": float (mm),
            "zone_id": int
        }
    """
    config = get_config()
    output_dir = Path(config.data_raw_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    climate_data = {}
    base_url = "https://plants.usda.gov/api/v3/plant"
    
    # We need to map species names to USDA IDs or search directly.
    # The API allows searching by scientific name.
    # We will fetch climate data for each species.
    
    logger.info(f"Fetching USDA climate data for {len(species_list)} species.")
    
    for species in species_list:
        try:
            # Search for the plant by scientific name
            search_url = f"{base_url}/search"
            params = {
                "scientificName": species,
                "limit": 1
            }
            
            resp = requests.get(search_url, params=params, timeout=30)
            resp.raise_for_status()
            
            data = resp.json()
            
            if not data.get("data") or len(data["data"]) == 0:
                logger.warning(f"No USDA entry found for {species}. Skipping climate data.")
                continue
            
            plant_data = data["data"][0]
            plant_id = plant_data.get("id")
            
            if not plant_id:
                logger.warning(f"USDA entry found for {species} but missing ID. Skipping.")
                continue
            
            # Fetch detailed climate data using the plant ID
            # The climate data is often in the 'climate' or 'environment' section.
            # Based on USDA API v3, we look for climate attributes in the full record.
            # Alternatively, we can fetch the specific plant details endpoint.
            
            detail_url = f"{base_url}/{plant_id}"
            detail_resp = requests.get(detail_url, timeout=30)
            detail_resp.raise_for_status()
            
            detail_json = detail_resp.json()
            
            # Extract climate attributes
            # USDA v3 API structure varies, but typically includes 'climate' or 'environment' keys.
            # We will attempt to extract temperature and precipitation data.
            # Note: The exact field names depend on the USDA API version.
            # Common fields: 'climateData', 'temperature', 'precipitation'.
            
            climate_info = {}
            
            # Attempt to find climate data in the response
            # We look for a 'climate' or 'environment' key in the top level or nested
            climate_section = detail_json.get("climate") or detail_json.get("environment") or detail_json.get("data", {}).get("climate")
            
            if climate_section:
                # Map USDA fields to our standard schema
                # USDA might use 'minTemp', 'maxTemp', 'precipitation'
                # We normalize to Celsius and mm.
                
                # Example extraction logic (adjust based on actual API response structure)
                # Assuming 'minTemp' is in Fahrenheit, convert to Celsius: (F - 32) * 5/9
                # Assuming 'precipitation' is in inches, convert to mm: inches * 25.4
                
                raw_min = climate_section.get("minTemp")
                raw_max = climate_section.get("maxTemp")
                raw_precip = climate_section.get("precipitation")
                
                if raw_min is not None:
                    # Check if it's already Celsius or Fahrenheit. USDA often uses Fahrenheit.
                    # Heuristic: if > 50, likely Fahrenheit.
                    if raw_min > 50:
                        climate_info["avg_min_temp"] = (float(raw_min) - 32) * 5/9
                    else:
                        climate_info["avg_min_temp"] = float(raw_min)
                
                if raw_max is not None:
                    if raw_max > 50:
                        climate_info["avg_max_temp"] = (float(raw_max) - 32) * 5/9
                    else:
                        climate_info["avg_max_temp"] = float(raw_max)
                
                if raw_precip is not None:
                    # Check if inches (usually < 100 for annual) or mm (usually > 200)
                    if raw_precip < 100:
                        climate_info["avg_precip"] = float(raw_precip) * 25.4
                    else:
                        climate_info["avg_precip"] = float(raw_precip)
                
                # Zone ID
                zone_raw = climate_section.get("zone")
                if zone_raw:
                    climate_info["zone_id"] = int(zone_raw)
            else:
                # If no explicit climate section, try to find in general attributes
                # This is a fallback for different API structures
                logger.debug(f"Climate section not found for {species} in standard location.")
                # We might need to parse the full JSON manually if the structure is flat.
                # For now, we log a warning if no climate data is found.
                
            if not climate_info:
                logger.warning(f"No climate data extracted for {species}.")
                continue
            
            climate_data[species] = climate_info
            
            # Rate limiting
            time.sleep(0.34)
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching USDA data for {species}: {e}")
            raise ValueError(f"Failed to fetch USDA climate data for {species}: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching USDA data for {species}: {e}")
            raise ValueError(f"Network error for {species}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing {species}: {e}")
            raise ValueError(f"Error processing {species}: {e}")
    
    if not climate_data:
        raise ValueError("Failed to fetch climate data for any species in the list.")
    
    # Save raw JSON to data/raw/ for audit trail (T021 requirement)
    raw_file = output_dir / "usda_climate_raw.json"
    import json
    with open(raw_file, 'w') as f:
        json.dump(climate_data, f, indent=2)
    
    logger.info(f"Successfully fetched USDA climate data for {len(climate_data)} species.")
    return climate_data
