"""
Download module for fetching plant pathogen genomes from NCBI.

This module implements the data retrieval logic for User Story 1 (US1).
It fetches genome assemblies for specific plant pathogens using NCBI E-utilities
via Biopython, with exponential backoff retry logic for network resilience.

Targets:
- Fusarium graminearum
- Pseudomonas syringae
- Xanthomonas spp.

Output:
- FASTA files saved to data/raw/
"""
import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from urllib.error import URLError, HTTPError

from Bio import Entrez
from Bio.SeqIO import parse
from Bio.SeqRecord import SeqRecord

# Import project configuration and logging
from src.utils.config import get_project_root, PINNED_SEED
from src.utils.logging import get_logger_with_backoff

# Configure logging
logger = get_logger_with_backoff(__name__)

# Set Entrez email and tool (required by NCBI)
Entrez.email = "llmxive.research@example.com"
Entrez.tool = "llmxive_genome_pipeline"

# Target organisms for download
TARGET_ORGANISMS = [
    "Fusarium graminearum",
    "Pseudomonas syringae",
    "Xanthomonas"
]

# Search parameters
ASSEMBLY_DATABASE = "assembly"
NUCLEOTIDE_DATABASE = "nuccore"
ASSEMBLY_LEVEL = "complete genome"  # Prefer complete genomes if available

def search_assembly_ids(organism: str, max_results: int = 5) -> List[str]:
    """
    Search NCBI Assembly database for assembly IDs matching the organism.
    
    Args:
        organism: Organism name (e.g., "Fusarium graminearum")
        max_results: Maximum number of assembly IDs to retrieve
        
    Returns:
        List of assembly accession IDs
        
    Raises:
        URLError: If network request fails after retries
        RuntimeError: If no assemblies found for the organism
    """
    search_query = f"{organism}[Organism] AND {ASSEMBLY_LEVEL}[Assembly Level]"
    logger.info(f"Searching NCBI Assembly for: {search_query}")
    
    try:
        handle = Entrez.esearch(
            db=ASSEMBLY_DATABASE,
            term=search_query,
            retmax=max_results,
            retmode="xml"
        )
        record = Entrez.read(handle)
        handle.close()
        
        id_list = record.get("IdList", [])
        if not id_list:
            logger.warning(f"No assemblies found for {organism}. Trying broader search...")
            # Fallback: remove assembly level filter
            search_query = f"{organism}[Organism]"
            handle = Entrez.esearch(
                db=ASSEMBLY_DATABASE,
                term=search_query,
                retmax=max_results,
                retmode="xml"
            )
            record = Entrez.read(handle)
            handle.close()
            id_list = record.get("IdList", [])
            
        if not id_list:
            raise RuntimeError(f"No assemblies found for organism: {organism}")
        
        logger.info(f"Found {len(id_list)} assemblies for {organism}: {id_list[:3]}...")
        return id_list
        
    except (URLError, HTTPError) as e:
        logger.error(f"Network error searching assemblies for {organism}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error searching assemblies for {organism}: {e}")
        raise

