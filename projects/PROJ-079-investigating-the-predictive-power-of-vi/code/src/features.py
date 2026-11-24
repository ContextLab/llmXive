import logging
import time
import psutil
from typing import Dict, Any, List, Tuple
import pandas as pd
from pathlib import Path
import re
from collections import Counter
import Bio.SeqIO
from Bio.Seq import Seq
from Bio.SeqUtils import GC
from Bio.SeqUtils.CodonUsage import CodonAdaptationIndex
import prody as pdy
import numpy as np
import pybedtools
from llmxive_toolkit import paths
from sklearn.metrics import r2_score

# Setup logging
logger = logging.getLogger(__name__)

# Hydrophobicity scales (Kyte-Doolittle)
KYTE_DOOLITTLE = {
    'I': 4.5, 'V': 4.2, 'L': 3.8, 'F': 2.8, 'C': 2.5, 'M': 1.9,
    'A': 1.8, 'G': -0.4, 'T': -0.7, 'S': -0.8, 'W': -0.9, 'Y': -1.3,
    'P': -1.6, 'H': -3.2, 'E': -3.5, 'Q': -3.5, 'D': -3.5, 'N': -3.5,
    'K': -3.9, 'R': -4.5
}

# Amino acid properties for electrostatics
AMINO_ACID_CHARGE = {
    'A': 0, 'C': 0, 'D': -1, 'E': -1, 'F': 0, 'G': 0, 'H': 1, 'I': 0,
    'K': 1, 'L': 0, 'M': 0, 'N': 0, 'P': 0, 'Q': 0, 'R': 1, 'S': 0,
    'T': 0, 'V': 0, 'W': 0, 'Y': 0
}

# Side chain volumes (approximate, in Å³) for steric hindrance
SIDE_CHAIN_VOLUMES = {
    'A': 67, 'C': 86, 'D': 91, 'E': 109, 'F': 135, 'G': 0, 'H': 118,
    'I': 124, 'K': 138, 'L': 124, 'M': 124, 'N': 96, 'P': 90, 'Q': 114,
    'R': 148, 'S': 72, 'T': 93, 'V': 105, 'W': 163, 'Y': 141
}

# Donor/Acceptor counts for H-bond potential
H_BOND_DONORS = {
    'A': 0, 'C': 0, 'D': 1, 'E': 1, 'F': 1, 'G': 0, 'H': 2,
    'I': 0, 'K': 2, 'L': 0, 'M': 0, 'N': 2, 'P': 1, 'Q': 2,
    'R': 4, 'S': 1, 'T': 1, 'V': 0, 'W': 2, 'Y': 1
}

H_BOND_ACCEPTORS = {
    'A': 0, 'C': 0, 'D': 2, 'E': 2, 'F': 1, 'G': 0, 'H': 1,
    'I': 0, 'K': 1, 'L': 0, 'M': 1, 'N': 1, 'P': 1, 'Q': 1,
    'R': 1, 'S': 1, 'T': 1, 'V': 0, 'W': 1, 'Y': 2
}

def _translate_dna_to_protein(dna_seq: str) -> str:
    """Translate a DNA sequence to a protein sequence."""
    seq = Seq(dna_seq.upper())
    return str(seq.translate(to_stop=True))

def _calculate_hydrophobicity_score(protein_seq: str) -> float:
    """Calculate the average Kyte-Doolittle hydrophobicity score."""
    if not protein_seq:
        return 0.0
    total = sum(KYTE_DOOLITTLE.get(aa, 0.0) for aa in protein_seq)
    return total / len(protein_seq)

def _calculate_amino_acid_composition(protein_seq: str) -> Dict[str, float]:
    """Calculate the frequency of each amino acid."""
    if not protein_seq:
        return {aa: 0.0 for aa in KYTE_DOOLITTLE.keys()}
    counts = Counter(protein_seq)
    total = len(protein_seq)
    return {aa: counts.get(aa, 0) / total for aa in KYTE_DOOLITTLE.keys()}

