"""
Generate documentation for the pseudocount value used in CLR transformation.

This module documents the specific pseudocount value (default 1.0) used in the
Centered Log-Ratio (CLR) transformation to handle zero-inflated taxa data.
It reads the configuration or default from the CLR transform module and writes
a justification and value to a documentation file.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.utils.logger import get_logger
from src.preprocessing.clr_transform import DEFAULT_PSEUDOCOUNT

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent.parent

def generate_documentation(output_path: Optional[Path] = None, logger: Optional[logging.Logger] = None) -> None:
    """
    Generate the pseudocount documentation file.
    
    Args:
        output_path: Path to write the documentation. Defaults to 
                    data/processed/results/pseudocount_documentation.txt
        logger: Logger instance. If None, creates a default one.
    """
    if logger is None:
        logger = get_logger("pseudocount_doc")
    
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "results" / "pseudocount_documentation.txt"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    pseudocount_value = DEFAULT_PSEUDOCOUNT
    
    documentation_content = f"""Pseudocount Documentation for CLR Transformation
================================================

Date Generated: Automatically by generate_pseudocount_doc.py

Pseudocount Value Used: {pseudocount_value}

Justification:
--------------
The Centered Log-Ratio (CLR) transformation is a standard method for analyzing 
compositional data, such as microbiome taxon abundances. The CLR transformation 
is defined as:

    clr(x_i) = ln(x_i / g(x))

where:
    - x_i is the abundance of taxon i
    - g(x) is the geometric mean of all taxa abundances in the sample
    - ln is the natural logarithm

Problem with Zeros:
-------------------
Microbiome sequencing data is inherently sparse and contains many zero values 
for taxa that are either absent or below the detection limit in a sample. 
The logarithm of zero is undefined (-infinity), which would cause the CLR 
transformation to fail if applied directly to raw counts.

Solution - Pseudocount Addition:
--------------------------------
To handle zero values, a small positive constant (pseudocount) is added to all 
abundance values before applying the log transformation:

    clr(x_i) = ln((x_i + pseudocount) / g(x + pseudocount))

Choice of Pseudocount Value:
----------------------------
The value of {pseudocount_value} was selected based on the following considerations:

1. Standard Practice: A pseudocount of 1 is the most common default in 
   compositional data analysis literature and bioinformatics pipelines (e.g., 
   QIIME2, phyloseq). It represents adding one "virtual read" to each taxon.

2. Minimal Distortion: For taxa with moderate to high abundances (>> 1 read), 
   adding 1 has negligible impact on the relative proportions. For zero-abundance 
   taxa, it allows them to participate in the geometric mean calculation without 
   causing division by zero.

3. Compatibility: This value is compatible with the default settings of popular 
   microbiome analysis tools and ensures reproducibility with published studies.

4. Alternatives Considered:
   - Smaller values (e.g., 0.5, 0.1): May be more appropriate for extremely deep 
     sequencing but can introduce numerical instability in the geometric mean 
     calculation.
   - Half-minimum non-zero value: Data-dependent and can vary between samples, 
     complicating interpretation.
   - Bayesian-multiplicative replacement: More sophisticated but computationally 
     intensive and less transparent.

Implementation Details:
-----------------------
- The pseudocount is added uniformly to all taxa in all samples.
- The geometric mean is recalculated after pseudocount addition.
- The transformation is applied in src.preprocessing.clr_transform.py.
- Validation ensures no NaN or Inf values remain in the output.

References:
-----------
1. Gloor, G. B., et al. (2017). "Microbiome Datasets Are Compositional: And This 
   Is Not Optional." Frontiers in Microbiology.
2. Quinn, T. P., et al. (2018). "A Field Guide for the Compositional Analysis of 
   Any-omics Data." Nature Communications.
3. Gloor, G. B., & Reid, G. (2016). "Compositional Analysis: A Valid Approach to 
   Analyze Microbiome High-Dimensional Data." The ISME Journal.

---
This documentation was generated as part of task T020b in the llmXive pipeline.
"""
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(documentation_content)
        
        logger.info(f"Pseudocount documentation written to: {output_path}")
        logger.info(f"Documented pseudocount value: {pseudocount_value}")
        
    except IOError as e:
        logger.error(f"Failed to write documentation file: {e}")
        raise

def build_arg_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the script."""
    parser = argparse.ArgumentParser(
        description="Generate documentation for the pseudocount value used in CLR transformation."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to the output documentation file. Defaults to "
             "data/processed/results/pseudocount_documentation.txt"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    return parser

def main() -> int:
    """Main entry point for the script."""
    parser = build_arg_parser()
    args = parser.parse_args()
    
    logger = get_logger("pseudocount_doc")
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    output_path = Path(args.output) if args.output else None
    
    try:
        generate_documentation(output_path=output_path, logger=logger)
        logger.info("Pseudocount documentation generated successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate documentation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())