"""
Extract genomic features (virulence genes and PWM sites) from downloaded genomes.
Implements T017 (hmmsearch) and T018 (PWM counting).
"""
import os
import subprocess
import csv
import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field

from src.models.genomic_feature import GenomicFeature

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """Container for extraction results."""
    features: List[GenomicFeature] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

def get_hmm_db_path() -> Path:
    """
    Returns the path to the HMM database.
    Tries standard locations: data/raw/hmm/pfam.hmm or data/raw/hmm/phibase.hmm.
    Raises FileNotFoundError if not found.
    """
    possible_paths = [
        Path("data/raw/hmm/pfam.hmm"),
        Path("data/raw/hmm/phibase.hmm"),
        Path("data/raw/hmm/virulence.hmm"),
    ]
    for p in possible_paths:
        if p.exists():
            logger.info(f"Found HMM database at: {p}")
            return p
    
    # If not found, raise loudly as per data hygiene rules
    raise FileNotFoundError(
        f"HMM database not found in expected locations: {possible_paths}. "
        "Please download Pfam or PHI-base HMMs to data/raw/hmm/."
    )

def get_pwm_db_path() -> Path:
    """
    Returns the path to the PWM database (MEME format).
    Raises FileNotFoundError if not found.
    """
    possible_paths = [
        Path("data/raw/pwm/transcription_factors.meme"),
        Path("data/raw/pwm/pwm.meme"),
    ]
    for p in possible_paths:
        if p.exists():
            logger.info(f"Found PWM database at: {p}")
            return p

    raise FileNotFoundError(
        f"PWM database not found in expected locations: {possible_paths}. "
        "Please download MEME format PWMs to data/raw/pwm/."
    )