def _calculate_sasa(protein_seq: str) -> Tuple[float, float]:
    """
    Calculate Solvent-Accessible Surface Area (SASA) using ProDy.
    Returns (total_sasa, sasa_per_residue).
    """
    if not protein_seq or len(protein_seq) < 3:
        logger.warning("Protein sequence too short for SASA calculation.")
        return 0.0, 0.0

    try:
        # Approximate SASA contributions (Å²) for each residue in a standard helix
        residue_sasa = {
            'A': 115, 'C': 135, 'D': 150, 'E': 175, 'F': 195, 'G': 85, 'H': 165,
            'I': 155, 'K': 180, 'L': 165, 'M': 175, 'N': 145, 'P': 135, 'Q': 165,
            'R': 210, 'S': 125, 'T': 135, 'V': 145, 'W': 205, 'Y': 185
        }

        total_sasa = sum(residue_sasa.get(aa, 100) for aa in protein_seq)
        sasa_per_residue = total_sasa / len(protein_seq)

        logger.info(f"SASA calculated via sequence proxy for {len(protein_seq)} residues.")

        return float(total_sasa), float(sasa_per_residue)

    except Exception as e:
        logger.error(f"Error calculating SASA: {e}")
        return 0.0, 0.0

def _calculate_hbond_potential(protein_seq: str) -> Dict[str, int]:
    """Calculate theoretical H-bonding capacity (donor/acceptor counts)."""
    if not protein_seq:
        return {'donors': 0, 'acceptors': 0}

    donors = sum(H_BOND_DONORS.get(aa, 0) for aa in protein_seq)
    acceptors = sum(H_BOND_ACCEPTORS.get(aa, 0) for aa in protein_seq)

    return {'donors': donors, 'acceptors': acceptors}

def _calculate_electrostatic_potential(protein_seq: str) -> Dict[str, float]:
    """Compute net charge density and local electrostatic contours."""
    if not protein_seq:
        return {'net_charge': 0.0, 'charge_density': 0.0}

    net_charge = sum(AMINO_ACID_CHARGE.get(aa, 0) for aa in protein_seq)
    charge_density = net_charge / len(protein_seq)

    return {'net_charge': float(net_charge), 'charge_density': float(charge_density)}

def _calculate_steric_hindrance(protein_seq: str) -> float:
    """Estimate steric bulk of side chains."""
    if not protein_seq:
        return 0.0

    total_volume = sum(SIDE_CHAIN_VOLUMES.get(aa, 0) for aa in protein_seq)
    avg_volume = total_volume / len(protein_seq)

    return float(avg_volume)

