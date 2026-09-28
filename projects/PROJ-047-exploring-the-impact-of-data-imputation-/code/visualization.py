import argparse
import os
import sys
from analysis.plot_bias import main as plot_bias_main
from analysis.plot_coverage import main as plot_coverage_main
from analysis.plot_distributions import main as plot_distributions_main

def main():
    parser = argparse.ArgumentParser(description='Visualization commands')
    subparsers = parser.add_subparsers(dest='command', help='Available plot commands')

    # Bias vs Beta Plot
    bias_parser = subparsers.add_parser('bias_vs_beta', help='Plot bias vs beta')
    bias_parser.add_argument('--input', type=str, required=True, help='Path to simulation_summary.csv')
    bias_parser.add_argument('--output', type=str, required=True, help='Path to output PNG')

    # Coverage vs Beta Plot
    coverage_parser = subparsers.add_parser('coverage_vs_beta', help='Plot coverage vs beta')
    coverage_parser.add_argument('--input', type=str, required=True, help='Path to simulation_summary.csv')
    coverage_parser.add_argument('--output', type=str, required=True, help='Path to output PDF')

    # Bias Distributions Plot
    dist_parser = subparsers.add_parser('bias_distributions', help='Plot bias distributions')
    dist_parser.add_argument('--input', type=str, required=True, help='Path to simulation_summary.csv')
    dist_parser.add_argument('--output', type=str, required=True, help='Path to output PNG')

    args = parser.parse_args()

    if args.command == 'bias_vs_beta':
        # Inject args into the plot_bias module's expected structure if needed
        # or call the main directly if it handles its own args.
        # Since plot_bias.py expects its own args, we simulate them.
        sys.argv = ['visualization.py', 
                    '--input', args.input, 
                    '--output', args.output]
        plot_bias_main()
    
    elif args.command == 'coverage_vs_beta':
        sys.argv = ['visualization.py', 
                    '--input', args.input, 
                    '--output', args.output]
        plot_coverage_main()
    
    elif args.command == 'bias_distributions':
        sys.argv = ['visualization.py', 
                    '--input', args.input, 
                    '--output', args.output]
        plot_distributions_main()
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
