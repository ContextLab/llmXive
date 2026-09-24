"""
Power analysis script to calculate required sample size.

This script calculates the sample size needed for statistical power
analysis based on Cohen's h effect size.
"""
import math
import sys
import os
from pathlib import Path
from src.utils.seeding import set_deterministic_seed


def calculate_sample_size_cohen_h(effect_size: float = 0.2, 
                                  power: float = 0.8, 
                                  alpha: float = 0.05) -> int:
    """
    Calculate the required sample size for a given effect size, power, and alpha.
    
    Uses the approximation formula for sample size calculation in proportion tests.
    
    Args:
        effect_size (float): Cohen's h effect size. Default is 0.2 (small effect).
        power (float): Statistical power (1 - beta). Default is 0.8.
        alpha (float): Significance level. Default is 0.05.
    
    Returns:
        int: Required sample size per group.
    """
    # Set deterministic seed for reproducibility
    set_deterministic_seed(42)
    
    # Z-scores for power and alpha
    # Using approximate values: Z(0.8) ≈ 0.84, Z(0.975) ≈ 1.96
    z_power = 0.8416  # Approximate Z-score for 80% power
    z_alpha = 1.96    # Approximate Z-score for alpha=0.05 (two-tailed)
    
    # Sample size formula for proportion test
    # n = 2 * ((Z_alpha + Z_power) / effect_size)^2
    n = 2 * ((z_alpha + z_power) / effect_size) ** 2
    
    return math.ceil(n)


def update_research_md(sample_size: int, research_md_path: str = 'specs/001-evoconflict-filtering/research.md'):
    """
    Update the research.md file with the calculated sample size.
    
    Args:
        sample_size (int): The calculated sample size.
        research_md_path (str): Path to the research.md file.
    """
    # Ensure directory exists
    Path(research_md_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing content or create new file
    if Path(research_md_path).exists():
        with open(research_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = "# Research Configuration\n\n"
    
    # Update or add sample_size
    if 'sample_size:' in content:
        # Replace existing sample_size
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if line.strip().startswith('sample_size:'):
                new_lines.append(f"sample_size: {sample_size}")
            else:
                new_lines.append(line)
        content = '\n'.join(new_lines)
    else:
        # Add sample_size at the end
        content += f"\nsample_size: {sample_size}\n"
    
    # Write updated content
    with open(research_md_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated {research_md_path} with sample_size: {sample_size}")


def main():
    """Main function to run power analysis and update research.md."""
    # Set deterministic seed
    set_deterministic_seed(42)
    
    # Calculate sample size
    sample_size = calculate_sample_size_cohen_h(effect_size=0.2, power=0.8, alpha=0.05)
    
    print(f"Calculated sample size: {sample_size}")
    
    # Update research.md
    update_research_md(sample_size)


if __name__ == '__main__':
    main()
