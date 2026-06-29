"""
Dataset Search and Verification Module for T000.

Searches for public developer productivity datasets containing required variables,
verifies URLs are accessible, and calculates SHA-256 checksums.

Required variables (from dataset.schema.yaml):
- tool_usage
- task_time
- defect_rate
- experience_years
- task_complexity
- project_type
- team_size
"""
import hashlib
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import re

# Configuration
RAW_DATA_DIR = Path("data/raw")
SPECS_DIR = Path("specs/001-code-generation-performance-outcomes")
SPEC_MD_PATH = SPECS_DIR / "spec.md"

REQUIRED_VARIABLES = [
    "tool_usage",
    "task_time",
    "defect_rate",
    "experience_years",
    "task_complexity",
    "project_type",
    "team_size"
]

# Candidate dataset sources with URLs
DATASET_CANDIDATES = [
    {
        "name": "OpenDev Benchmark - Developer Productivity",
        "url": "https://raw.githubusercontent.com/openssf/openssf-benchmark/main/data/developer_productivity_sample.csv",
        "description": "Open Source Security Foundation benchmark dataset with developer metrics",
        "variables_expected": ["tool_usage", "task_time", "defect_rate", "experience_years"]
    },
    {
        "name": "GitHub Copilot Study - Productivity Impact",
        "url": "https://raw.githubusercontent.com/github/copilot-research/main/data/productivity_study_sample.csv",
        "description": "GitHub Copilot research study data on developer productivity",
        "variables_expected": ["tool_usage", "task_time", "defect_rate", "experience_years", "task_complexity"]
    },
    {
        "name": "Stack Overflow Developer Survey - Aggregated",
        "url": "https://raw.githubusercontent.com/StackOverflow/developer-survey/main/aggregated/productivity_metrics.csv",
        "description": "Aggregated Stack Overflow survey data on developer productivity",
        "variables_expected": ["tool_usage", "task_time", "defect_rate", "experience_years", "team_size"]
    },
    {
        "name": "DevEx Research Dataset",
        "url": "https://raw.githubusercontent.com/devex-research/datasets/main/developer_experience.csv",
        "description": "Developer Experience research dataset with comprehensive metrics",
        "variables_expected": ["tool_usage", "task_time", "defect_rate", "experience_years", "task_complexity", "project_type", "team_size"]
    }
]

def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_url_accessible(url: str, timeout: int = 30) -> Tuple[bool, Optional[str]]:
    """Check if a URL is accessible and returns the status."""
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(request, timeout=timeout)
        status_code = response.getcode()
        if status_code == 200:
            return True, None
        else:
            return False, f"HTTP {status_code}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error: {e.code}"
    except urllib.error.URLError as e:
        return False, f"URL Error: {e.reason}"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def download_dataset(url: str, output_path: Path) -> bool:
    """Download a dataset from URL to the specified output path."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, output_path)
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def check_csv_variables(filepath: Path, required_vars: List[str]) -> Dict[str, bool]:
    """Check if CSV file contains required variables as column headers."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Read first line as header
            header_line = f.readline().strip()
            columns = [col.strip().lower() for col in header_line.split(',')]
        
        results = {}
        for var in required_vars:
            # Check if variable exists (case-insensitive, underscore variants)
            var_lower = var.lower()
            found = any(var_lower in col for col in columns)
            results[var] = found
        
        return results
    except Exception as e:
        print(f"Error checking variables in {filepath}: {e}")
        return {var: False for var in required_vars}

def search_and_verify_datasets() -> List[Dict]:
    """Search for and verify datasets containing required variables."""
    verified_datasets = []
    
    for candidate in DATASET_CANDIDATES:
        print(f"\n{'='*60}")
        print(f"Checking: {candidate['name']}")
        print(f"URL: {candidate['url']}")
        
        # Step 1: Verify URL is accessible
        accessible, error = verify_url_accessible(candidate['url'])
        if not accessible:
            print(f"  ❌ URL not accessible: {error}")
            continue
        print(f"  ✅ URL accessible")
        
        # Step 2: Download dataset
        output_filename = candidate['name'].lower().replace(' ', '_').replace('-', '_') + '.csv'
        output_path = RAW_DATA_DIR / output_filename
        
        if not download_dataset(candidate['url'], output_path):
            print(f"  ❌ Download failed")
            continue
        print(f"  ✅ Downloaded to {output_path}")
        
        # Step 3: Calculate SHA-256 checksum
        checksum = calculate_sha256(output_path)
        print(f"  ✅ SHA-256: {checksum}")
        
        # Step 4: Check for required variables
        variables_found = check_csv_variables(output_path, REQUIRED_VARIABLES)
        all_present = all(variables_found.values())
        
        print(f"  Variable check: {variables_found}")
        if all_present:
            print(f"  ✅ All required variables present")
        else:
            missing = [v for v, found in variables_found.items() if not found]
            print(f"  ⚠️  Missing variables: {missing}")
        
        verified_datasets.append({
            "name": candidate['name'],
            "url": candidate['url'],
            "description": candidate['description'],
            "local_path": str(output_path.relative_to(Path.cwd())),
            "sha256": checksum,
            "variables_found": variables_found,
            "all_required_present": all_present,
            "verified": all_present and accessible
        })
    
    return verified_datasets

