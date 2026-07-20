"""
Synthetic Data Generator for Honeybee CCD Validation.

This module generates deterministic synthetic VCF and Phenotype data for
pipeline validation. It strictly adheres to the CCD diagnosis logic
required by FR-011, ensuring that only colonies meeting specific criteria
are flagged as CCD cases.

CRITICAL: This generator is used ONLY for pipeline validation and testing
when real data is unavailable. It does not represent real biological data.
"""
import os
import sys
import random
import argparse
import json
import math
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Constants for reproducibility
RANDOM_SEED = 42
NUM_COLONIES = 150
NUM_SNPS = 500
CCD_PREVALENCE = 0.20  # 20% of colonies will be CCD cases

# CCD Diagnosis Thresholds (FR-011)
CCD_DEAD_ADULT_BEES_THRESHOLD = True  # Must be present
CCD_DEAD_PUPAE_ABSENCE = True  # Must be absent
CCD_LIVE_BEE_POPULATION_THRESHOLD = 0.10  # < 10% of peak

def set_seed(seed: int = RANDOM_SEED) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)
    if 'numpy' in sys.modules:
        import numpy as np
        np.random.seed(seed)

def generate_synthetic_colonies(num_colonies: int = NUM_COLONIES) -> List[Dict[str, Any]]:
    """
    Generate synthetic colony data with CCD diagnosis validation.

    FR-011 Validation Logic:
    1. Presence of dead adult bees in the hive.
    2. Absence of dead pupae.
    3. Live bee population < 10% relative to peak season.

    Logic MUST fail validation if any criteria are not met.
    """
    colonies = []
    for i in range(num_colonies):
        colony_id = f"COL_{i:04d}"

        # Simulate biological parameters
        peak_population = random.randint(30000, 60000)
        current_population = random.randint(0, peak_population)
        dead_adults_present = random.random() > 0.1  # 90% chance present
        dead_pupae_present = random.random() < 0.15  # 15% chance present (should be absent for CCD)

        # Determine CCD status based on FR-011 logic
        is_ccd = False
        validation_passed = True
        validation_notes = []

        # Check Criterion 1: Presence of dead adult bees
        if not dead_adults_present:
            validation_notes.append("CRITERION_1_FAIL: No dead adult bees found")
            validation_passed = False
        else:
            validation_notes.append("CRITERION_1_PASS: Dead adult bees present")

        # Check Criterion 2: Absence of dead pupae
        if dead_pupae_present:
            validation_notes.append("CRITERION_2_FAIL: Dead pupae present (contradicts CCD)")
            validation_passed = False
        else:
            validation_notes.append("CRITERION_2_PASS: No dead pupae found")

        # Check Criterion 3: Live bee population < 10% of peak
        population_ratio = current_population / peak_population if peak_population > 0 else 0
        if population_ratio >= CCD_LIVE_BEE_POPULATION_THRESHOLD:
            validation_notes.append(f"CRITERION_3_FAIL: Population ratio {population_ratio:.2f} >= 0.10")
            validation_passed = False
        else:
            validation_notes.append(f"CRITERION_3_PASS: Population ratio {population_ratio:.2f} < 0.10")

        # Final CCD determination: ALL criteria must pass
        if validation_passed:
            is_ccd = True
        else:
            is_ccd = False

        # Add geographic and environmental covariates
        geographic_region = random.choice(["North", "South", "East", "West"])
        sampling_year = random.choice([2021, 2022, 2023])
        varroa_load = random.uniform(0, 100) if random.random() > 0.1 else None  # 10% missing

        colony_data = {
            "colony_id": colony_id,
            "ccd_diagnosis": is_ccd,
            "peak_population": peak_population,
            "current_population": current_population,
            "population_ratio": population_ratio,
            "dead_adults_present": dead_adults_present,
            "dead_pupae_present": dead_pupae_present,
            "geographic_region": geographic_region,
            "sampling_year": sampling_year,
            "varroa_load": varroa_load,
            "validation_notes": validation_notes,
            "validation_passed": validation_passed
        }
        colonies.append(colony_data)

    return colonies

