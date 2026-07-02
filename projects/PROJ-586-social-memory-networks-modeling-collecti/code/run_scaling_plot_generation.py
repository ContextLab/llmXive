import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from analysis.scaling import aggregate_metrics_by_agent_count
from analysis.scaling_plot_generator import generate_scaling_plot_with_notes

def aggregate_scaling_data(
    results_dir: Path,
    agent_counts: list = [3, 5, 7],
    games_per_config: int = 800
) -> pd.DataFrame:
    """
    Aggregate scaling data from individual experiment results.
    
    This function loads results from multiple experiment runs (one per agent count)
    and aggregates them into a single DataFrame with mean and standard deviation
    of specialization_index and retrieval_efficiency for each agent count.
    """
    all_data = []
    
    for agent_count in agent_counts:
        # Look for result files matching the pattern results_scaling_N.csv
        result_file = results_dir / f"results_scaling_{agent_count}.csv"
        
        if not result_file.exists():
            # Try alternative naming convention
            result_file = results_dir / f"scaling_results_{agent_count}.csv"
        
        if result_file.exists():
            df = pd.read_csv(result_file)
            df['agent_count'] = agent_count
            all_data.append(df)
        else:
            print(f"Warning: No result file found for agent_count={agent_count}")
    
    if not all_data:
        return pd.DataFrame()
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Aggregate by agent count
    aggregated = combined_df.groupby('agent_count').agg({
        'specialization_index': ['mean', 'std'],
        'retrieval_efficiency': ['mean', 'std']
    }).reset_index()
    
    # Flatten column names
    aggregated.columns = [
        'agent_count',
        'specialization_index_mean',
        'specialization_index_std',
        'retrieval_efficiency_mean',
        'retrieval_efficiency_std'
    ]
    
    # Replace NaN std with 0 (for single-game cases)
    aggregated['specialization_index_std'] = aggregated['specialization_index_std'].fillna(0)
    aggregated['retrieval_efficiency_std'] = aggregated['retrieval_efficiency_std'].fillna(0)
    
    return aggregated

def main():
    """Main entry point for scaling plot generation script."""
    parser = argparse.ArgumentParser(description='Run scaling plot generation pipeline')
    parser.add_argument('--results-dir', type=str, default='projects/PROJ-586-social-memory-networks-modeling-collecti/results',
                      help='Directory containing experiment results')
    parser.add_argument('--agent-counts', type=int, nargs='+', default=[3, 5, 7],
                      help='Agent counts to include in scaling analysis')
    parser.add_argument('--games-per-config', type=int, default=800,
                      help='Number of games per configuration')
    
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Aggregate data
    print(f"Aggregating scaling data for agent counts: {args.agent_counts}")
    aggregated_data = aggregate_scaling_data(
        results_dir,
        agent_counts=args.agent_counts,
        games_per_config=args.games_per_config
    )
    
    if aggregated_data.empty:
        print("Error: No scaling data found. Run scaling experiments first.")
        sys.exit(1)
    
    # Save aggregated data
    output_csv = results_dir / "scaling_metrics.csv"
    aggregated_data.to_csv(output_csv, index=False)
    print(f"Saved aggregated data to {output_csv}")
    
    # Generate plot
    print("Generating scaling plot with power-law fits...")
    result = generate_scaling_plot_with_notes(
        results_dir,
        agent_counts=args.agent_counts,
        games_per_config=args.games_per_config
    )
    
    print(result.message)
    if result.success:
        print(f"Output: {result.output_path}")
        if result.exponent is not None:
            print(f"Power-law exponent (β): {result.exponent:.4f}")
            if result.is_sublinear is not None:
                print(f"Sub-linear scaling (β < 1): {result.is_sublinear}")
        sys.exit(0)
    else:
        print("Failed to generate plot")
        sys.exit(1)

if __name__ == '__main__':
    main()
