import os
import subprocess
import csv
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

# Import existing models to ensure type compatibility if needed
# from src.models.genomic_feature import GenomicFeature

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """Container for extraction results."""
    isolate_id: str
    feature_type: str
    feature_id: str
    presence_binary: int
    pwm_count: int
    source: str
    raw_data: Dict[str, Any] = field(default_factory=dict)

def get_hmm_db_path() -> Path:
    """Return the path to the HMM database file."""
    # Assuming HMMs are stored in data/raw or a specific location relative to project
    # Based on T017 context, we look for pre-built HMM DBs
    base_path = Path("data/raw")
    if not base_path.exists():
        base_path = Path("data/processed")
    
    # Look for common HMM DB names
    candidates = [base_path / "virulence.hmm", base_path / "phibase.hmm", base_path / "pfam.hmm"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    
    # Fallback: raise error if not found (fail loudly)
    raise FileNotFoundError(
        f"Could not find HMM database in {base_path}. "
        "Expected one of: virulence.hmm, phibase.hmm, pfam.hmm. "
        "Please run the download/extract pipeline to generate these."
    )

def get_pwm_db_path() -> Path:
    """Return the path to the PWM (MEME format) database file."""
    base_path = Path("data/raw")
    if not base_path.exists():
        base_path = Path("data/processed")
    
    # Look for MEME format PWM files
    candidates = [base_path / "transcription_factors.meme", base_path / "pwm.meme", base_path / "tfbs.meme"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    
    # If not found, check if we can fetch a standard one or raise
    # For now, fail loudly as per data hygiene rules
    raise FileNotFoundError(
        f"Could not find PWM database in {base_path}. "
        "Expected one of: transcription_factors.meme, pwm.meme, tfbs.meme. "
        "This file should contain Position Weight Matrices in MEME format."
    )

def run_hmmsearch(genome_path: Path, hmm_db_path: Path, output_path: Path) -> bool:
    """
    Run hmmsearch against a genome assembly using an HMM database.
    
    Args:
        genome_path: Path to the genome FASTA file.
        hmm_db_path: Path to the HMM database file.
        output_path: Path where the hmmsearch output will be written.
        
    Returns:
        True if successful, False otherwise.
    """
    if not genome_path.exists():
        raise FileNotFoundError(f"Genome file not found: {genome_path}")
    if not hmm_db_path.exists():
        raise FileNotFoundError(f"HMM database not found: {hmm_db_path}")
    
    cmd = [
        "hmmsearch",
        "--tblout", str(output_path),
        "--noali",
        str(hmm_db_path),
        str(genome_path)
    ]
    
    logger.info(f"Running HMMsearch: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stderr:
            logger.warning(f"hmmsearch stderr: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"hmmsearch failed with code {e.returncode}: {e.stderr}")
        raise

def load_pwm_profiles(pwm_path: Path) -> List[Dict[str, Any]]:
    """
    Load PWM profiles from a MEME format file.
    
    Args:
        pwm_path: Path to the MEME format PWM file.
        
    Returns:
        List of dictionaries containing profile information.
    """
    if not pwm_path.exists():
        raise FileNotFoundError(f"PWM file not found: {pwm_path}")
    
    profiles = []
    current_profile = {}
    
    with open(pwm_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("MEME version"):
                continue
            elif line.startswith("ALPHABET"):
                current_profile['alphabet'] = line.split()[-1]
            elif line.startswith("strands"):
                current_profile['strands'] = line.split()[-1]
            elif line.startswith("Background letter frequencies"):
                continue
            elif line.startswith("MOTIF"):
                if current_profile:
                    profiles.append(current_profile)
                parts = line.split()
                current_profile = {'id': parts[1], 'letter_probabilities': []}
            elif line.startswith("     A"):
                # Parse probability matrix rows
                parts = line.split()
                if len(parts) >= 5: # A, C, G, T (or similar)
                    current_profile['letter_probabilities'].append({
                        'A': float(parts[1]),
                        'C': float(parts[2]),
                        'G': float(parts[3]),
                        'T': float(parts[4])
                    })
            elif line.startswith("    A"):
                 # Handle indented format variations
                 parts = line.split()
                 if len(parts) >= 5:
                     current_profile['letter_probabilities'].append({
                         'A': float(parts[1]),
                         'C': float(parts[2]),
                         'G': float(parts[3]),
                         'T': float(parts[4])
                     })
            elif line.startswith("END MOTIF"):
                if current_profile:
                    profiles.append(current_profile)
                    current_profile = {}
    
    if current_profile:
        profiles.append(current_profile)
        
    logger.info(f"Loaded {len(profiles)} PWM profiles from {pwm_path}")
    return profiles

def parse_meme_pwm(pwm_content: str) -> List[Dict[str, float]]:
    """
    Parse the probability matrix from MEME PWM content.
    
    Args:
        pwm_content: The content of a single motif block from MEME file.
        
    Returns:
        List of dictionaries with nucleotide probabilities per position.
    """
    # This is a simplified parser; a robust one would handle all MEME variations
    matrix = []
    lines = pwm_content.split('\n')
    for line in lines:
        if line.startswith("     ") or line.startswith("    "):
            parts = line.split()
            if len(parts) >= 5:
                try:
                    row = {
                        'A': float(parts[1]),
                        'C': float(parts[2]),
                        'G': float(parts[3]),
                        'T': float(parts[4])
                    }
                    matrix.append(row)
                except ValueError:
                    continue
    return matrix

def count_pwm_sites(genome_path: Path, pwm_profiles: List[Dict[str, Any]], 
                    threshold: float = 0.8) -> Dict[str, int]:
    """
    Count transcription factor binding sites using Position Weight Matrices.
    
    This function scans the genome sequence against the provided PWM profiles
    and counts occurrences where the log-odds score exceeds the threshold.
    
    Args:
        genome_path: Path to the genome FASTA file.
        pwm_profiles: List of PWM profile dictionaries.
        threshold: Minimum score threshold for a match (default 0.8).
        
    Returns:
        Dictionary mapping profile ID to count of matching sites.
    """
    if not genome_path.exists():
        raise FileNotFoundError(f"Genome file not found: {genome_path}")
    
    counts = {profile['id']: 0 for profile in pwm_profiles}
    
    # Read genome sequence
    sequence = ""
    with open(genome_path, 'r') as f:
        for line in f:
            if line.startswith('>'):
                continue
            sequence += line.strip().upper()
    
    if not sequence:
        raise ValueError(f"Empty sequence found in {genome_path}")
    
    logger.info(f"Scanning {len(sequence)} bp genome against {len(pwm_profiles)} PWMs")
    
    # Simple scoring function (log-odds)
    # In a real implementation, we would use a proper PWM scoring library
    # Here we implement a basic version for demonstration
    for profile in pwm_profiles:
        motif_id = profile['id']
        matrix = profile.get('letter_probabilities', [])
        if not matrix:
            continue
        
        motif_len = len(matrix)
        if motif_len == 0:
            continue
            
        count = 0
        # Slide window across genome
        for i in range(len(sequence) - motif_len + 1):
            window = sequence[i:i+motif_len]
            score = 0.0
            
            # Calculate log-odds score
            for j, nucleotide in enumerate(window):
                if nucleotide in ['A', 'C', 'G', 'T'] and j < len(matrix):
                    prob = matrix[j].get(nucleotide, 0.01) # Avoid log(0)
                    # Background probability assumption (0.25 for each)
                    bg_prob = 0.25
                    if prob > 0:
                        score += prob / bg_prob # Simplified scoring
            
            # Normalize score (simplified)
            normalized_score = score / motif_len
            
            if normalized_score >= threshold:
                count += 1
        
        counts[motif_id] = count
        logger.debug(f"Found {count} sites for {motif_id}")
    
    return counts

def extract_virulence_features(genome_path: Path, isolate_id: str, 
                               hmm_db_path: Optional[Path] = None,
                               pwm_db_path: Optional[Path] = None) -> List[ExtractionResult]:
    """
    Main function to extract virulence features from a genome.
    
    This function runs HMMsearch for virulence genes and PWM scanning for
    transcription factor binding sites, returning a list of GenomicFeature-like
    objects.
    
    Args:
        genome_path: Path to the genome FASTA file.
        isolate_id: Unique identifier for the isolate.
        hmm_db_path: Optional path to HMM database. If None, auto-discovered.
        pwm_db_path: Optional path to PWM database. If None, auto-discovered.
        
    Returns:
        List of ExtractionResult objects containing feature data.
    """
    results = []
    
    # 1. HMMsearch for virulence genes
    try:
        if hmm_db_path is None:
            hmm_db_path = get_hmm_db_path()
        
        temp_output = Path("data/raw/hmmsearch_results.tmp")
        run_hmmsearch(genome_path, hmm_db_path, temp_output)
        
        # Parse HMMsearch output
        with open(temp_output, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 10:
                    # HMMsearch output format: target name, accession, query name, ... e-value, score
                    feature_id = parts[0]
                    e_value = float(parts[4])
                    score = float(parts[5])
                    
                    # Threshold for presence (e.g., e-value < 1e-5)
                    presence = 1 if e_value < 1e-5 else 0
                    
                    if presence == 1:
                        results.append(ExtractionResult(
                            isolate_id=isolate_id,
                            feature_type="hmm_gene",
                            feature_id=feature_id,
                            presence_binary=presence,
                            pwm_count=0,
                            source=str(hmm_db_path),
                            raw_data={"e_value": e_value, "score": score}
                        ))
        
        temp_output.unlink(missing_ok=True)
        
    except FileNotFoundError as e:
        logger.warning(f"HMMsearch skipped: {e}")
    except Exception as e:
        logger.error(f"Error during HMMsearch: {e}")
    
    # 2. PWM scanning for transcription factor binding sites
    try:
        if pwm_db_path is None:
            pwm_db_path = get_pwm_db_path()
        
        profiles = load_pwm_profiles(pwm_db_path)
        pwm_counts = count_pwm_sites(genome_path, profiles)
        
        for feature_id, count in pwm_counts.items():
            if count > 0:
                results.append(ExtractionResult(
                    isolate_id=isolate_id,
                    feature_type="pwm_site",
                    feature_id=feature_id,
                    presence_binary=1 if count > 0 else 0,
                    pwm_count=count,
                    source=str(pwm_db_path),
                    raw_data={"count": count}
                ))
                
    except FileNotFoundError as e:
        logger.warning(f"PWM scanning skipped: {e}")
    except Exception as e:
        logger.error(f"Error during PWM scanning: {e}")
        
    return results

def main():
    """
    Main entry point for the extraction script.
    
    This function processes all genomes in data/raw/*.fna and writes
    the extracted features to data/processed/extracted_features.csv.
    """
    logging.basicConfig(level=logging.INFO)
    
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = processed_dir / "extracted_features.csv"
    
    # Find all genome files
    genome_files = list(raw_dir.glob("*.fna")) + list(raw_dir.glob("*.fasta")) + list(raw_dir.glob("*.fa"))
    
    if not genome_files:
        logger.error("No genome files found in data/raw/")
        return
    
    logger.info(f"Found {len(genome_files)} genome files to process")
    
    all_results = []
    
    for genome_path in genome_files:
        # Derive isolate ID from filename
        isolate_id = genome_path.stem
        logger.info(f"Processing {isolate_id} from {genome_path}")
        
        try:
            results = extract_virulence_features(genome_path, isolate_id)
            all_results.extend(results)
        except Exception as e:
            logger.error(f"Failed to process {isolate_id}: {e}")
    
    # Write results to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['isolate_id', 'feature_type', 'feature_id', 
                       'presence_binary', 'pwm_count', 'source'])
        
        for res in all_results:
            writer.writerow([
                res.isolate_id, res.feature_type, res.feature_id,
                res.presence_binary, res.pwm_count, res.source
            ])
    
    logger.info(f"Extracted {len(all_results)} features to {output_file}")

if __name__ == "__main__":
    main()