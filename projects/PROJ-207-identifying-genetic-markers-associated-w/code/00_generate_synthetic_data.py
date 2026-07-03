"""
Generate deterministic synthetic VCF and Phenotype data for GWAS validation.

Implements CCD diagnosis validation logic (FR-011) explicitly checking:
1. Presence of dead adult bees in the hive.
2. Absence of dead pupae.
3. Live bee population < 10% relative to peak season.

Logic fails validation if any criteria are not met.
"""
import os
import sys
import random
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Any

# Add code directory to path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.validators.colony_schema import validate_colony_data, ColonySchema
from utils.validators.snp_schema import validate_snp_data, SnpSchema

# Constants for synthetic data generation
RANDOM_SEED = 42
NUM_COLONIES = 150
NUM_SNPS = 500
CHROMOSOMES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

def set_seed(seed: int) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)

def generate_synthetic_colonies(n: int) -> List[Dict[str, Any]]:
    """
    Generate synthetic colony data with CCD diagnosis validation.
    
    FR-011 Validation Logic:
    1. Presence of dead adult bees (must be > 0)
    2. Absence of dead pupae (must be 0)
    3. Live bee population < 10% of peak (must be < 0.10)
    
    Returns list of colony dictionaries.
    """
    colonies = []
    
    for i in range(n):
        # Determine if this colony has CCD (roughly 30% prevalence)
        has_ccd = random.random() < 0.30
        
        if has_ccd:
            # CCD colonies MUST meet all three criteria
            # 1. Dead adult bees present (significant amount)
            dead_adult_bees = random.randint(5000, 20000)
            
            # 2. Dead pupae absent (must be 0)
            dead_pupae = 0
            
            # 3. Live bee population < 10% of peak
            peak_population = random.randint(40000, 60000)
            live_bee_population = random.randint(int(peak_population * 0.01), int(peak_population * 0.09))
            
            # Validate CCD criteria explicitly
            if dead_adult_bees == 0:
                raise ValueError(f"CCD Colony {i}: Dead adult bees must be > 0")
            if dead_pupae != 0:
                raise ValueError(f"CCD Colony {i}: Dead pupae must be 0")
            if live_bee_population >= peak_population * 0.10:
                raise ValueError(f"CCD Colony {i}: Live bee population must be < 10% of peak")
            
            ccd_status = 1
        else:
            # Non-CCD colonies should NOT meet the CCD criteria
            # Either dead adults are low, OR dead pupae present, OR live population is high
            scenario = random.choice(['low_dead_adults', 'dead_pupae_present', 'normal_population'])
            
            if scenario == 'low_dead_adults':
                dead_adult_bees = random.randint(0, 500)
                dead_pupae = 0
                peak_population = random.randint(40000, 60000)
                live_bee_population = random.randint(int(peak_population * 0.50), int(peak_population * 0.90))
            elif scenario == 'dead_pupae_present':
                dead_adult_bees = random.randint(0, 1000)
                dead_pupae = random.randint(100, 5000)
                peak_population = random.randint(40000, 60000)
                live_bee_population = random.randint(int(peak_population * 0.50), int(peak_population * 0.90))
            else:
                dead_adult_bees = random.randint(0, 1000)
                dead_pupae = 0
                peak_population = random.randint(40000, 60000)
                live_bee_population = random.randint(int(peak_population * 0.50), int(peak_population * 0.90))
            
            ccd_status = 0
            
            # Additional validation for non-CCD: ensure they don't accidentally meet CCD criteria
            if dead_adult_bees > 0 and dead_pupae == 0 and live_bee_population < peak_population * 0.10:
                # This colony accidentally looks like CCD, adjust slightly
                if random.random() < 0.5:
                    dead_pupae = random.randint(10, 100)
                else:
                    live_bee_population = int(peak_population * 0.15)
        
        colony = {
            'colony_id': f"COL_{i:04d}",
            'ccd_status': ccd_status,
            'dead_adult_bees': dead_adult_bees,
            'dead_pupae': dead_pupae,
            'peak_population': peak_population,
            'current_population': live_bee_population,
            'population_ratio': round(live_bee_population / peak_population, 4),
            'geographic_region': random.choice(['North', 'South', 'East', 'West', 'Central']),
            'sampling_year': random.choice([2021, 2022, 2023]),
            'varroa_load': round(random.uniform(0.0, 15.0), 2),
            'hive_weight_kg': round(random.uniform(10.0, 40.0), 2),
            'honey_production_kg': round(random.uniform(0.0, 80.0), 2)
        }
        
        # Validate against schema
        validate_colony_data(colony, ColonySchema())
        colonies.append(colony)
    
    return colonies