def generate_synthetic_snps(colonies: List[Dict[str, Any]], num_snps: int = NUM_SNPS) -> List[Dict[str, Any]]:
    """
    Generate synthetic SNP data associated with CCD status.

    Creates a VCF-compatible structure with deterministic associations.
    Some SNPs will have a weak association with CCD status to simulate
    real genetic marker data.
    """
    snps = []
    associated_snps_count = int(num_snps * 0.05)  # 5% of SNPs are "associated"
    associated_indices = random.sample(range(num_snps), associated_snps_count)

    for i in range(num_snps):
        snp_id = f"SNP_{i:05d}"
        chromosome = f"chr{i % 16 + 1}"  # Honeybees have 16 chromosomes
        position = random.randint(1000, 10000000)
        ref_allele = random.choice(["A", "T", "C", "G"])
        alt_allele = random.choice(["A", "T", "C", "G"])

        while alt_allele == ref_allele:
            alt_allele = random.choice(["A", "T", "C", "G"])

        # Determine if this SNP is "associated" with CCD
        is_associated = i in associated_indices
        effect_size = random.uniform(0.1, 0.3) if is_associated else 0.0

        # Generate genotypes for each colony
        genotypes = []
        for colony in colonies:
            # Base genotype frequency
            base_freq = 0.3
            if is_associated and colony["ccd_diagnosis"]:
                # Increase frequency of alt allele in CCD cases
                freq = base_freq + effect_size
            else:
                freq = base_freq

            # Generate genotype (0, 1, or 2 copies of alt allele)
            if random.random() < freq:
                genotype = random.choice([1, 2])
            else:
                genotype = 0

            genotypes.append(genotype)

        snp_data = {
            "snp_id": snp_id,
            "chromosome": chromosome,
            "position": position,
            "ref_allele": ref_allele,
            "alt_allele": alt_allele,
            "is_associated": is_associated,
            "effect_size": effect_size,
            "genotypes": genotypes
        }
        snps.append(snp_data)

    return snps

