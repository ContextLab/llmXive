import os
import sys
import random
import argparse
import json
from pathlib import Path
from typing import List, Dict, Tuple, Any

# Set seed for reproducibility
def set_seed(seed: int = 42) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)

def generate_synthetic_colonies(n_colonies: int = 100) -> List[Dict[str, Any]]:
    """
    Generate synthetic colony data with CCD diagnosis validation logic.
    
    CCD Diagnosis Validation Logic (FR-011):
    1. Presence of dead adult bees in the hive.
    2. Absence of dead pupae.
    3. Live bee population < 10% relative to peak season.
    
    Returns a list of colony dictionaries.
    """
    colonies = []
    
    for i in range(n_colonies):
        # Simulate peak season population (random between 20,000 and 60,000)
        peak_population = random.randint(20000, 60000)
        
        # Simulate current live bee population
        # For CCD colonies, this should be < 10% of peak
        # For healthy colonies, this should be > 10% of peak
        is_ccd = random.random() < 0.3  # 30% chance of CCD
        
        if is_ccd:
            current_population = int(peak_population * random.uniform(0.01, 0.09))
        else:
            current_population = int(peak_population * random.uniform(0.11, 0.95))
        
        # Simulate dead adult bees (present in CCD, variable in healthy)
        dead_adult_bees = random.randint(500, 5000) if is_ccd else random.randint(0, 500)
        
        # Simulate dead pupae (should be absent in CCD)
        # In healthy colonies, some dead pupae might be present
        dead_pupae = 0 if is_ccd else random.randint(0, 200)
        
        # Simulate Varroa mite load (higher in CCD)
        varroa_load = random.randint(10, 50) if is_ccd else random.randint(0, 15)
        
        # Simulate geographic region
        regions = ["North", "South", "East", "West", "Central"]
        region = random.choice(regions)
        
        # Simulate sampling year
        year = random.choice([2020, 2021, 2022, 2023])
        
        # Validate CCD diagnosis criteria
        # Criterion 1: Presence of dead adult bees
        criterion_1 = dead_adult_bees > 0
        
        # Criterion 2: Absence of dead pupae
        criterion_2 = dead_pupae == 0
        
        # Criterion 3: Live bee population < 10% relative to peak
        population_ratio = current_population / peak_population
        criterion_3 = population_ratio < 0.10
        
        # CCD diagnosis: all three criteria must be met
        is_ccd_validated = criterion_1 and criterion_2 and criterion_3
        
        colony = {
            "colony_id": f"COL_{i:04d}",
            "peak_population": peak_population,
            "current_population": current_population,
            "dead_adult_bees": dead_adult_bees,
            "dead_pupae": dead_pupae,
            "population_ratio": round(population_ratio, 4),
            "varroa_load": varroa_load,
            "region": region,
            "sampling_year": year,
            "ccd_diagnosis": is_ccd_validated,
            "criteria_met": {
                "dead_adult_bees_present": criterion_1,
                "dead_pupae_absent": criterion_2,
                "population_below_10pct": criterion_3
            }
        }
        
        colonies.append(colony)
    
    return colonies