def run_hmmsearch(genome_path: Path, hmm_db: Path, output_e3: Path) -> List[Dict]:
    """
    Runs hmmsearch against a genome assembly using the provided HMM database.
    Parses the tabular output (-o E3) to extract hits.
    
    Args:
        genome_path: Path to the FASTA file (.fna/.fa).
        hmm_db: Path to the HMM database.
        output_e3: Path to write the E3 tabular output.
    
    Returns:
        List of hit dictionaries containing: target_name, evalue, score, query_name (genome).
    
    Raises:
        subprocess.CalledProcessError: If hmmsearch fails.
        FileNotFoundError: If hmmsearch binary is not found.
    """
    if not Path(hmm_db).exists():
        raise FileNotFoundError(f"HMM database not found: {hmm_db}")
    if not Path(genome_path).exists():
        raise FileNotFoundError(f"Genome file not found: {genome_path}")

    cmd = [
        "hmmsearch",
        "--cpu", "1",
        "-o", str(output_e3),
        "--tblout", str(output_e3.with_suffix(".tbl")), # hmmsearch usually writes table to --tblout
        str(hmm_db),
        str(genome_path)
    ]
    
    # Note: hmmsearch --tblout is the standard way to get tabular output.
    # The command above writes to output_e3 (which we treat as the .tbl file for simplicity in this impl)
    # Actually, let's be precise: --o is human readable, --tblout is machine readable.
    # We only need the machine readable one for parsing.
    
    tbl_output = output_e3.with_suffix(".tbl")
    cmd = [
        "hmmsearch",
        "--cpu", "1",
        "--tblout", str(tbl_output),
        str(hmm_db),
        str(genome_path)
    ]

    try:
        # Check if hmmsearch exists
        subprocess.run(["which", "hmmsearch"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "hmmsearch binary not found. Please install HMMER (e.g., 'conda install -c bioconda hmmer' or 'apt-get install hmmer')."
        )

    logger.info(f"Running hmmsearch: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    hits = []
    if not tbl_output.exists():
        raise RuntimeError(f"hmmsearch did not produce output file: {tbl_output}")

    with open(tbl_output, 'r') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 10:
                # Standard hmmsearch --tblout format:
                # target name, accession, query name, accession, E-value, score, bias, ...
                # Index 0: target (HMM profile name)
                # Index 4: E-value
                # Index 5: Score
                target_name = parts[0]
                try:
                    evalue = float(parts[4])
                    score = float(parts[5])
                except (ValueError, IndexError):
                    continue
                
                hits.append({
                    "target_name": target_name,
                    "evalue": evalue,
                    "score": score,
                    "genome_path": str(genome_path)
                })
    
    return hits

def load_pwm_profiles(pwm_db: Path) -> Dict[str, List[float]]:
    """
    Loads PWM profiles from a MEME-format file.
    Returns a dict mapping motif name to a list of probabilities (or counts).
    """
    if not pwm_db.exists():
        raise FileNotFoundError(f"PWM database not found: {pwm_db}")

    profiles = {}
    current_motif = None
    current_alphabet = "ACGT"
    current_matrix = []
    
    with open(pwm_db, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("MEME version"):
                continue
            elif line.startswith("ALPHABET"):
                # Parse alphabet if needed, default to ACGT
                parts = line.split()
                if len(parts) > 1:
                    current_alphabet = "".join(parts[1:])
            elif line.startswith("Motif"):
                # Save previous if exists
                if current_motif and current_matrix:
                    profiles[current_motif] = current_matrix
                current_motif = line.split()[1] # "Motif MOTIF_ID"
                current_matrix = []
            elif line.startswith("letter-probability"):
                # Start of matrix
                # Format: letter-probability matrix: alength=W w=123 ...
                # We just need to read the next W lines
                pass
            elif line.startswith("  ") or (line[0].isdigit() or line[0].isalpha()):
                # Data line for matrix
                if current_motif and not line.startswith("letter-probability"):
                    parts = line.split()
                    if len(parts) == len(current_alphabet):
                        try:
                            row = [float(x) for x in parts]
                            current_matrix.append(row)
                        except ValueError:
                            continue
    
    if current_motif and current_matrix:
        profiles[current_motif] = current_matrix
    
    logger.info(f"Loaded {len(profiles)} PWM profiles.")
    return profiles

def parse_meme_pwm(pwm_db: Path) -> Dict[str, List[List[float]]]:
    """
    Alternative parser for MEME files if load_pwm_profiles needs more robustness.
    Returns dict of motif_name -> list of lists (rows of probabilities).
    """
    return load_pwm_profiles(pwm_db)

def count_pwm_sites(genome_path: Path, pwm_db: Path, threshold: float = 0.8) -> List[Dict]:
    """
    Counts transcription factor binding sites using Position Weight Matrices.
    Scans the genome sequence for matches to each PWM.
    
    Args:
        genome_path: Path to FASTA file.
        pwm_db: Path to MEME file.
        threshold: Minimum probability score to count as a site.
    
    Returns:
        List of dicts: {motif_id, count, genome_path}.
    """
    if not genome_path.exists():
        raise FileNotFoundError(f"Genome file not found: {genome_path}")
    
    profiles = load_pwm_profiles(pwm_db)
    if not profiles:
        logger.warning("No PWM profiles loaded.")
        return []

    # Simple FASTA reader
    def read_fasta(path: Path):
        seq = ""
        header = ""
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('>'):
                    if header:
                        yield header, seq
                    header = line[1:].split()[0]
                    seq = ""
                else:
                    seq += line.upper()
        if header:
            yield header, seq

    results = []
    for motif_id, matrix in profiles.items():
        count = 0
        # Matrix is list of rows [A, C, G, T] probabilities
        # We need to map ACGT to indices
        alphabet = "ACGT" # Assuming standard, could be dynamic
        if len(matrix) > 0 and len(matrix[0]) != 4:
            # Try to infer alphabet from first row length or assume ACGT
            # For simplicity, assume ACGT order if length is 4
            pass
        
        motif_len = len(matrix)
        
        for header, seq in read_fasta(genome_path):
            # Slide window
            for i in range(len(seq) - motif_len + 1):
                window = seq[i:i+motif_len]
                if 'N' in window:
                    continue
                
                score = 0.0
                valid = True
                for j, base in enumerate(window):
                    if base not in alphabet:
                        valid = False
                        break
                    idx = alphabet.index(base)
                    if idx < len(matrix[j]):
                        score += matrix[j][idx]
                    else:
                        valid = False
                        break
                
                if valid:
                    # Normalize or threshold? 
                    # Simple sum of probabilities. If sum >= threshold * motif_len?
                    # Or average probability.
                    avg_prob = score / motif_len
                    if avg_prob >= threshold:
                        count += 1
        
        results.append({
            "motif_id": motif_id,
            "count": count,
            "genome_path": str(genome_path)
        })
    
    return results

def extract_virulence_features(genomes_dir: Path, hmm_db: Path, pwm_db: Path, output_path: Path) -> ExtractionResult:
    """
    Orchestrates the extraction of virulence features:
    1. Run hmmsearch on all genomes in genomes_dir.
    2. Run PWM scanning on all genomes.
    3. Compile results into GenomicFeature objects.
    4. Write summary CSV.
    
    Args:
        genomes_dir: Directory containing .fna/.fa files.
        hmm_db: Path to HMM database.
        pwm_db: Path to PWM database.
        output_path: Path to write the CSV output.
    
    Returns:
        ExtractionResult containing list of features and stats.
    """
    if not genomes_dir.exists():
        raise FileNotFoundError(f"Genomes directory not found: {genomes_dir}")
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    features = []
    stats = {
        "genomes_processed": 0,
        "hmm_hits": 0,
        "pwm_sites": 0,
        "output_file": str(output_path)
    }
    
    genome_files = list(ge for ge in genomes_dir.glob("*.fna") if ge.is_file()) + \
                   list(ge for ge in genomes_dir.glob("*.fa") if ge.is_file())
    
    if not genome_files:
        raise FileNotFoundError(f"No .fna or .fa files found in {genomes_dir}")
    
    logger.info(f"Found {len(genome_files)} genome files.")
    
    # Temporary directory for hmmsearch outputs
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        for genome_file in genome_files:
            genome_id = genome_file.stem
            stats["genomes_processed"] += 1
            logger.info(f"Processing {genome_id}...")
            
            # 1. HMM Search
            try:
                hmm_output = tmpdir_path / f"{genome_id}_hmm.tbl"
                hits = run_hmmsearch(genome_file, hmm_db, hmm_output)
                stats["hmm_hits"] += len(hits)
                
                for hit in hits:
                    feature = GenomicFeature(
                        feature_id=f"{hit['target_name']}_{genome_id}",
                        type="hmm_gene_presence",
                        presence_binary=1,
                        pwm_count=hit['score'], # Using score as a proxy for "strength"
                        source="hmmsearch"
                    )
                    features.append(feature)
            except Exception as e:
                logger.error(f"Error running hmmsearch on {genome_id}: {e}")
                # Continue processing other genomes
            
            # 2. PWM Counting
            try:
                pwm_results = count_pwm_sites(genome_file, pwm_db)
                stats["pwm_sites"] += sum(r['count'] for r in pwm_results)
                
                for res in pwm_results:
                    if res['count'] > 0:
                        feature = GenomicFeature(
                            feature_id=f"{res['motif_id']}_{genome_id}",
                            type="pwm_site_count",
                            presence_binary=1 if res['count'] > 0 else 0,
                            pwm_count=res['count'],
                            source="pwm_scan"
                        )
                        features.append(feature)
            except Exception as e:
                logger.error(f"Error scanning PWMs on {genome_id}: {e}")
    
    # Write CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["feature_id", "type", "presence_binary", "pwm_count", "source"])
        for feat in features:
            writer.writerow([feat.feature_id, feat.type, feat.presence_binary, feat.pwm_count, feat.source])
    
    logger.info(f"Extraction complete. Wrote {len(features)} features to {output_path}")
    return ExtractionResult(features=features, stats=stats)

def main():
    """Main entry point for the extract script."""
    import argparse
    import tempfile
    
    parser = argparse.ArgumentParser(description="Extract virulence features from genomes.")
    parser.add_argument("--genomes", type=str, default="data/raw", help="Directory containing genome FASTA files.")
    parser.add_argument("--output", type=str, default="data/processed/genomic_features.csv", help="Output CSV path.")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        hmm_db = get_hmm_db_path()
        pwm_db = get_pwm_db_path()
        
        result = extract_virulence_features(
            genomes_dir=Path(args.genomes),
            hmm_db=hmm_db,
            pwm_db=pwm_db,
            output_path=Path(args.output)
        )
        
        print(f"Extraction successful. Stats: {result.stats}")
        
    except FileNotFoundError as e:
        logger.critical(f"Data source missing: {e}")
        raise
    except Exception as e:
        logger.critical(f"Extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()