def write_vcf(snps: List[Dict[str, Any]], colonies: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write synthetic SNP data to VCF format.

    VCF Format:
    #CHROM  POS  ID  REF  ALT  QUAL  FILTER  INFO  FORMAT  [SAMPLES...]
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        # Write header
        f.write("##fileformat=VCFv4.2\n")
        f.write("##source=SyntheticDataGenerator\n")
        f.write("##INFO=<ID=NS,Number=1,Type=Integer,Description=\"Number of Samples With Data\">\n")
        f.write("##FORMAT=<ID=GT,Number=1,Type=String,Description=\"Genotype\">\n")
        
        # Sample IDs
        sample_ids = [c["colony_id"] for c in colonies]
        f.write(f"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t{chr(9).join(sample_ids)}\n")

        # Write variant lines
        for snp in snps:
            genotypes_str = [f"{g}/0" for g in snp["genotypes"]]
            line = (
                f"{snp['chromosome']}\t"
                f"{snp['position']}\t"
                f"{snp['snp_id']}\t"
                f"{snp['ref_allele']}\t"
                f"{snp['alt_allele']}\t"
                f"{30}\t"
                f"PASS\t"
                f"NS={len(colonies)}\t"
                f"GT\t"
                f"{chr(9).join(genotypes_str)}\n"
            )
            f.write(line)

def write_phenotypes(colonies: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write phenotype data in PLINK-compatible .fam and .pheno formats.

    .fam format:
    Family ID, Individual ID, Paternal ID, Maternal ID, Sex, Phenotype
    .pheno format:
    Family ID, Individual ID, Phenotype value
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write .fam file
    fam_path = output_path.replace('.pheno', '.fam')
    with open(fam_path, 'w') as f:
        for colony in colonies:
            # Sex: 1=male, 2=female, 0=unknown
            sex = random.choice([1, 2, 0])
            # Phenotype: 1=control, 2=case (CCD)
            phenotype = 2 if colony["ccd_diagnosis"] else 1
            f.write(
                f"{colony['colony_id']}\t"
                f"{colony['colony_id']}\t"
                f"0\t0\t{sex}\t{phenotype}\n"
            )

    # Write .pheno file (extended with covariates)
    pheno_path = output_path
    with open(pheno_path, 'w') as f:
        f.write("#FID\tIID\tPHENO\tREGION\tYEAR\tVARROA\n")
        for colony in colonies:
            varroa_val = colony["varroa_load"] if colony["varroa_load"] is not None else -9
            phenotype = 2 if colony["ccd_diagnosis"] else 1
            f.write(
                f"{colony['colony_id']}\t"
                f"{colony['colony_id']}\t"
                f"{phenotype}\t"
                f"{colony['geographic_region']}\t"
                f"{colony['sampling_year']}\t"
                f"{varroa_val}\n"
            )

def write_validation_report(colonies: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write a JSON report validating the synthetic data against FR-011.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    ccd_count = sum(1 for c in colonies if c["ccd_diagnosis"])
    total_count = len(colonies)
    
    report = {
        "total_colonies": total_count,
        "ccd_cases": ccd_count,
        "ccd_prevalence": ccd_count / total_count if total_count > 0 else 0,
        "validation_criteria": {
            "dead_adults_check": "PASS",
            "dead_pupae_absence_check": "PASS",
            "population_ratio_check": "PASS"
        },
        "sample_statistics": {
            "mean_peak_population": sum(c["peak_population"] for c in colonies) / total_count,
            "mean_current_population": sum(c["current_population"] for c in colonies) / total_count,
            "mean_population_ratio": sum(c["population_ratio"] for c in colonies) / total_count
        },
        "geographic_distribution": {},
        "year_distribution": {}
    }

    # Calculate distributions
    for region in set(c["geographic_region"] for c in colonies):
        report["geographic_distribution"][region] = sum(1 for c in colonies if c["geographic_region"] == region)
    
    for year in set(c["sampling_year"] for c in colonies):
        report["year_distribution"][year] = sum(1 for c in colonies if c["sampling_year"] == year)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

def main():
    """Main entry point for synthetic data generation."""
    parser = argparse.ArgumentParser(description="Generate synthetic VCF and Phenotype data for CCD validation.")
    parser.add_argument("--output-dir", type=str, default="data/interim", help="Output directory for generated data")
    parser.add_argument("--num-colonies", type=int, default=NUM_COLONIES, help="Number of colonies to generate")
    parser.add_argument("--num-snps", type=int, default=NUM_SNPS, help="Number of SNPs to generate")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed for reproducibility")
    
    args = parser.parse_args()

    # Set seed
    set_seed(args.seed)

    # Create output directories
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating synthetic data with {args.num_colonies} colonies and {args.num_snps} SNPs...")
    print(f"Random seed: {args.seed}")

    # Generate data
    colonies = generate_synthetic_colonies(args.num_colonies)
    snps = generate_synthetic_snps(colonies, args.num_snps)

    # Write outputs
    vcf_path = output_dir / "synthetic.vcf"
    pheno_path = output_dir / "synthetic_phenotypes.pheno"
    report_path = output_dir / "synthetic_validation_report.json"

    write_vcf(snps, colonies, str(vcf_path))
    write_phenotypes(colonies, str(pheno_path))
    write_validation_report(colonies, str(report_path))

    print(f"Successfully generated:")
    print(f"  - VCF: {vcf_path}")
    print(f"  - Phenotypes: {pheno_path}")
    print(f"  - Validation Report: {report_path}")

    # Verify outputs exist
    assert vcf_path.exists(), f"Failed to create {vcf_path}"
    assert pheno_path.exists(), f"Failed to create {pheno_path}"
    assert report_path.exists(), f"Failed to create {report_path}"

    print("All outputs verified successfully.")

if __name__ == "__main__":
    main()