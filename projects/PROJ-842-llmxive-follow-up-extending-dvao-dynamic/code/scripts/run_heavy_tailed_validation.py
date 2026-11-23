"""
Script to run heavy-tailed Pareto validation and generate output file.
Implements T034d verification requirement.
"""
import os
import sys
import argparse
import json
from src.analysis.stats import validate_heavy_tailed_pareto
from src.environment.synthetic_mdp import generate_heavy_tailed_mdp

def main():
    parser = argparse.ArgumentParser(
        description="Run heavy-tailed Pareto frontier validation"
    )
    parser.add_argument(
        "--n-objectives",
        type=int,
        default=5,
        help="Number of objectives (default: 5)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        help="Deviation threshold percentage (default: 10.0)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/heavy_tailed_results.json",
        help="Output file path (default: data/processed/heavy_tailed_results.json)"
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    print(f"Running heavy-tailed Pareto validation...")
    print(f"  N objectives: {args.n_objectives}")
    print(f"  Seed: {args.seed}")
    print(f"  Threshold: {args.threshold}%")
    print(f"  Output: {args.output}")
    
    try:
        deviation, passed = validate_heavy_tailed_pareto(
            n_objectives=args.n_objectives,
            seed=args.seed,
            threshold_percent=args.threshold,
            output_path=args.output
        )
        
        print(f"\nResults:")
        print(f"  Deviation metric: {deviation:.4f}%")
        print(f"  Threshold passed: {passed}")
        
        # Verify file was created
        if os.path.exists(args.output):
            with open(args.output, 'r') as f:
                results = json.load(f)
            print(f"\nOutput file verified: {args.output}")
            print(f"  threshold_passed in file: {results['threshold_passed']}")
            
            # Exit with appropriate code
            if passed:
                print("\nValidation PASSED")
                sys.exit(0)
            else:
                print("\nValidation FAILED (threshold not met)")
                sys.exit(0)  # Still exit 0 as the script ran successfully
        else:
            print(f"\nERROR: Output file not created at {args.output}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()