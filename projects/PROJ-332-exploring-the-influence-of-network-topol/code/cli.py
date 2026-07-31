import argparse
import sys
from typing import Dict, Any, Optional

def parse_material_override(raw_value: str) -> Dict[str, float]:
    """
    Parse a single --material-override argument of the form 'name=value'.
    
    Args:
        raw_value: A string in the format 'MaterialName=value'
        
    Returns:
        A dictionary with a single key-value pair: {material_name: float_value}
        
    Raises:
        ValueError: If the format is incorrect or value is not a valid float.
    """
    if '=' not in raw_value:
        raise ValueError(f"Invalid format for material override: '{raw_value}'. Expected 'name=value'.")
    
    parts = raw_value.split('=', 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid format for material override: '{raw_value}'. Expected exactly one '='.")
        
    material_name = parts[0].strip()
    value_str = parts[1].strip()
    
    if not material_name:
        raise ValueError("Material name cannot be empty.")
        
    try:
        value = float(value_str)
    except ValueError:
        raise ValueError(f"Invalid numeric value for material '{material_name}': '{value_str}'.")
        
    return {material_name: value}

def parse_cli_args(args: Optional[list] = None) -> argparse.Namespace:
    """
    Parse command-line arguments for the CLI.
    
    This function handles:
    - Standard flags (--run-single, --run-grid, --seed, --output)
    - The --material-override argument which allows overriding NIST defaults.
    
    Args:
        args: Optional list of arguments. If None, sys.argv[1:] is used.
        
    Returns:
        An argparse.Namespace object containing the parsed arguments.
        The 'material_overrides' attribute is a list of dictionaries, 
        each containing one material name and its override value.
    """
    parser = argparse.ArgumentParser(
        description="CLI for Nanowire Network Thermal Conductivity Simulation"
    )
    
    # Simulation modes
    parser.add_argument(
        '--run-single',
        action='store_true',
        help='Run a single simulation with parameters provided via other flags.'
    )
    parser.add_argument(
        '--run-grid',
        action='store_true',
        help='Run a grid of simulations over specified parameters.'
    )
    
    # Basic parameters
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility. Default: 42'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/simulation_results.csv',
        help='Output file path for results. Default: data/processed/simulation_results.csv'
    )
    
    # Material override (FR-016)
    parser.add_argument(
        '--material-override',
        action='append',
        dest='material_overrides',
        metavar='NAME=VALUE',
        help='Override thermal conductivity for a specific material. '
             'Format: MaterialName=value (e.g., --material-override Cu=400). '
             'Can be specified multiple times.'
    )
    
    # Grid parameters (optional, for --run-grid)
    parser.add_argument(
        '--N',
        type=int,
        nargs='+',
        default=[100],
        help='Node counts for grid simulation. Default: 100'
    )
    parser.add_argument(
        '--p',
        type=float,
        nargs='+',
        default=[0.1],
        help='Connection probabilities for grid simulation. Default: 0.1'
    )
    parser.add_argument(
        '--target-degree',
        type=int,
        nargs='+',
        default=[6],
        help='Target average degrees for grid simulation. Default: 6'
    )
    
    parsed = parser.parse_args(args)
    
    # Validate mutually exclusive modes
    if not parsed.run_single and not parsed.run_grid:
        parser.error("Either --run-single or --run-grid must be specified.")
    if parsed.run_single and parsed.run_grid:
        parser.error("--run-single and --run-grid cannot be specified together.")
        
    # Process material overrides into a list of dicts
    # This list will be passed to material_db.py for validation and merging with NIST defaults
    if parsed.material_overrides:
        overrides = []
        for override_str in parsed.material_overrides:
            overrides.append(parse_material_override(override_str))
        parsed.material_overrides = overrides
    else:
        parsed.material_overrides = []
        
    return parsed

def main():
    """Entry point for CLI execution."""
    args = parse_cli_args()
    
    # Log the parsed arguments for debugging
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"CLI Args parsed successfully.")
    logger.info(f"Mode: {'Single' if args.run_single else 'Grid'}")
    logger.info(f"Seed: {args.seed}")
    logger.info(f"Output: {args.output}")
    
    if args.material_overrides:
        logger.info(f"Material overrides provided: {args.material_overrides}")
    else:
        logger.info("No material overrides provided. Using NIST defaults.")
        
    # In a full implementation, we would now pass 'args' to the main simulation runner.
    # For T004a, we stop here as the task is strictly about parsing and passing the dict.
    return args

if __name__ == '__main__':
    main()