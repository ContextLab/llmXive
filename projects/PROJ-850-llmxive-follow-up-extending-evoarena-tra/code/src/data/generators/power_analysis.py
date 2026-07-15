"""
Power analysis script to calculate sample size N for the EvoMem-Conflict study.

Parameters:
  Cohen's h = 0.2 (small effect size)
  Power = 0.80
  Alpha = 0.05

Calculates the required sample size for a two-proportion z-test (or equivalent
test for proportions) given the specified parameters.
"""

import math
import sys
import os
from pathlib import Path

# Add project root to path to ensure imports work regardless of execution context
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def calculate_sample_size_cohen_h(effect_size: float, power: float, alpha: float) -> int:
    """
    Calculate sample size N for a two-proportion test given Cohen's h, power, and alpha.
    
    Formula derivation:
      For a two-proportion z-test, the sample size per group (n) is:
      n = 2 * (Z_{1-alpha/2} + Z_{power})^2 / h^2
      
      Where:
        - Z_{1-alpha/2} is the critical value for the significance level
        - Z_{power} is the critical value for the desired power
        - h is Cohen's h (effect size)
        
      Total sample size N = 2 * n (assuming equal group sizes)
    
    Args:
        effect_size (float): Cohen's h (e.g., 0.2 for small effect)
        power (float): Desired statistical power (e.g., 0.80)
        alpha (float): Significance level (e.g., 0.05)
    
    Returns:
        int: Total sample size N (rounded up)
    """
    # Calculate Z-scores
    # Z_{1-alpha/2} for two-tailed test
    z_alpha = abs(math.erfcinv(alpha) * math.sqrt(2))
    
    # Z_{power}
    z_power = abs(math.erfcinv(2 * (1 - power)) * math.sqrt(2))
    
    # Calculate sample size per group
    # n = 2 * (Z_alpha + Z_power)^2 / h^2
    numerator = 2 * (z_alpha + z_power) ** 2
    denominator = effect_size ** 2
    
    n_per_group = numerator / denominator
    
    # Total sample size (two groups)
    total_n = 2 * n_per_group
    
    # Round up to ensure sufficient power
    return math.ceil(total_n)

def update_research_md(sample_size: int, research_md_path: Path) -> None:
    """
    Update the research.md file with the calculated sample size.
    
    Args:
        sample_size (int): The calculated sample size N
        research_md_path (Path): Path to the research.md file
    """
    if not research_md_path.exists():
        raise FileNotFoundError(f"research.md not found at {research_md_path}")
    
    # Read existing content
    content = research_md_path.read_text(encoding='utf-8')
    
    # Check if sample_size key already exists
    lines = content.splitlines()
    updated_lines = []
    found = False
    
    for line in lines:
        if line.strip().startswith("sample_size:"):
            # Update existing line
            updated_lines.append(f"sample_size: {sample_size}")
            found = True
        else:
            updated_lines.append(line)
    
    # If not found, append at the end (or after a relevant section)
    if not found:
        # Try to append after the title or first header if it looks like a config section
        # For simplicity, just append at the end with a newline
        if content and not content.endswith('\n'):
            updated_lines.append('')
        updated_lines.append(f"sample_size: {sample_size}")
    
    # Write back
    research_md_path.write_text('\n'.join(updated_lines), encoding='utf-8')

def main():
    """
    Main entry point for the power analysis script.
    
    Calculates sample size and updates research.md.
    """
    # Configuration parameters
    COHEN_H = 0.2  # Small effect size
    POWER = 0.80   # 80% power
    ALPHA = 0.05   # 5% significance level
    
    # Determine paths
    # research.md is expected at: specs/001-evoconflict-filtering/research.md
    specs_dir = PROJECT_ROOT / "specs" / "001-evoconflict-filtering"
    research_md_path = specs_dir / "research.md"
    
    if not specs_dir.exists():
        raise FileNotFoundError(f"Specs directory not found: {specs_dir}")
    
    # Calculate sample size
    print(f"Calculating sample size for:")
    print(f"  Cohen's h: {COHEN_H}")
    print(f"  Power: {POWER}")
    print(f"  Alpha: {ALPHA}")
    
    sample_size = calculate_sample_size_cohen_h(COHEN_H, POWER, ALPHA)
    
    print(f"  Calculated sample size N: {sample_size}")
    
    # Update research.md
    if not research_md_path.exists():
        # Create a minimal research.md if it doesn't exist
        print(f"Creating research.md at {research_md_path}")
        specs_dir.mkdir(parents=True, exist_ok=True)
        research_md_path.write_text(f"# Research Configuration\n\nsample_size: {sample_size}\n", encoding='utf-8')
    else:
        print(f"Updating research.md at {research_md_path}")
        update_research_md(sample_size, research_md_path)
    
    print("Done.")

if __name__ == "__main__":
    main()
