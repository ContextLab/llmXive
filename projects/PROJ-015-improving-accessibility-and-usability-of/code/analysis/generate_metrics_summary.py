import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from analysis.stat_utils import generate_metrics_summary, run_anova_pipeline, calculate_effect_size, run_holm_bonferroni
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    """CLI wrapper for generating metrics summary."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate metrics summary CSV")
    parser.add_argument("--input", type=str, required=True, help="Input cleaned sessions CSV")
    parser.add_argument("--output", type=str, required=True, help="Output metrics summary CSV")
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
        
    df = pd.read_csv(args.input)
    generate_metrics_summary(df, args.output)
    logger.info(f"Metrics summary generated at {args.output}")

if __name__ == "__main__":
    main()