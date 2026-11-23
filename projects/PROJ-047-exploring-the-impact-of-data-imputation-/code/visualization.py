import argparse
import os
import sys
from typing import List, Optional, Dict, Any

# Import specific functions from analysis modules to avoid circular imports and allow direct calling
# We import the functions, not the module-level 'main', to have more control over arguments
from analysis.plot_bias import load_and_prepare_data as load_bias_data, aggregate_bias_by_beta, plot_bias_vs_beta
from analysis.plot_coverage import load_and_prepare_data as load_coverage_data, run_regression_test, plot_coverage_vs_beta
from analysis.plot_distributions import load_and_prepare_data as load_dist_data, plot_bias_distributions

def main():
    parser = argparse.ArgumentParser(description='Unified CLI for plot generation')
    subparsers = parser.add_subparsers(dest='command', help='Available plot commands')

    # Bias vs Beta Plot
    bias_parser = subparsers.add_parser('bias_vs_beta', help='Plot bias vs beta')
    bias_parser.add_argument('--input', type=str, required=True, help='Path to simulation_summary.csv')
    bias_parser.add_argument('--output', type=str, required=True, help='Path to output PNG')

    # Coverage vs Beta Plot
    coverage_parser = subparsers.add_parser('coverage_vs_beta', help='Plot coverage vs beta')
    coverage_parser.add_argument('--input', type=str, required=True, help='Path to simulation_summary.csv')
    coverage_parser.add_argument('--output', type=str, required=True, help='Path to output PNG')

    # Bias Distributions Plot
    dist_parser = subparsers.add_parser('bias_distributions', help='Plot bias distributions')
    dist_parser.add_argument('--input', type=str, required=True, help='Path to simulation_summary.csv')
    dist_parser.add_argument('--output', type=str, required=True, help='Path to output PNG')

    args = parser.parse_args()

    if args.command == 'bias_vs_beta':
        if not os.path.exists(args.input):
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        
        # Load data
        df = load_bias_data(args.input)
        
        # Aggregate
        aggregated = aggregate_bias_by_beta(df)
        
        # Plot and save
        plot_bias_vs_beta(aggregated, args.output)
        print(f"Bias vs Beta plot saved to {args.output}")
        
    elif args.command == 'coverage_vs_beta':
        if not os.path.exists(args.input):
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        
        # Load data
        df = load_coverage_data(args.input)
        
        # Run regression
        regression_results = run_regression_test(df)
        
        # Plot and save
        plot_coverage_vs_beta(df, regression_results, args.output)
        print(f"Coverage vs Beta plot saved to {args.output}")
        
    elif args.command == 'bias_distributions':
        if not os.path.exists(args.input):
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        
        # Load data
        df = load_dist_data(args.input)
        
        # Plot and save
        plot_bias_distributions(df, args.output)
        print(f"Bias distributions plot saved to {args.output}")
        
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
