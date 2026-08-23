"""
Bonferroni Correction Verification Module (T061a Implementation)

This module verifies that the Bonferroni correction was applied correctly
to the p-values generated in T048 (Statistical Report Generation).

It reads the final statistical report (Markdown), parses the raw and corrected
p-values, manually recalculates the correction, and writes a verification report.

Output: results/analysis/bonferroni_verification.txt
"""
import os
import re
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REPORT_PATH = "results/analysis/final_statistical_report.md"
OUTPUT_PATH = "results/analysis/bonferroni_verification.txt"
NUM_COMPARISONS = 3  # occlusion, depth, relative position

def load_markdown_report(path: str) -> str:
    """Load the statistical report markdown file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Statistical report not found at {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_markdown_report(content: str) -> Dict[str, Dict[str, float]]:
    """
    Parse the markdown report to extract p-values.
    
    Expected format in report (example):
    | Metric | Comparison | Raw P-value | Bonferroni Corrected |
    | --- | --- | --- | --- |
    | Latency | occlusion | 0.032 | 0.096 |
    | ...
    
    Returns:
        Dict mapping comparison_name -> { "raw": float, "corrected": float }
    """
    results = {}
    
    # Regex to find table rows with p-values
    # Matches lines like: | Latency | occlusion | 0.032 | 0.096 |
    pattern = r'\|\s*(\w+)\s*\|\s*(\w+)\s*\|\s*([\d\.eE+-]+)\s*\|\s*([\d\.eE+-]+)\s*\|'
    
    matches = re.findall(pattern, content)
    
    for metric, comparison, raw_str, corrected_str in matches:
        try:
            raw_p = float(raw_str)
            corrected_p = float(corrected_str)
            
            # We expect "Latency" or "Success" metrics. 
            # We aggregate by comparison name.
            if comparison not in results:
                results[comparison] = {"raw": raw_p, "corrected": corrected_p}
            else:
                # If multiple metrics exist for same comparison, we might need to handle differently.
                # For this verification, we assume the table lists the primary metric or we take the last one.
                # A more robust parser would check the metric name column.
                results[comparison]["raw"] = raw_p
                results[comparison]["corrected"] = corrected_p
        except ValueError:
            logger.warning(f"Could not parse p-values from row: {matches}")
            continue
    
    if not results:
        logger.warning("No p-values found in the report using the expected table format.")
        # Fallback: Try to find specific text patterns if table parsing fails
        # This is a heuristic fallback
        for comp in ["occlusion", "depth", "relative"]:
            raw_match = re.search(rf"{comp}.*?raw.*?p-value.*?[:\s]([0-9\.]+)", content, re.IGNORECASE | re.DOTALL)
            corr_match = re.search(rf"{comp}.*?corrected.*?p-value.*?[:\s]([0-9\.]+)", content, re.IGNORECASE | re.DOTALL)
            if raw_match and corr_match:
                results[comp] = {
                    "raw": float(raw_match.group(1)),
                    "corrected": float(corr_match.group(1))
                }
    
    return results

def apply_bonferroni_correction(raw_p: float, m: int) -> float:
    """
    Manually apply Bonferroni correction.
    Corrected P = min(Raw P * m, 1.0)
    """
    corrected = raw_p * m
    return min(corrected, 1.0)

def verify_bonferroni_correction(parsed_data: Dict[str, Dict[str, float]], m: int) -> List[Tuple[str, bool, str]]:
    """
    Verify the correction for each comparison.
    
    Returns:
        List of (comparison_name, passed, message) tuples.
    """
    verification_results = []
    
    for comp, values in parsed_data.items():
        raw_p = values.get("raw")
        reported_corr = values.get("corrected")
        
        if raw_p is None or reported_corr is None:
            verification_results.append((comp, False, "Missing raw or corrected p-value in report."))
            continue
        
        expected_corr = apply_bonferroni_correction(raw_p, m)
        
        # Allow for small floating point differences
        if np.isclose(expected_corr, reported_corr, rtol=1e-5, atol=1e-7):
            verification_results.append((comp, True, f"Corrected p-value matches: {reported_corr:.6f}"))
        else:
            msg = f"Mismatch. Raw: {raw_p:.6f}, Expected: {expected_corr:.6f}, Reported: {reported_corr:.6f}"
            verification_results.append((comp, False, msg))
    
    return verification_results

def generate_verification_report(results: List[Tuple[str, bool, str]], output_path: str, m: int):
    """
    Write the verification report to disk.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("BONFERRONI CORRECTION VERIFICATION REPORT\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Number of Comparisons (m): {m}\n")
        f.write(f"Source File: {REPORT_PATH}\n")
        f.write(f"Output File: {output_path}\n\n")
        
        all_passed = True
        for comp, passed, msg in results:
            status = "PASS" if passed else "FAIL"
            f.write(f"Comparison: {comp.upper()}\n")
            f.write(f"  Status: {status}\n")
            f.write(f"  Details: {msg}\n")
            f.write("-" * 40 + "\n")
            if not passed:
                all_passed = False
        
        f.write("\n" + "=" * 60 + "\n")
        if all_passed:
            f.write("OVERALL STATUS: PASSED\n")
            f.write("The Bonferroni correction was applied correctly in the statistical report.\n")
        else:
            f.write("OVERALL STATUS: FAILED\n")
            f.write("Discrepancies found in Bonferroni correction calculations.\n")
        f.write("=" * 60 + "\n")
    
    logger.info(f"Verification report written to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Verify Bonferroni correction in statistical report.")
    parser.add_argument("--report", type=str, default=REPORT_PATH, help="Path to the statistical report markdown.")
    parser.add_argument("--output", type=str, default=OUTPUT_PATH, help="Path to the verification output file.")
    parser.add_argument("--comparisons", type=int, default=NUM_COMPARISONS, help="Number of comparisons (m) for correction.")
    args = parser.parse_args()

    logger.info(f"Loading report from {args.report}...")
    try:
        content = load_markdown_report(args.report)
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Cannot proceed without the statistical report. Ensure T048 has been executed.")
        return 1

    logger.info("Parsing p-values from report...")
    parsed_data = parse_markdown_report(content)
    
    if not parsed_data:
        logger.error("Failed to extract any p-values from the report.")
        logger.error("Please check the format of the report or the parsing regex.")
        return 1

    logger.info(f"Found {len(parsed_data)} comparisons: {list(parsed_data.keys())}")
    
    logger.info("Verifying Bonferroni correction...")
    results = verify_bonferroni_correction(parsed_data, args.comparisons)
    
    logger.info(f"Generating verification report to {args.output}...")
    generate_verification_report(results, args.output, args.comparisons)
    
    # Return non-zero if verification failed
    if any(not passed for _, passed, _ in results):
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