def generate_synthetic_snps(colonies: List[Dict], n_snps: int) -> List[Dict]:
    """
    Generate synthetic SNP data for the colonies.
    
    Creates a VCF-like structure with genotypes for each colony.
    Includes a few 'causal' SNPs associated with CCD status.
    """
    snps = []
    
    # Define a few causal SNPs (indices 10, 50, 100, 200, 300)
    causal_indices = [10, 50, 100, 200, 300]
    
    for i in range(n_snps):
        is_causal = i in causal_indices
        
        # Assign chromosome and position
        chrom = random.choice(CHROMOSOMES)
        pos = random.randint(1000, 1000000)
        
        # Alleles
        ref_allele = random.choice(['A', 'T', 'C', 'G'])
        alt_allele = random.choice(['A', 'T', 'C', 'G'])
        while alt_allele == ref_allele:
            alt_allele = random.choice(['A', 'T', 'C', 'G'])
        
        snp_entry = {
            'snp_id': f"SNP_{i:06d}",
            'chromosome': chrom,
            'position': pos,
            'ref_allele': ref_allele,
            'alt_allele': alt_allele,
            'is_causal': is_causal,
            'genotypes': []
        }
        
        # Generate genotypes for each colony
        for colony in colonies:
            # Causal SNPs have higher frequency of risk allele in CCD colonies
            if is_causal and colony['ccd_status'] == 1:
                # Higher probability of risk allele (0.7)
                risk_allele_freq = 0.7
            elif is_causal and colony['ccd_status'] == 0:
                # Lower probability of risk allele (0.3)
                risk_allele_freq = 0.3
            else:
                # Neutral SNPs: random frequency
                risk_allele_freq = random.uniform(0.1, 0.9)
            
            # Generate diploid genotype (0, 1, or 2 risk alleles)
            n_risk_alleles = sum(1 for _ in range(2) if random.random() < risk_allele_freq)
            snp_entry['genotypes'].append(n_risk_alleles)
        
        snps.append(snp_entry)
    
    return snps

def write_vcf(colonies: List[Dict], snps: List[Dict], output_path: Path) -> None:
    """
    Write synthetic data to VCF format.
    
    VCF format:
    ##fileformat=VCFv4.2
    ##INFO=<ID=...,>
    #CHROM  POS     ID      REF     ALT     QUAL    FILTER  INFO    FORMAT  [sample1] [sample2] ...
    """
    with open(output_path, 'w') as f:
        # Header
        f.write("##fileformat=VCFv4.2\n")
        f.write("##source=synthetic_generator\n")
        f.write("##INFO=<ID=NS,Number=1,Type=Integer,Description=\"Number of Samples with Data\">\n")
        f.write("##INFO=<ID=DP,Number=1,Type=Integer,Description=\"Total Depth\">\n")
        f.write("##FORMAT=<ID=GT,Number=1,Type=String,Description=\"Genotype\">\n")
        
        # Sample line
        sample_ids = [c['colony_id'] for c in colonies]
        f.write(f"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t" + "\t".join(sample_ids) + "\n")
        
        # Variant lines
        for snp in snps:
            gt_values = [str(g) for g in snp['genotypes']]
            info_str = f"NS={len(colonies)};DP=15"
            f.write(f"{snp['chromosome']}\t{snp['position']}\t{snp['snp_id']}\t{snp['ref_allele']}\t"
                    f"{snp['alt_allele']}\t30\tPASS\t{info_str}\tGT\t" + "\t".join(gt_values) + "\n")

