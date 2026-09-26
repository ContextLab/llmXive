import sys
import os
import argparse
from pathlib import Path
from config import Config
from data.download import main as download_main
from data.verify_checksum import main as verify_checksum_main
from data.extract_geometry import main as extract_geometry_main
from validate.dry_run import main as dry_run_main
from validate.vlm_trace_auditor import main as vlm_audit_main
from solver.run_solver import main as solver_main
from benchmark.generate_benchmark_results import main as benchmark_gen_main
from benchmark.metrics import main as metrics_main
from benchmark.sensitivity import main as sensitivity_main
from benchmark.analyze_failures import main as failure_analysis_main
from validate.final_report_generator import main as report_gen_main

def run_pipeline():
    """Run the full research pipeline."""
    print("Starting llmXive Symbolic Spatial Reasoning Pipeline...")
    
    # 1. Download
    print("Step 1: Downloading dataset...")
    # Assuming download_main handles its own args or we pass defaults
    # For simplicity in main.py, we assume args are handled by individual scripts
    # or we set environment variables. Here we just call them.
    try:
        # We need to ensure the correct arguments are passed. 
        # In a real scenario, main.py would parse args and pass them.
        # For this implementation, we assume the scripts can run with defaults or 
        # we are invoking them via subprocess with specific args.
        # To keep it simple and robust as per the "fix the root cause" instruction:
        # We will simulate the command line arguments for each step.
        
        # Step 1: Download
        # sys.argv = ['main.py', 'download', '--sample-size', '1000']
        # download_main()
        # Instead, let's just call the logic directly if possible, or use subprocess
        # But the task says "extend, don't re-author". We assume the scripts have main()
        # that reads sys.argv. We will set sys.argv for each step.
        
        # We will execute the steps sequentially.
        
        # 1. Download
        print("Downloading...")
        # We assume the user has run the download script manually or via a wrapper
        # If we must automate:
        import subprocess
        subprocess.run([sys.executable, 'code/data/download.py', '--sample-size', '1000'], check=True)
        
        # 2. Verify Checksum
        print("Verifying checksums...")
        subprocess.run([sys.executable, 'code/data/verify_checksum.py'], check=True)
        
        # 3. Extract Geometry
        print("Extracting geometry...")
        subprocess.run([sys.executable, 'code/data/extract_geometry.py', '--input', 'data/raw', '--output', 'data/derived/constraints.jsonl'], check=True)
        
        # 4. Dry Run
        print("Running dry run...")
        subprocess.run([sys.executable, 'code/validate/dry_run.py'], check=True)
        
        # 5. VLM Audit
        print("Auditing VLM traces...")
        subprocess.run([sys.executable, 'code/validate/vlm_trace_auditor.py'], check=True)
        
        # 6. Solve
        print("Running solver...")
        subprocess.run([sys.executable, 'code/solver/run_solver.py', '--input', 'data/derived/constraints.jsonl', '--output', 'data/derived/predictions.jsonl', '--latency-log', 'data/derived/latency_log.jsonl', '--exclusion-log', 'data/derived/solver_failures.json'], check=True)
        
        # 7. Generate Benchmark Results
        print("Generating benchmark results...")
        subprocess.run([sys.executable, 'code/benchmark/generate_benchmark_results.py', '--predictions', 'data/derived/predictions.jsonl', '--vlm', 'data/derived/vlm_baseline.csv', '--ground_truth', 'data/derived/ground_truth.csv', '--output', 'data/results/benchmark_results.csv'], check=True)
        
        # 8. Metrics (McNemar)
        print("Calculating metrics...")
        subprocess.run([sys.executable, 'code/benchmark/metrics.py', '--input', 'data/results/benchmark_results.csv'], check=True)
        
        # 9. Sensitivity Analysis
        print("Running sensitivity analysis...")
        subprocess.run([sys.executable, 'code/benchmark/sensitivity.py', '--input', 'data/results/benchmark_results.csv', '--output', 'data/results/sensitivity_analysis.csv'], check=True)
        
        # 10. Failure Analysis
        print("Analyzing failures...")
        subprocess.run([sys.executable, 'code/benchmark/analyze_failures.py', '--results', 'data/results/benchmark_results.csv', '--output', 'data/derived/failure_classification.json'], check=True)
        
        # 11. Final Report
        print("Generating final report...")
        subprocess.run([sys.executable, 'code/validate/final_report_generator.py'], check=True)
        
        print("Pipeline completed successfully.")
        
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed at step: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Run the full llmXive research pipeline.')
    parser.add_argument('--full', action='store_true', help='Run the full pipeline.')
    args = parser.parse_args()
    
    if args.full:
        run_pipeline()
    else:
        print("Run with --full to execute the entire pipeline.")

if __name__ == '__main__':
    main()