"""
Synthetic Data Generator for Honeybee CCD GWAS Pipeline Validation.

This module generates deterministic synthetic VCF and Phenotype data for validation
purposes ONLY. It does NOT fetch or use real biological data.

The synthetic data generation strictly adheres to the CCD diagnosis validation logic
defined in FR-011:
1. Presence of dead adult bees in the hive.
2. Absence of dead pupae.
3. Live bee population < 10% relative to peak season.

If these criteria are not met in the generated sample, the sample is flagged as
'NOT CCD' or the generation logic adjusts to ensure validity for the 'CCD' class.
"""

import os
import sys
import random
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Set seeds for reproducibility
RANDOM_SEED = 42

def set_seed(seed: int = RANDOM_SEED) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    if 'numpy' in sys.modules:
        import numpy as np
        np.random.seed(seed)

def generate_synthetic_colonies(n_colonies: int = 100) -> List[Dict[str, Any]]:
    """
    Generate synthetic colony data with CCD diagnosis validation logic.

    Validates FR-011 criteria:
    1. Presence of dead adult bees (dead_adults > 0).
    2. Absence of dead pupae (dead_pupae == 0).
    3. Live bee population < 10% of peak (live_bees < 0.1 * peak_bees).

    Returns a list of colony records.
    """
    set_seed()
    colonies = []

    # We will generate roughly 50% CCD positive and 50% negative for balance
    n_ccd = n_colonies // 2
    n_control = n_colonies - n_ccd

    for i in range(n_colonies):
        is_ccd = i < n_ccd
        colony_id = f"COL_{i:04d}"

        # Base population parameters (simulating a hive peak)
        peak_bees = random.randint(40000, 60000)

        if is_ccd:
            # CCD Criteria:
            # 1. Dead adults > 0 (Significant presence)
            dead_adults = random.randint(1000, 5000)
            # 2. Dead pupae == 0 (Absence of dead pupae)
            dead_pupae = 0
            # 3. Live bees < 10% of peak
            live_bees = random.randint(100, int(peak_bees * 0.09))
            diagnosis = "CCD"
        else:
            # Control: Healthy colony
            # 1. Dead adults low (normal turnover)
            dead_adults = random.randint(0, 200)
            # 2. Dead pupae present (normal brood cycle) OR 0, but not the specific CCD pattern
            # To differentiate, we ensure dead_pupae > 0 sometimes or live_bees are high
            dead_pupae = random.randint(100, 2000)
            # 3. Live bees > 80% of peak
            live_bees = random.randint(int(peak_bees * 0.8), peak_bees)
            diagnosis = "HEALTHY"

        # Validation Check: Ensure the generated data strictly meets the logic
        # If we accidentally generated a "CCD" that doesn't meet criteria, we fix it
        if diagnosis == "CCD":
            assert dead_adults > 0, "CCD must have dead adults"
            assert dead_pupae == 0, "CCD must have NO dead pupae"
            assert live_bees < (peak_bees * 0.10), "CCD must have <10% live bees"

        # Add covariates required by FR-003
        geographic_region = random.choice(["North", "South", "East", "West"])
        sampling_year = random.choice([2021, 2022, 2023])
        varroa_load = random.uniform(0.1, 15.0) if random.random() > 0.05 else None # 5% missing

        colony = {
            "colony_id": colony_id,
            "diagnosis": diagnosis,
            "peak_bees": peak_bees,
            "live_bees": live_bees,
            "dead_adults": dead_adults,
            "dead_pupae": dead_pupae,
            "geographic_region": geographic_region,
            "sampling_year": sampling_year,
            "varroa_load": varroa_load
        }
        colonies.append(colony)

    return colonies

def generate_synthetic_snps(colonies: List[Dict[str, Any]], n_snps: int = 1000) -> List[Dict[str, Any]]:
    """
    Generate synthetic SNP data associated with the colonies.

    Creates a matrix of genotypes (0, 1, 2) for each colony.
    Introduces a weak signal for a subset of SNPs to simulate association.
    """
    set_seed()
    snps = []

    # Define "causal" SNPs (first 10) to have a slight association with CCD
    causal_indices = list(range(10))

    for i in range(n_snps):
        snp_id = f"SNP_{i:06d}"
        chrom = f"chr{random.randint(1, 16)}" # Honeybee has ~16 chromosomes
        pos = random.randint(1000, 10000000)
        ref = random.choice(["A", "C", "G", "T"])
        alt = random.choice(["A", "C", "G", "T"])
        while alt == ref:
            alt = random.choice(["A", "C", "G", "T"])

        # Generate genotypes for each colony
        genotypes = []
        for colony in colonies:
            is_ccd = colony["diagnosis"] == "CCD"

            # Base minor allele frequency (MAF) ~ 0.3
            maf = 0.3

            if i in causal_indices and is_ccd:
                # Slight enrichment in CCD cases
                prob = maf + 0.1
            else:
                prob = maf

            # Draw genotype (0, 1, 2) based on binomial distribution approx
            # P(0) = (1-p)^2, P(1) = 2p(1-p), P(2) = p^2
            p = prob
            r = random.random()
            if r < (1-p)**2:
                gt = 0
            elif r < (1-p)**2 + 2*p*(1-p):
                gt = 1
            else:
                gt = 2

            genotypes.append(gt)

        snp_record = {
            "snp_id": snp_id,
            "chrom": chrom,
            "pos": pos,
            "ref": ref,
            "alt": alt,
            "genotypes": genotypes
        }
        snps.append(snp_record)

    return snps

