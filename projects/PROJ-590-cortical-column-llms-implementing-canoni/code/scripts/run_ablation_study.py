import argparse
import logging
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.experiments.ablation import run_ablation_study, generate_ablation_configs

def main():
    parser = argparse.ArgumentParser(description="Run the ablation study.")
    parser.add_argument("--configs", type=str, default="data/configs/ablation_configs.json",
                        help="Path to ablation configs JSON.")
    parser.add_argument("--output", type=str, default="data/results/ablation_results.json",
                        help="Path to output results JSON.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Ensure configs exist
    if not os.path.exists(args.configs):
        logging.info(f"Config file {args.configs} not found. Generating now...")
        generate_ablation_configs(args.configs)

    logging.info(f"Running ablation study with configs: {args.configs}")
    try:
        results = run_ablation_study(configs_path=args.configs, output_path=args.output)
        logging.info(f"Study complete. Results written to {args.output}")
        for r in results:
            logging.info(f"Variant: {r.variant}, MAE: {r.mae:.4f}, Time: {r.time:.2f}s")
    except Exception as e:
        logging.error(f"Study failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
