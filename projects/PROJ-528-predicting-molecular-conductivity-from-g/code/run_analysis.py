"""
Wrapper script to run the analysis pipeline with correct CLI arguments.
This script reconciles the quickstart.md command with the actual analysis.py implementation.
"""
import sys
import os

# Ensure code directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analysis import main

if __name__ == "__main__":
    # The quickstart calls: python code/analysis.py --results data/processed/model_results.json --plots data/processed/correlation_plots/
    # But analysis.py expects --data and --output.
    # We will intercept sys.argv to map the old arguments to the new ones.
    # However, the cleanest fix is to update the quickstart.md.
    # But per task instructions, we fix the script to accept the quickstart args if possible,
    # or ensure the script works with the intended data.
    
    # Since the error was "unrecognized arguments", we need to either:
    # 1. Update quickstart.md (not allowed in this task context as we are fixing the script)
    # 2. Make the script accept the old arguments for backward compatibility
    
    # We will add a check for --results and --plots and map them to --output and a placeholder for plots.
    # Note: The analysis.py script primarily needs --data (input) and --output (results).
    # The quickstart command is missing --data. We must assume a default or fail.
    # Looking at the error, the script failed because of unrecognized args.
    
    # Strategy: If --results is passed, treat it as --output.
    # If --data is missing, use the default DATA_PATH from config.
    
    import argparse
    
    # Check if we are being called with the old arguments
    if '--results' in sys.argv or '--plots' in sys.argv:
        new_argv = [sys.argv[0]]
        results_found = False
        plots_found = False
        
        i = 1
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == '--results':
                if i + 1 < len(sys.argv):
                    new_argv.extend(['--output', sys.argv[i+1]])
                    results_found = True
                    i += 2
                    continue
            elif arg == '--plots':
                # We ignore --plots for now as analysis.py doesn't generate plots directly (that's plot_top_features)
                # But we consume the argument to avoid error
                i += 2
                continue
            elif arg == '--data':
                new_argv.append(arg)
                if i + 1 < len(sys.argv):
                    new_argv.append(sys.argv[i+1])
                    i += 2
                    continue
            else:
                new_argv.append(arg)
            
            i += 1
        
        # If --data was not provided and --results was, we assume the user intended to run on default data
        # but we need to ensure --data exists. If not, we use the default from config.
        if '--data' not in new_argv and not results_found:
             # Fallback to default
             from code.config import DATA_PATH
             new_argv.extend(['--data', DATA_PATH])
        
        sys.argv = new_argv
    
    main()
