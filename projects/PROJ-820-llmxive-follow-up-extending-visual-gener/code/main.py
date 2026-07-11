"""
Main orchestration script for the llmXive Visual Generation pipeline.

Executes the pipeline in phases based on command-line flags:
--sim  : Run physics simulation (Phase 3: US1)
--gen  : Run image generation (Phase 4: US2)
--eval : Run evaluation (Phase 5: US3)
--analyze : Run statistical analysis (Phase 5: US3)

Usage:
  python code/main.py --sim
  python code/main.py --gen
  python code/main.py --eval
  python code/main.py --analyze
  python code/main.py --sim --gen --eval --analyze  (Full pipeline)
"""
import argparse
import sys
import os
from pathlib import Path

# Add project root to path to ensure imports work
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from setup.config import Config
from simulation.physics_engine import run_physics_simulation
from generation.prompt_engine import run_prompt_generation
from generation.diffusion_runner import run_diffusion_generation
from generation.reference_geometry import generate_reference_geometry
from evaluation.detector import run_evaluation
from analysis.statistics import (
    run_power_analysis_and_report,
    run_statistical_comparison,
    generate_final_analysis_csv,
    verify_contradiction_rate
)
from utils.update_state import update_state_file


def main():
    parser = argparse.ArgumentParser(description="llmXive Pipeline Orchestration")
    parser.add_argument("--sim", action="store_true", help="Run Physics Simulation phase")
    parser.add_argument("--gen", action="store_true", help="Run Image Generation phase")
    parser.add_argument("--eval", action="store_true", help="Run Evaluation phase")
    parser.add_argument("--analyze", action="store_true", help="Run Statistical Analysis phase")
    parser.add_argument("--full", action="store_true", help="Run all phases sequentially")
    
    args = parser.parse_args()

    # If no flags provided, default to full pipeline for convenience
    if not any([args.sim, args.gen, args.eval, args.analyze, args.full]):
        print("No phase flags provided. Defaulting to full pipeline (--full).")
        args.full = True

    # Initialize configuration
    config = Config()
    print(f"Pipeline initialized. Root: {project_root}")
    print(f"Random seed: {config.seed}")

    try:
        # --- Phase 3: Simulation (US1) ---
        if args.full or args.sim:
            print("\n[PHASE: SIMULATION] Starting physics simulation...")
            run_physics_simulation(config)
            print("[PHASE: SIMULATION] Completed.")

        # --- Phase 4: Generation (US2) ---
        if args.full or args.gen:
            print("\n[PHASE: GENERATION] Starting image generation...")
            # Ensure reference geometry is generated before diffusion
            print("[PHASE: GENERATION] Generating reference geometry...")
            generate_reference_geometry(config)
            
            print("[PHASE: GENERATION] Running prompt engineering...")
            run_prompt_generation(config)
            
            print("[PHASE: GENERATION] Running diffusion models...")
            run_diffusion_generation(config)
            print("[PHASE: GENERATION] Completed.")

        # --- Phase 5: Evaluation (US3) ---
        if args.full or args.eval:
            print("\n[PHASE: EVALUATION] Starting object detection and evaluation...")
            run_evaluation(config)
            print("[PHASE: EVALUATION] Completed.")

        # --- Phase 5: Analysis (US3) ---
        if args.full or args.analyze:
            print("\n[PHASE: ANALYSIS] Starting statistical analysis...")
            
            # 1. Verify Contradiction Rate (SC-004)
            print("[PHASE: ANALYSIS] Verifying contradiction rate...")
            is_valid = verify_contradiction_rate(config)
            if not is_valid:
                raise RuntimeError("Contradiction rate exceeds 5% threshold. Study halted.")
            
            # 2. Power Analysis
            print("[PHASE: ANALYSIS] Running power analysis...")
            run_power_analysis_and_report(config)
            
            # 3. Statistical Comparison
            print("[PHASE: ANALYSIS] Running statistical comparison...")
            run_statistical_comparison(config)
            
            # 4. Generate Final CSV
            print("[PHASE: ANALYSIS] Generating final analysis CSV...")
            generate_final_analysis_csv(config)
            
            print("[PHASE: ANALYSIS] Completed.")

        # Update state file with new artifacts
        print("\nUpdating state file...")
        update_state_file(config)

        print("\n=== PIPELINE EXECUTION SUCCESSFUL ===")

    except Exception as e:
        print(f"\n!!! PIPELINE EXECUTION FAILED: {e} !!!")
        sys.exit(1)


if __name__ == "__main__":
    main()