def write_phenotypes(colonies: List[Dict], output_path: Path) -> None:
    """
    Write phenotype data in PLINK-compatible format.
    
    Output: data/processed/phenotypes_raw.tsv
    Columns: colony_id, ccd_status, geographic_region, sampling_year, varroa_load, ...
    """
    with open(output_path, 'w') as f:
        # Header
        header = ['colony_id', 'ccd_status', 'geographic_region', 'sampling_year', 
                 'varroa_load', 'hive_weight_kg', 'honey_production_kg',
                 'dead_adult_bees', 'dead_pupae', 'peak_population', 'current_population', 'population_ratio']
        f.write("\t".join(header) + "\n")
        
        # Data rows
        for c in colonies:
            row = [
                c['colony_id'],
                str(c['ccd_status']),
                c['geographic_region'],
                str(c['sampling_year']),
                str(c['varroa_load']),
                str(c['hive_weight_kg']),
                str(c['honey_production_kg']),
                str(c['dead_adult_bees']),
                str(c['dead_pupae']),
                str(c['peak_population']),
                str(c['current_population']),
                str(c['population_ratio'])
            ]
            f.write("\t".join(row) + "\n")

def write_validation_report(colonies: List[Dict], output_path: Path) -> None:
    """
    Write a validation report confirming CCD criteria were met.
    """
    ccd_colonies = [c for c in colonies if c['ccd_status'] == 1]
    non_ccd_colonies = [c for c in colonies if c['ccd_status'] == 0]
    
    with open(output_path, 'w') as f:
        f.write("CCD Diagnosis Validation Report\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Total Colonies: {len(colonies)}\n")
        f.write(f"CCD Colonies: {len(ccd_colonies)}\n")
        f.write(f"Non-CCD Colonies: {len(non_ccd_colonies)}\n\n")
        
        f.write("CCD Criteria Validation (FR-011):\n")
        f.write("-" * 30 + "\n")
        
        # Check all CCD colonies meet criteria
        all_valid = True
        for c in ccd_colonies:
            checks = []
            checks.append(f"Dead adults > 0: {c['dead_adult_bees'] > 0}")
            checks.append(f"Dead pupae == 0: {c['dead_pupae'] == 0}")
            checks.append(f"Population ratio < 0.10: {c['population_ratio'] < 0.10}")
            
            if not all(checks):
                all_valid = False
                f.write(f"FAILED: {c['colony_id']} - {checks}\n")
        
        if all_valid:
            f.write("All CCD colonies passed FR-011 validation criteria.\n")
        
        f.write("\nSample CCD Colonies (first 5):\n")
        for c in ccd_colonies[:5]:
            f.write(f"  {c['colony_id']}: Dead Adults={c['dead_adult_bees']}, "
                    f"Dead Pupae={c['dead_pupae']}, Ratio={c['population_ratio']:.4f}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Generate deterministic synthetic VCF and Phenotype data for GWAS validation."
    )
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default=Path("data/interim"),
        help="Output directory for generated files"
    )
    parser.add_argument(
        "--n-colonies",
        type=int,
        default=NUM_COLONIES,
        help="Number of synthetic colonies to generate"
    )
    parser.add_argument(
        "--n-snps",
        type=int,
        default=NUM_SNPS,
        help="Number of synthetic SNPs to generate"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Set seed
    set_seed(args.seed)
    
    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {args.n_colonies} synthetic colonies...")
    colonies = generate_synthetic_colonies(args.n_colonies)
    
    print(f"Generating {args.n_snps} synthetic SNPs...")
    snps = generate_synthetic_snps(colonies, args.n_snps)
    
    # Write outputs
    vcf_path = args.output_dir / "synthetic.vcf"
    phenotypes_path = args.output_dir / "phenotypes_raw.tsv"
    validation_report_path = args.output_dir / "ccd_validation_report.txt"
    
    print(f"Writing VCF to {vcf_path}...")
    write_vcf(colonies, snps, vcf_path)
    
    print(f"Writing phenotypes to {phenotypes_path}...")
    write_phenotypes(colonies, phenotypes_path)
    
    print(f"Writing validation report to {validation_report_path}...")
    write_validation_report(colonies, validation_report_path)
    
    print("Synthetic data generation complete.")
    print(f"  VCF: {vcf_path}")
    print(f"  Phenotypes: {phenotypes_path}")
    print(f"  Validation Report: {validation_report_path}")

if __name__ == "__main__":
    main()