def write_vcf(snps: List[Dict[str, Any]], colonies: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write synthetic SNP data to VCF format.

    VCF Header + Genotype Matrix.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w') as f:
        # Header
        f.write("##fileformat=VCFv4.2\n")
        f.write(f"##source=SyntheticDataGenerator\n")
        f.write(f"##reference=SyntheticHoneybeeRef\n")
        f.write(f"##FORMAT=<ID=GT,Number=1,Type=String,Description=\"Genotype\">\n")
        
        # Column names
        col_names = ["#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO", "FORMAT"]
        for col in colonies:
            col_names.append(col["colony_id"])
        f.write("\t".join(col_names) + "\n")

        # Data rows
        for snp in snps:
            row = [
                snp["chrom"],
                str(snp["pos"]),
                snp["snp_id"],
                snp["ref"],
                snp["alt"],
                "30.0", # QUAL
                "PASS",
                ".",
                "GT"
            ]
            # Add genotypes
            for gt in snp["genotypes"]:
                row.append(str(gt))
            f.write("\t".join(row) + "\n")

def write_phenotypes(colonies: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write phenotype data in PLINK-compatible .fam and .pheno format.

    .fam format:
    1. Family ID (FID)
    2. Individual ID (IID)
    3. Paternal ID (0)
    4. Maternal ID (0)
    5. Sex (0)
    6. Phenotype (1=Control, 2=Case, -9=Missing)

    .pheno format:
    1. IID
    2. Phenotype value
    3. Covariates
    """
    fam_path = Path(output_path)
    pheno_path = fam_path.with_suffix('.pheno')
    fam_path.parent.mkdir(parents=True, exist_ok=True)

    with open(fam_path, 'w') as f_fam, open(pheno_path, 'w') as f_pheno:
        # Write .fam
        for col in colonies:
            fid = col["colony_id"]
            iid = col["colony_id"]
            sex = "0"
            # Map diagnosis: CCD=2 (Case), HEALTHY=1 (Control)
            pheno_val = "2" if col["diagnosis"] == "CCD" else "1"
            f_fam.write(f"{fid}\t{iid}\t0\t0\t{sex}\t{pheno_val}\n")

        # Write .pheno (for covariates)
        f_pheno.write("#FID IID PHENO GEO_REGION YEAR VARROA\n")
        for col in colonies:
            pheno_val = "2" if col["diagnosis"] == "CCD" else "1"
            varroa = col["varroa_load"] if col["varroa_load"] is not None else -9.0
            f_pheno.write(f"{col['colony_id']}\t{col['colony_id']}\t{pheno_val}\t{col['geographic_region']}\t{col['sampling_year']}\t{varroa}\n")

def write_validation_report(colonies: List[Dict[str, Any]], snps: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write a JSON report validating the synthetic data against FR-011.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    ccd_count = sum(1 for c in colonies if c["diagnosis"] == "CCD")
    healthy_count = sum(1 for c in colonies if c["diagnosis"] == "HEALTHY")

    # Validate all CCD samples
    validation_passed = True
    errors = []

    for col in colonies:
        if col["diagnosis"] == "CCD":
            if col["dead_adults"] <= 0:
                validation_passed = False
                errors.append(f"CCD sample {col['colony_id']} has dead_adults <= 0")
            if col["dead_pupae"] != 0:
                validation_passed = False
                errors.append(f"CCD sample {col['colony_id']} has dead_pupae != 0")
            if col["live_bees"] >= (col["peak_bees"] * 0.10):
                validation_passed = False
                errors.append(f"CCD sample {col['colony_id']} has live_bees >= 10% of peak")

    report = {
        "total_colonies": len(colonies),
        "ccd_count": ccd_count,
        "healthy_count": healthy_count,
        "total_snps": len(snps),
        "validation_criteria": "FR-011",
        "validation_passed": validation_passed,
        "errors": errors
    }

    with open(path, 'w') as f:
        json.dump(report, f, indent=2)

def main():
    """Main function to generate synthetic VCF and phenotype data."""
    parser = argparse.ArgumentParser(description="Generate synthetic VCF and phenotype data for GWAS validation.")
    parser.add_argument("--n-colonies", type=int, default=100, help="Number of colonies to generate.")
    parser.add_argument("--n-snps", type=int, default=1000, help="Number of SNPs to generate.")
    parser.add_argument("--output-dir", type=str, default="data/interim", help="Output directory for generated files.")
    
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.n_colonies} colonies and {args.n_snps} SNPs...")
    
    colonies = generate_synthetic_colonies(args.n_colonies)
    snps = generate_synthetic_snps(colonies, args.n_snps)

    vcf_path = output_dir / "synthetic.vcf"
    fam_path = output_dir / "synthetic.fam"
    report_path = output_dir / "synthetic_validation_report.json"

    write_vcf(snps, colonies, str(vcf_path))
    write_phenotypes(colonies, str(fam_path))
    write_validation_report(colonies, snps, str(report_path))

    print(f"Synthetic data generation complete.")
    print(f"  VCF: {vcf_path}")
    print(f"  FAM: {fam_path}")
    print(f"  Report: {report_path}")

if __name__ == "__main__":
    main()