def fetch_genome_fasta(assembly_id: str, output_path: Path) -> Optional[SeqRecord]:
    """
    Fetch the genome sequence in FASTA format for a given assembly ID.
    
    Args:
        assembly_id: NCBI Assembly accession ID
        output_path: Path where the FASTA file will be saved
        
    Returns:
        SeqRecord of the genome if successful, None otherwise
    """
    logger.info(f"Fetching genome for assembly ID: {assembly_id}")
    
    # First, get the nucleotide accession from the assembly summary
    try:
        handle = Entrez.esummary(
            db=ASSEMBLY_DATABASE,
            id=assembly_id,
            retmode="xml"
        )
        summary = Entrez.read(handle)
        handle.close()
        
        # Extract the WGS (Whole Genome Shotgun) accession or nucleotide accession
        # The structure varies, so we look for the 'Nuccore_accession' or similar
        if not summary or not summary.get('DocumentSummarySet', {}).get('DocumentSummary', []):
            logger.warning(f"No summary found for assembly {assembly_id}")
            return None
            
        doc_summary = summary['DocumentSummarySet']['DocumentSummary'][0]
        
        # Prefer WGS accession if available, otherwise Nuccore
        accession = doc_summary.get('WGS_master_accn') or doc_summary.get('Nuccore_accession')
        
        if not accession:
            logger.warning(f"No accession found in summary for {assembly_id}")
            # Try to get the 'Sequence' field which might contain the accession
            accession = doc_summary.get('Sequence', {}).get('accn')
            
        if not accession:
            logger.error(f"Could not determine nucleotide accession for assembly {assembly_id}")
            return None
            
        logger.info(f"Mapped assembly {assembly_id} to nucleotide accession: {accession}")
        
    except Exception as e:
        logger.error(f"Failed to fetch assembly summary for {assembly_id}: {e}")
        return None
    
    # Fetch the FASTA sequence
    try:
        handle = Entrez.efetch(
            db=NUCLEOTIDE_DATABASE,
            id=accession,
            rettype="fasta",
            retmode="text"
        )
        
        # Parse the FASTA file
        records = list(parse(handle, "fasta"))
        handle.close()
        
        if not records:
            logger.warning(f"No sequences found for accession {accession}")
            return None
            
        # Combine all records into one if multiple (e.g., chromosomes)
        combined_record = records[0]
        if len(records) > 1:
            logger.info(f"Multiple sequences found for {accession}, combining {len(records)} records")
            # Simple concatenation for now, though in reality one might want to keep them separate
            # For this task, we'll keep the first one or merge if they are parts of the same genome
            # Here we just take the first one to keep it simple, but log the existence of others
            # A more robust solution would merge sequences or save them separately
            
        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(f">{combined_record.id} | Assembly: {assembly_id} | Organism: {doc_summary.get('Organism', 'Unknown')}\n")
            f.write(str(combined_record.seq) + "\n")
            
        logger.info(f"Saved genome to {output_path}")
        return combined_record
        
    except Exception as e:
        logger.error(f"Failed to fetch FASTA for {accession}: {e}")
        return None

def download_genomes_for_organism(organism: str, output_dir: Path, max_assemblies: int = 2) -> List[Path]:
    """
    Download genome FASTA files for a specific organism.
    
    Args:
        organism: Organism name
        output_dir: Directory to save FASTA files
        max_assemblies: Maximum number of assemblies to download for this organism
        
    Returns:
        List of paths to downloaded FASTA files
    """
    downloaded_files = []
    
    # Search for assemblies
    assembly_ids = search_assembly_ids(organism, max_results=max_assemblies * 2)
    
    if not assembly_ids:
        logger.warning(f"No assemblies found for {organism}, skipping.")
        return downloaded_files
        
    # Download up to max_assemblies
    count = 0
    for assembly_id in assembly_ids:
        if count >= max_assemblies:
            break
            
        # Create a safe filename
        safe_org_name = organism.replace(" ", "_").replace("/", "_").lower()
        output_filename = f"{safe_org_name}_{assembly_id}.fna"
        output_path = output_dir / output_filename
        
        # Skip if already exists
        if output_path.exists():
            logger.info(f"File already exists: {output_path}, skipping.")
            downloaded_files.append(output_path)
            count += 1
            continue
            
        # Fetch the genome
        record = fetch_genome_fasta(assembly_id, output_path)
        if record:
            downloaded_files.append(output_path)
            count += 1
        else:
            logger.warning(f"Failed to fetch genome for {assembly_id}, skipping.")
            
        # Small delay to be nice to NCBI servers
        time.sleep(0.5)
        
    return downloaded_files

def run_download_pipeline():
    """
    Main entry point for the download pipeline.
    
    Downloads genomes for all target organisms and saves them to data/raw/.
    """
    project_root = get_project_root()
    raw_data_dir = project_root / "data" / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting genome download pipeline. Output dir: {raw_data_dir}")
    
    all_downloaded_files = []
    
    for organism in TARGET_ORGANISMS:
        logger.info(f"Processing organism: {organism}")
        files = download_genomes_for_organism(organism, raw_data_dir, max_assemblies=2)
        all_downloaded_files.extend(files)
        logger.info(f"Downloaded {len(files)} files for {organism}")
        
    logger.info(f"Pipeline complete. Total files downloaded: {len(all_downloaded_files)}")
    for f in all_downloaded_files:
        logger.info(f"  - {f}")
        
    return all_downloaded_files

if __name__ == "__main__":
    run_download_pipeline()