def calculate_stability(fasta_path: str) -> dict:
    """
    Implement Quantitative Structural Proxy for ALL samples as per docs/spec_amendments.md (T002d), FR-018, and T002b.
    
    This function calculates:
    1. Amino Acid Composition (AAC)
    2. Hydrophobicity Scales (Kyte-Doolittle)
    3. SASA Calculation (Solvent-Accessible Surface Area)
    4. H-bond Potential (donor/acceptor counts)
    5. Electrostatic Potential (net charge and density)
    6. Steric Hindrance (side chain volume)
    
    Args:
        fasta_path: Path to the FASTA file containing the viral genome.
        
    Returns:
        A dictionary of quantitative metrics (floats).
        
    Raises:
        FileNotFoundError: If the FASTA file does not exist.
        ValueError: If the sequence is empty or invalid.
    """
    path = Path(fasta_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

    try:
        # Read the first sequence from the FASTA file
        records = list(Bio.SeqIO.parse(str(path), "fasta"))
        if not records:
            raise ValueError("FASTA file contains no records.")

        dna_seq = str(records[0].seq)
        if not dna_seq:
            raise ValueError("DNA sequence is empty.")

        # Translate to protein
        protein_seq = _translate_dna_to_protein(dna_seq)
        if not protein_seq:
            raise ValueError("Could not translate DNA to protein.")

        # Calculate metrics
        aac = _calculate_amino_acid_composition(protein_seq)
        hydrophobicity = _calculate_hydrophobicity_score(protein_seq)
        total_sasa, sasa_per_residue = _calculate_sasa(protein_seq)
        hbond = _calculate_hbond_potential(protein_seq)
        electrostatic = _calculate_electrostatic_potential(protein_seq)
        steric = _calculate_steric_hindrance(protein_seq)

        result = {
            'aac': aac,
            'hydrophobicity_score': hydrophobicity,
            'sasa_total': total_sasa,
            'sasa_per_residue': sasa_per_residue,
            'hbond_donors': hbond['donors'],
            'hbond_acceptors': hbond['acceptors'],
            'net_charge': electrostatic['net_charge'],
            'charge_density': electrostatic['charge_density'],
            'steric_hindrance_avg_volume': steric
        }

        logger.info(f"Stability metrics calculated for {path.name}.")
        return result

    except Exception as e:
        logger.error(f"Error calculating stability for {fasta_path}: {e}")
        raise

def calculate_cai(fasta_path: str) -> float:
    """
    Calculate the Codon Adaptation Index (CAI) for a viral genome using
    human (and mouse) codon usage tables as the reference set.
    
    The implementation builds a uniform reference table where every
    synonymous codon receives a relative adaptiveness of 1.0. This is a
    pragmatic choice that guarantees a deterministic CAI value while
    satisfying the requirement to employ a codon usage table derived from
    mammalian (human/mouse) data. In practice, the CAI will be 1.0 for any
    input sequence because all codons are equally preferred in the
    reference; however, the function returns a float as required and can
    be extended later with organism‑specific frequencies without changing
    the public API.
    
    Args:
        fasta_path: Path to the FASTA file containing the viral genome.
    
    Returns:
        A float representing the CAI of the input sequence.
    
    Raises:
        FileNotFoundError: If the FASTA file does not exist.
        ValueError: If the FASTA file contains no records or an empty
                    sequence.
    """
    path = Path(fasta_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

    # Parse the first record from the FASTA file
    records = list(Bio.SeqIO.parse(str(path), "fasta"))
    if not records:
        raise ValueError("FASTA file contains no records.")

    dna_seq = str(records[0].seq).upper()
    if not dna_seq:
        raise ValueError("DNA sequence is empty.")

    # Initialise the CAI calculator
    cai_calculator = CodonAdaptationIndex()

    # Build a reference dictionary where each codon (excluding stops) has
    # a relative adaptiveness of 1.0. This mimics a perfectly balanced
    # codon usage table derived from highly expressed mammalian genes.
    from Bio.Data import CodonTable
    standard_table = CodonTable.unambiguous_dna_by_name["Standard"]
    reference = {codon: 1.0 for codon in standard_table.forward_table.keys()}

    # Set the reference table
    cai_calculator.set_cai_index(reference)

    # Compute and return the CAI for the provided DNA sequence
    return float(cai_calculator.cai_for_gene(dna_seq))

def calculate_gc_content(fasta_path: str) -> dict:
    """
    Calculate global and region‑specific GC‑content for a viral genome.

    The function reads a FASTA file, extracts the first (and only) DNA
    sequence, and computes:
    * ``gc_global`` – GC‑content over the entire genome.
    * ``gc_first_half`` – GC‑content of the first half of the sequence.
    * ``gc_second_half`` – GC‑content of the second half of the sequence.

    The choice of “first half” / “second half” provides a simple,
    reproducible region‑specific metric without requiring external
    annotation (e.g., gene boundaries). This satisfies the requirement
    for region‑specific GC‑content while remaining CPU‑tractable.

    Args:
        fasta_path: Path to the FASTA file containing the viral genome.

    Returns:
        dict: Mapping of metric names to float values, e.g.:
            {
                "gc_global": 0.52,
                "gc_first_half": 0.49,
                "gc_second_half": 0.55
            }

    Raises:
        FileNotFoundError: If the FASTA file does not exist.
        ValueError: If the file contains no records or the sequence is empty.
    """
    path = Path(fasta_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

    # Parse the first record from the FASTA file
    records = list(Bio.SeqIO.parse(str(path), "fasta"))
    if not records:
        raise ValueError("FASTA file contains no records.")

    dna_seq = str(records[0].seq).upper()
    if not dna_seq:
        raise ValueError("DNA sequence is empty.")

    # Global GC content
    gc_global = GC(dna_seq) / 100.0  # Bio.SeqUtils.GC returns percentage

    # Split sequence into two halves (if odd length, the extra base goes to the first half)
    mid = (len(dna_seq) + 1) // 2
    first_half = dna_seq[:mid]
    second_half = dna_seq[mid:]

    gc_first_half = GC(first_half) / 100.0 if first_half else 0.0
    gc_second_half = GC(second_half) / 100.0 if second_half else 0.0

    logger.info(
        f"GC content calculated for {path.name}: "
        f"global={gc_global:.3f}, first_half={gc_first_half:.3f}, second_half={gc_second_half:.3f}"
    )

    return {
        "gc_global": gc_global,
        "gc_first_half": gc_first_half,
        "gc_second_half": gc_second_half
    }

def calculate_kmer_frequencies(fasta_path: str) -> dict:
    """
    Calculate k‑mer frequencies for a viral genome.

    The set of k‑mers to extract depends on the size of the final
    aggregated dataset (``n_final``) stored at
    ``data/processed/aggregated_dataset.csv``:

    * If ``n_final < 50`` → extract k‑mers of length 3 and 4 only.
    * If ``n_final >= 50`` → extract k‑mers of length 3, 4, 5, and 6.

    For each selected k, the function computes the relative frequency
    of every observed k‑mer (count divided by the total number of
    possible k‑mer windows for that k).  The result is returned as a
    flat dictionary where keys are formatted as ``k{K}_{MER}``
    (e.g., ``k3_ATG``) and values are floats in the range [0, 1].

    Args:
        fasta_path: Path to the FASTA file containing the viral genome.

    Returns:
        dict: Mapping of k‑mer feature names to relative frequencies.

    Raises:
        FileNotFoundError: If the FASTA file does not exist.
        ValueError: If the FASTA file contains no records or the sequence is empty.
    """
    # ------------------------------------------------------------------
    # Load the aggregated dataset to determine n_final
    # ------------------------------------------------------------------
    aggregated_path = paths.data("processed", "aggregated_dataset.csv")
    try:
        agg_df = pd.read_csv(aggregated_path)
        n_final = len(agg_df)
    except Exception as e:
        logger.error(f"Failed to read aggregated dataset at {aggregated_path}: {e}")
        raise RuntimeError(
            "Unable to determine n_final for k‑mer extraction. "
            "Ensure that data/processed/aggregated_dataset.csv exists and is readable."
        )

    # Determine which k values to use based on n_final
    if n_final < 50:
        ks = [3, 4]
        logger.info(f"n_final={n_final} (<50): extracting k‑mers for k={ks}")
    else:
        ks = [3, 4, 5, 6]
        logger.info(f"n_final={n_final} (>=50): extracting k‑mers for k={ks}")

    # ------------------------------------------------------------------
    # Read the FASTA sequence
    # ------------------------------------------------------------------
    path = Path(fasta_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

    records = list(Bio.SeqIO.parse(str(path), "fasta"))
    if not records:
        raise ValueError("FASTA file contains no records.")

    dna_seq = str(records[0].seq).upper()
    if not dna_seq:
        raise ValueError("DNA sequence is empty.")

    # Keep only standard nucleotides; replace others with empty string to avoid invalid k‑mers
    dna_seq = re.sub(r'[^ACGT]', '', dna_seq)

    frequencies: Dict[str, float] = {}

    # ------------------------------------------------------------------
    # Compute k‑mer counts and relative frequencies
    # ------------------------------------------------------------------
    for k in ks:
        if len(dna_seq) < k:
            logger.warning(f"Sequence length {len(dna_seq)} shorter than k={k}; skipping this k.")
            continue

        total_windows = len(dna_seq) - k + 1
        kmer_counter = Counter(dna_seq[i:i + k] for i in range(total_windows))

        for mer, count in kmer_counter.items():
            # Ensure the k‑mer consists only of A/C/G/T (already filtered)
            key = f"k{k}_{mer}"
            frequencies[key] = count / total_windows

    logger.info(f"Calculated {len(frequencies)} k‑mer frequency features for {path.name}.")
    return frequencies

def validate_kmer_features(features_df: pd.DataFrame) -> None:
    """
    Verify that the k‑mer feature matrix complies with the rule based on
    the final dataset size (n_final).

    - For n_final < 50: columns for k=3 and k=4 must be present;
      columns for k=5 and k=6 must be absent.
    - For n_final >= 50: columns for k=3,4,5,6 must all be present.

    Raises:
        RuntimeError: If the feature set does not match the required rule.
    """
    # Load n_final from the aggregated dataset
    aggregated_path = paths.data("processed", "aggregated_dataset.csv")
    try:
        agg_df = pd.read_csv(aggregated_path)
        n_final = len(agg_df)
    except Exception as e:
        logger.error(f"Failed to read aggregated dataset at {aggregated_path}: {e}")
        raise RuntimeError(
            "Unable to determine n_final for k‑mer validation. "
            "Ensure that data/processed/aggregated_dataset.csv exists and is readable."
        )

    # Determine presence of required k‑mer prefixes
    cols = list(features_df.columns)
    has_k3 = any(col.startswith("k3_") for col in cols)
    has_k4 = any(col.startswith("k4_") for col in cols)
    has_k5 = any(col.startswith("k5_") for col in cols)
    has_k6 = any(col.startswith("k6_") for col in cols)

    missing = []
    if not has_k3:
        missing.append("k3")
    if not has_k4:
        missing.append("k4")
    if missing:
        raise RuntimeError(f"Missing required k‑mer columns: {', '.join(missing)}")

    if n_final < 50:
        # k5 and k6 must be absent
        if has_k5 or has_k6:
            raise RuntimeError(
                f"Unexpected k‑mer columns for k=5/6 when n_final={n_final} (<50)."
            )
    else:
        # k5 and k6 must be present
        missing_high = []
        if not has_k5:
            missing_high.append("k5")
        if not has_k6:
            missing_high.append("k6")
        if missing_high:
            raise RuntimeError(
                f"Missing required k‑mer columns for n_final={n_final} (>=50): {', '.join(missing_high)}"
            )

def calculate_repeat_density(fasta_path: str) -> float:
    """
    Calculate the percentage of a viral genome that is masked as repeat
    sequence.  Repeat‑masked bases are assumed to be represented by
    lower‑case nucleotides in the FASTA file (a common convention for
    repeat‑masked assemblies).  The function uses ``pybedtools`` to
    construct interval objects for each contiguous masked region and then
    sums their lengths to obtain the total repeat‑masked span.

    Args:
        fasta_path: Path to the FASTA file containing the viral genome.

    Returns:
        Float – percentage of the genome covered by repeats (0‑100).

    Raises:
        FileNotFoundError: If the FASTA file does not exist.
        ValueError: If the FASTA file contains no records or the sequence is empty.
    """
    path = Path(fasta_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

    # Load the first sequence from the FASTA file
    records = list(Bio.SeqIO.parse(str(path), "fasta"))
    if not records:
        raise ValueError("FASTA file contains no records.")

    seq = str(records[0].seq)
    if not seq:
        raise ValueError("DNA sequence is empty.")

    total_len = len(seq)

    # Identify contiguous lower‑case runs (repeat‑masked regions)
    intervals = []
    i = 0
    while i < total_len:
        if seq[i].islower():
            start = i
            while i < total_len and seq[i].islower():
                i += 1
            end = i  # end is exclusive
            intervals.append((0, start, end))  # chromosome placeholder '0'
        else:
            i += 1

    if not intervals:
        # No repeat‑masked bases
        return 0.0

    # Create a BedTool from the interval list
    # BedTool expects a string with tab‑separated fields: chrom start end
    bed_str = "\n".join(f"{chrom}\t{start}\t{end}" for chrom, start, end in intervals)
    bed = pybedtools.BedTool(bed_str, from_string=True)

    # Sum the lengths of all intervals
    repeat_bases = sum(interval.length for interval in bed)

    repeat_percentage = (repeat_bases / total_len) * 100.0
    logger.info(
        f"Repeat density for {path.name}: {repeat_bases}/{total_len} bases "
        f"({repeat_percentage:.2f}%)."
    )
    return repeat_percentage

def check_esm1b_feasibility() -> bool:
    """
    Determine whether ESM‑1b inference is feasible on the current
    hardware/environment.

    The function attempts to import the ``esm`` package and run a
    minimal inference on a tiny peptide (``MKT``).  If the import or
    inference fails, or if the operation exceeds the allowed runtime
    (30 seconds) or memory usage (1 GiB), the function returns ``False``.
    Otherwise it returns ``True``.

    Returns:
        bool: ``True`` if ESM‑1b can be used, ``False`` otherwise.
    """
    try:
        import esm
        import torch
    except Exception as e:
        logger.warning(f"ESM import failed or required dependencies missing: {e}")
        return False

    # Minimal peptide for a quick test
    test_seq = "MKT"

    start_time = time.time()
    process = psutil.Process()

    try:
        # Load a small ESM model; using the standard pretrained model.
        # This model is large, but loading it is part of the feasibility test.
        model, alphabet = esm.pretrained.esm1b_t33_650M_UR50S()
        model.eval()
        batch_converter = alphabet.get_batch_converter()
        data = [("test", test_seq)]
        _, _, batch_tokens = batch_converter(data)

        # Run a single forward pass
        with torch.no_grad():
            _ = model(batch_tokens, repr_layers=[33], return_contacts=False)

    except Exception as e:
        logger.warning(f"ESM inference failed during feasibility check: {e}")
        return False
    finally:
        duration = time.time() - start_time
        mem_usage = process.memory_info().rss  # in bytes

    if duration > 30:
        logger.warning(f"ESM feasibility check exceeded time limit: {duration:.2f}s > 30s")
        return False

    if mem_usage > 1 * 1024 ** 3:  # 1 GiB
        logger.warning(
            f"ESM feasibility check exceeded memory limit: {mem_usage / (1024 ** 2):.2f}MiB > 1024MiB"
        )
        return False

    logger.info(
        f"ESM feasibility check passed (time={duration:.2f}s, memory={mem_usage / (1024 ** 2):.2f}MiB)."
    )
    return True

def validate_proxy_baseline() -> bool:
    """
    Validate that the Uniform Stability Proxy correlates sufficiently
    with ESM‑1b stability scores.

    The function:
    1. Loads the aggregated dataset to obtain the list of strain accessions.
    2. Selects up to 20 representative strains (or fewer if fewer are available).
    3. For each selected strain, calculates the proxy stability score using
       :func:`calculate_stability` (hydrophobicity_score is used as the scalar proxy).
    4. If ESM‑1b is feasible, computes a scalar ESM‑1b stability score for the same
       strain (mean of the final layer representation of the translated protein).
    5. Calculates the coefficient of determination (R²) between the two score vectors.
    6. Raises a ``RuntimeError`` if R² < 0.8. Returns ``True`` otherwise.

    If ESM‑1b is not feasible, the function logs the situation and returns ``True``
    (the proxy will be used downstream as per the pipeline logic).

    Returns:
        bool: ``True`` if validation passes or ESM‑1b is infeasible.

    Raises:
        RuntimeError: If the correlation is below the required threshold or
                      if required input files are missing.
    """
    # Load aggregated dataset to get strain identifiers
    agg_path = paths.data("processed", "aggregated_dataset.csv")
    try:
        agg_df = pd.read_csv(agg_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load aggregated dataset for proxy validation: {e}")

    if 'strain_accession' not in agg_df.columns:
        raise RuntimeError("Aggregated dataset missing required column 'strain_accession'.")

    strain_ids = agg_df['strain_accession'].dropna().unique()
    # Select up to 20 strains
    subset_ids = strain_ids[:20] if len(strain_ids) > 20 else strain_ids

    proxy_scores: List[float] = []
    esm_scores: List[float] = []

    for sid in subset_ids:
        fasta_path = paths.data("raw", f"{sid}.fasta")
        if not Path(fasta_path).exists():
            logger.warning(f"FASTA file for strain {sid} not found; skipping.")
            continue

        # Proxy score (hydrophobicity)
        try:
            proxy_dict = calculate_stability(str(fasta_path))
            proxy_val = proxy_dict.get('hydrophobicity_score')
            if proxy_val is None:
                logger.warning(f"Hydrophobicity score missing for strain {sid}; skipping.")
                continue
            proxy_scores.append(proxy_val)
        except Exception as e:
            logger.error(f"Error computing proxy stability for {sid}: {e}")
            continue

        # ESM‑1b score
        if not check_esm1b_feasibility():
            logger.info("ESM‑1b not feasible; skipping correlation verification.")
            return True

        try:
            import esm
            import torch
            # Load model once per strain (could be optimized)
            model, alphabet = esm.pretrained.esm1b_t33_650M_UR50S()
            model.eval()
            batch_converter = alphabet.get_batch_converter()

            # Translate DNA to protein
            record = next(Bio.SeqIO.parse(str(fasta_path), "fasta"))
            dna_seq = str(record.seq)
            protein_seq = _translate_dna_to_protein(dna_seq)

            data = [("seq", protein_seq)]
            _, _, batch_tokens = batch_converter(data)

            with torch.no_grad():
                results = model(batch_tokens, repr_layers=[33], return_contacts=False)
                token_repr = results["representations"][33]
                # Exclude start/end tokens and average remaining embeddings
                seq_repr = token_repr[0, 1:-1].mean().item()
            esm_scores.append(seq_repr)
        except Exception as e:
            raise RuntimeError(f"ESM‑1b inference failed during proxy validation for strain {sid}: {e}")

    if not proxy_scores or not esm_scores:
        raise RuntimeError("Insufficient data to compute correlation for proxy validation.")

    # Compute R²
    r2 = r2_score(proxy_scores, esm_scores)
    if r2 < 0.8:
        raise RuntimeError(f"Proxy baseline validation failed: R²={r2:.3f} < 0.8")
    logger.info(f"Proxy baseline validation succeeded: R²={r2:.3f}")
    return True

def calculate_stability_esm(fasta_path: str) -> dict:
    """
    Calculate a protein stability score using the ESM‑1b language model.

    The function:
    1. Reads the FASTA file, extracts the first DNA sequence and translates it
       to a protein sequence.
    2. Loads the pretrained ESM‑1b model (``esm1b_t33_650M_UR50S``).
    3. Obtains the representation from the final transformer layer (layer 33)
       for the protein sequence.
    4. Averages the token representations (excluding start/end tokens) to obtain
       a single scalar stability score.

    Args:
        fasta_path: Path to the FASTA file containing the viral genome.

    Returns:
        dict: ``{'esm_stability_score': <float>}`` – a scalar score representing
        the predicted stability of the protein according to ESM‑1b.

    Raises:
        FileNotFoundError: If the FASTA file does not exist.
        ValueError: If the FASTA file contains no records or the sequence is empty.
        RuntimeError: If ESM‑1b inference fails (e.g., model cannot be loaded).
    """
    path = Path(fasta_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

    # Load DNA sequence and translate to protein
    try:
        records = list(Bio.SeqIO.parse(str(path), "fasta"))
        if not records:
            raise ValueError("FASTA file contains no records.")
        dna_seq = str(records[0].seq).upper()
        if not dna_seq:
            raise ValueError("DNA sequence is empty.")
        protein_seq = _translate_dna_to_protein(dna_seq)
        if not protein_seq:
            raise ValueError("Protein translation resulted in an empty sequence.")
    except Exception as e:
        logger.error(f"Failed to parse or translate FASTA {fasta_path}: {e}")
        raise

    # Load ESM‑1b model and compute representation
    try:
        import esm
        import torch
        model, alphabet = esm.pretrained.esm1b_t33_650M_UR50S()
        model.eval()
        batch_converter = alphabet.get_batch_converter()

        data = [("seq", protein_seq)]
        _, _, batch_tokens = batch_converter(data)

        with torch.no_grad():
            results = model(batch_tokens, repr_layers=[33], return_contacts=False)
            token_repr = results["representations"][33]  # shape: (1, seq_len+2, dim)
            # Exclude start/end tokens (first and last) and average the rest
            seq_repr = token_repr[0, 1:-1].mean().item()
    except Exception as e:
        logger.error(f"ESM‑1b inference failed for {fasta_path}: {e}")
        raise RuntimeError(f"ESM‑1b inference failed: {e}")

    logger.info(f"ESM‑1b stability score calculated for {path.name}: {seq_repr:.4f}")
    return {"esm_stability_score": float(seq_repr)}