def generate_synthetic_snps(colonies: List[Dict[str, Any]], n_snps: int = 10000) -> List[Dict[str, Any]]:
    """
    Generate synthetic SNP data associated with colonies.
    
    Some SNPs will be randomly associated with CCD status to simulate
    genetic markers.
    """
    snps = []
    
    # Select a subset of SNPs to be "associated" with CCD (simulate real genetic markers)
    n_associated = max(10, n_snps // 100)  # ~1% of SNPs are associated
    associated_indices = set(random.sample(range(n_snps), n_associated))
    
    for i in range(n_snps):
        is_associated = i in associated_indices
        
        # Generate chromosome and position
        chromosome = random.randint(1, 16)  # Honeybee has 16 chromosomes
        position = random.randint(1, 10000000)  # Up to 10M bp
        
        # Generate alleles (A, T, C, G)
        ref_allele = random.choice(["A", "T", "C", "G"])
        alt_allele = random.choice([a for a in ["A", "T", "C", "G"] if a != ref_allele])
        
        # For associated SNPs, create a bias in allele frequency based on CCD status
        # For non-associated SNPs, allele frequencies are random
        snp_data = {
            "snp_id": f"rs{i:06d}",
            "chromosome": chromosome,
            "position": position,
            "ref_allele": ref_allele,
            "alt_allele": alt_allele,
            "associated_with_ccd": is_associated
        }
        
        # Generate genotypes for each colony
        genotypes = []
        for colony in colonies:
            if is_associated:
                # Create a bias: CCD colonies more likely to have alt allele
                if colony["ccd_diagnosis"]:
                    # Higher probability of alt allele in CCD colonies
                    alt_freq = random.uniform(0.6, 0.9)
                else:
                    # Lower probability of alt allele in healthy colonies
                    alt_freq = random.uniform(0.1, 0.4)
            else:
                # Random allele frequency for non-associated SNPs
                alt_freq = random.uniform(0.1, 0.9)
            
            # Generate genotype (0, 1, or 2 copies of alt allele)
            # Simple binomial sampling
            n_alt = 0
            if random.random() < alt_freq:
                n_alt += 1
            if random.random() < alt_freq:
                n_alt += 1
            
            genotypes.append(n_alt)
        
        snp_data["genotypes"] = genotypes
        snps.append(snp_data)
    
    return snps

def write_vcf(snps: List[Dict[str, Any]], colonies: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write synthetic SNP data to VCF format.
    
    VCF format:
    #CHROM  POS     ID      REF     ALT     QUAL    FILTER  INFO    FORMAT  Sample1 Sample2 ...
    """
    with open(output_path, 'w') as f:
        # Write header
        f.write("##fileformat=VCFv4.2\n")
        f.write("##source=SyntheticDataGenerator\n")
        f.write("##INFO=<ID=NS,Number=1,Type=Integer,Description=\"Number of Samples With Data\">\n")
        f.write("##INFO=<ID=DP,Number=1,Type=Integer,Description=\"Total Depth\">\n")
        f.write("##FORMAT=<ID=GT,Number=1,Type=String,Description=\"Genotype\">\n")
        
        # Write column header
        sample_ids = [colony["colony_id"] for colony in colonies]
        f.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t" + "\t".join(sample_ids) + "\n")
        
        # Write SNP data
        for snp in snps:
            chrom = snp["chromosome"]
            pos = snp["position"]
            snp_id = snp["snp_id"]
            ref = snp["ref_allele"]
            alt = snp["alt_allele"]
            qual = "30"  # Arbitrary quality score
            filter_val = "PASS"
            info = "NS={};DP=10".format(len(colonies))
            format_val = "GT"
            
            genotypes = [str(g) for g in snp["genotypes"]]
            
            line = f"{chrom}\t{pos}\t{snp_id}\t{ref}\t{alt}\t{qual}\t{filter_val}\t{info}\t{format_val}\t" + "\t".join(genotypes) + "\n"
            f.write(line)

def write_phenotypes(colonies: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write phenotype data in PLINK .pheno format.
    
    Format:
    FID IID PHENOTYPE [covariates...]
    """
    with open(output_path, 'w') as f:
        # Write header
        f.write("FID\tIID\tPHENOTYPE\tREGION\tYEAR\tVARROA_LOAD\n")
        
        # Write phenotype data
        for colony in colonies:
            fid = colony["colony_id"]
            iid = colony["colony_id"]
            phenotype = 1 if colony["ccd_diagnosis"] else 0
            region = colony["region"]
            year = colony["sampling_year"]
            varroa_load = colony["varroa_load"]
            
            line = f"{fid}\t{iid}\t{phenotype}\t{region}\t{year}\t{varroa_load}\n"
            f.write(line)

def write_validation_report(colonies: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write a validation report detailing CCD diagnosis criteria.
    """
    ccd_count = sum(1 for c in colonies if c["ccd_diagnosis"])
    healthy_count = len(colonies) - ccd_count
    
    with open(output_path, 'w') as f:
        f.write("CCD Diagnosis Validation Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total colonies: {len(colonies)}\n")
        f.write(f"CCD colonies: {ccd_count}\n")
        f.write(f"Healthy colonies: {healthy_count}\n\n")
        
        f.write("CCD Diagnosis Criteria (FR-011):\n")
        f.write("-" * 30 + "\n")
        f.write("1. Presence of dead adult bees in the hive\n")
        f.write("2. Absence of dead pupae\n")
        f.write("3. Live bee population < 10% relative to peak season\n\n")
        
        f.write("Validation Summary:\n")
        f.write("-" * 30 + "\n")
        
        # Count how many colonies meet each criterion
        criterion_1_count = sum(1 for c in colonies if c["criteria_met"]["dead_adult_bees_present"])
        criterion_2_count = sum(1 for c in colonies if c["criteria_met"]["dead_pupae_absent"])
        criterion_3_count = sum(1 for c in colonies if c["criteria_met"]["population_below_10pct"])
        
        f.write(f"Criterion 1 (Dead adult bees present): {criterion_1_count}/{len(colonies)}\n")
        f.write(f"Criterion 2 (Dead pupae absent): {criterion_2_count}/{len(colonies)}\n")
        f.write(f"Criterion 3 (Population < 10% of peak): {criterion_3_count}/{len(colonies)}\n\n")
        
        f.write("Sample CCD Colonies:\n")
        f.write("-" * 30 + "\n")
        ccd_colonies = [c for c in colonies if c["ccd_diagnosis"]][:5]
        for colony in ccd_colonies:
            f.write(f"  {colony['colony_id']}: Population ratio={colony['population_ratio']:.2%}, ")
            f.write(f"Dead adults={colony['dead_adult_bees']}, Dead pupae={colony['dead_pupae']}\n")
        
        f.write("\nSample Healthy Colonies:\n")
        f.write("-" * 30 + "\n")
        healthy_colonies = [c for c in colonies if not c["ccd_diagnosis"]][:5]
        for colony in healthy_colonies:
            f.write(f"  {colony['colony_id']}: Population ratio={colony['population_ratio']:.2%}, ")
            f.write(f"Dead adults={colony['dead_adult_bees']}, Dead pupae={colony['dead_pupae']}\n")

def main():
    """Main function to generate synthetic data."""
    parser = argparse.ArgumentParser(description="Generate synthetic VCF and phenotype data for GWAS validation.")
    parser.add_argument("--n-colonies", type=int, default=100, help="Number of colonies to generate")
    parser.add_argument("--n-snps", type=int, default=10000, help="Number of SNPs to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="data/interim", help="Output directory")
    
    args = parser.parse_args()
    
    # Set seed
    set_seed(args.seed)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    print(f"Generating {args.n_colonies} synthetic colonies...")
    colonies = generate_synthetic_colonies(args.n_colonies)
    
    print(f"Generating {args.n_snps} synthetic SNPs...")
    snps = generate_synthetic_snps(colonies, args.n_snps)
    
    # Write outputs
    vcf_path = output_dir / "synthetic.vcf"
    phenotype_path = output_dir / "synthetic_phenotypes.pheno"
    validation_report_path = output_dir / "synthetic_validation_report.txt"
    
    print(f"Writing VCF to {vcf_path}...")
    write_vcf(snps, colonies, vcf_path)
    
    print(f"Writing phenotypes to {phenotype_path}...")
    write_phenotypes(colonies, phenotype_path)
    
    print(f"Writing validation report to {validation_report_path}...")
    write_validation_report(colonies, validation_report_path)
    
    print("Synthetic data generation complete.")
    print(f"  - VCF: {vcf_path}")
    print(f"  - Phenotypes: {phenotype_path}")
    print(f"  - Validation Report: {validation_report_path}")

if __name__ == "__main__":
    main()