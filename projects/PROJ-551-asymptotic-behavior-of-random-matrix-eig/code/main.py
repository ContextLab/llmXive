import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is in path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from utils.config import ensure_directories
from analysis.simulation_loop import run_single_simulation
from analysis.results_recorder import save_single_run_results
from analysis.simulation_logging import log_simulation_start, log_simulation_end
from generators.wigner import generate_wigner_matrix

def _setup_file_logging():
    log_file = Path("data") / "logs" / "simulation_run.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Clear log for T001 to ensure it's not 0 bytes but contains the actual run
    # Fixed the TypeError: 'float' object is not callable by removing () from st_ctime
    # and adding a check to ensure file exists before stat()
    with open(log_file, "w") as f:
        f.write(f"Simulation Log - Started at {datetime.now(timezone.utc).isoformat()}\n")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)

def _ensure_raw_matrix(N: int, seed: int) -> Path:
    raw_dir = Path("data") / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"matrix_N{N}_seed{seed}.npy"
    if not raw_path.exists():
        logging.info(f"Raw matrix not found at {raw_path}. Generating on‑the‑fly.")
        matrix = generate_wigner_matrix(N, seed=seed)
        import numpy as np
        np.save(raw_path, matrix)
        logging.info(f"Generated raw matrix saved to {raw_path}")
    return raw_path

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='single')
    parser.add_argument('--N', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--theta', type=float, default=2.5)
    parser.add_argument('--k', type=int, default=1)
    parser.add_argument('--pattern', type=str, default='diagonal')
    parser.add_argument('--output', type=str, default='data/processed/single_run_results.json')
    return parser.parse_args()

def main():
    args = parse_args()
    ensure_directories()
    logger = _setup_file_logging()
    _ensure_raw_matrix(args.N, args.seed)

    if args.mode == 'single':
        params = {
            'N': args.N,
            'seed': args.seed,
            'theta': args.theta,
            'k': args.k,
            'pattern': args.pattern
        }
        logger.info(f"Starting single simulation with params: {params}")
        log_simulation_start(params)
        try:
            result = run_single_simulation(params)
            log_simulation_end(result)
            save_single_run_results(result, args.output)
            logger.info(f"Single run results written to {args.output}")
            print(json.dumps(result, indent=2))
            return 0
        except Exception as e:
            logger.error(f"Simulation failed: {e}", exc_info=True)
            return 1
    return 1

if __name__ == "__main__":
    sys.exit(main())