def update_spec_md(verified_datasets: List[Dict]) -> None:
    """Update spec.md with verified datasets block."""
    if not SPEC_MD_PATH.exists():
        print(f"Warning: {SPEC_MD_PATH} does not exist. Creating it.")
        SPEC_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Create minimal spec.md with verified datasets block
        spec_content = """# Specification: Code Generation Performance Outcomes

This specification documents the research design and requirements for evaluating the impact of code generation tools on developer productivity.

## Overview

This research project investigates the relationship between AI code generation tools (e.g., GitHub Copilot) and developer productivity metrics including task completion time, defect rates, and code quality.

## Research Questions

1. How does tool usage affect task completion time across experience levels?
2. What is the association between AI code generation and defect rates?
3. How do task complexity and team size moderate these effects?

## Methodology

- **Statistical Approach**: Two-way ANOVA/ANCOVA with interaction terms
- **Effect Size**: Cohen's d for pairwise comparisons
- **Multiple Comparison Correction**: Bonferroni/Holm-Bonferroni
- **Framing**: Associational (non-causal) language only

"""
        with open(SPEC_MD_PATH, 'w', encoding='utf-8') as f:
            f.write(spec_content)
    
    with open(SPEC_MD_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Build verified datasets block
    datasets_block = """
## Verified Datasets

The following datasets have been verified for use in this research. All datasets meet the requirements specified in the dataset schema contract.

| Dataset Name | URL | SHA-256 Checksum | Variables Verified |
|--------------|-----|------------------|-------------------|
"""
    
    for ds in verified_datasets:
        if ds['verified']:
            var_list = ", ".join([v for v, found in ds['variables_found'].items() if found])
            datasets_block += f"| {ds['name']} | {ds['url']} | {ds['sha256']} | {var_list} |\n"
    
    # Check if verified datasets block already exists
    if "## Verified Datasets" in content:
        # Replace existing block
        lines = content.split('\n')
        new_lines = []
        in_block = False
        block_start_idx = None
        
        for i, line in enumerate(lines):
            if line.strip().startswith('## Verified Datasets'):
                block_start_idx = i
                in_block = True
                new_lines.append(line)
            elif in_block and line.strip().startswith('## '):
                # New section started, add our block before it
                new_lines.append(datasets_block.strip())
                new_lines.append('')
                new_lines.append(line)
                in_block = False
            elif in_block:
                continue
            else:
                new_lines.append(line)
        
        # If we reached end without new section, append at end
        if in_block:
            new_lines.append(datasets_block.strip())
        
        content = '\n'.join(new_lines)
    else:
        # Append at end
        content += datasets_block
    
    with open(SPEC_MD_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Updated {SPEC_MD_PATH} with verified datasets block")

def save_verification_report(verified_datasets: List[Dict]) -> None:
    """Save verification report to data/output directory."""
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "dataset_verification.json"
    
    report = {
        "verification_timestamp": None,  # Will be set by caller if needed
        "total_candidates": len(DATASET_CANDIDATES),
        "verified_count": sum(1 for d in verified_datasets if d['verified']),
        "datasets": verified_datasets
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Verification report saved to {report_path}")

def main():
    """Main entry point for dataset search and verification."""
    print("=" * 60)
    print("Dataset Search and Verification (T000)")
    print("=" * 60)
    print(f"Required variables: {REQUIRED_VARIABLES}")
    print(f"Candidate datasets: {len(DATASET_CANDIDATES)}")
    
    # Ensure raw data directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Search and verify datasets
    verified_datasets = search_and_verify_datasets()
    
    # Update spec.md
    update_spec_md(verified_datasets)
    
    # Save verification report
    save_verification_report(verified_datasets)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    verified_count = sum(1 for d in verified_datasets if d['verified'])
    print(f"Total candidates checked: {len(verified_datasets)}")
    print(f"Verified datasets: {verified_count}")
    
    for ds in verified_datasets:
        status = "✅ VERIFIED" if ds['verified'] else "❌ FAILED"
        print(f"\n{status}: {ds['name']}")
        print(f"  URL: {ds['url']}")
        print(f"  SHA-256: {ds['sha256']}")
        print(f"  Variables: {ds['variables_found']}")
    
    return verified_count > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)