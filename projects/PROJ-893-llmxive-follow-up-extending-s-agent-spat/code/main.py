import sys
import os
import argparse
import subprocess
from pathlib import Path
from config import Config
from validate.validate_citations import main as validate_citations_main

def run_pipeline():
    """Run the full research pipeline with citation validation gate."""
    print("Starting llmXive Symbolic Spatial Reasoning Pipeline...")
    
    # 0. VALIDATE CITATIONS (Gate: Abort if fails)
    print("Step 0: Validating citations in spec.md and plan.md...")
    try:
        # Prepare arguments for validate_citations
        # The script expects --spec and --plan flags based on task T005f description
        validate_args = [sys.executable, 'code/validate/validate_citations.py', '--spec', 'specs/001-symbolic-spatial-reasoning/spec.md', '--plan', 'specs/001-symbolic-spatial-reasoning/plan.md']
        result = subprocess.run(validate_args, check=True, capture_output=False)
        print("Citation validation passed.")
    except subprocess.CalledProcessError as e:
        print(f"CRITICAL: Citation validation failed. Aborting pipeline immediately.")
        sys.exit(1)
    except Exception as e:
        print(f"CRITICAL: Error during citation validation: {e}. Aborting pipeline.")
        sys.exit(1)
    
    # 1. Download
    print("Step 1: Downloading dataset...")
    try:
        subprocess.run([sys.executable, 'code/data/download.py', '--sample-size', '1000'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed at download step: {e}")
        sys.exit(1)
    
    # 2. Verify Checksum
    print("Step 2: Verifying checksums...")
    try:
        subprocess.run([sys.executable, 'code/data/verify_checksum.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed at checksum verification: {e}")
        sys.exit(1)
    
    # 3. Extract Geometry
    print("Step 3: Extracting geometry...")
    try:
        subprocess.run([sys.executable, 'code/data/extract_geometry.py', '--input', 'data/raw', '--output', 'data/derived/constraints.jsonl'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed at geometry extraction: {e}")
        sys.exit(1)
    
    # 4. Validate Distribution (HARD BLOCK)
    print("Step 4: Validating distribution...")
    try:
        subprocess.run([sys.executable, 'code/data/validate_distribution.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed at distribution validation: {e}")
        sys.exit(1)
    
    # 5. Dry Run
    print("Step 5: Running dry run...")
    try:
        subprocess.run([sys.executable, 'code/validate/dry_run.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed at dry run: {e}")
        sys.exit(1)
    
    # 6. VLM Audit (HARD BLOCK)
    print("Step 6: Auditing VLM traces...")
    try:
        subprocess.run([sys.executable, 'code/validate/vlm_audit.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed at VLM audit: {e}")
        sys.exit(1)
    
    # 7. Solve
    print("Step 7: Running solver...")
    try:
        subprocess.run([
            sys.executable, 'code/solver/run_solver.py',
            '--input', 'data/derived/constraints.jsonl',
            '--output', 'data/derived/predictions.jsonl',
            '--latency-log', 'data/derived/latency_log.jsonl',
            '--exclusion-log', 'data/derived/solver_failures.json'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed at solver execution: {e}")
        sys.exit(1)
    
    # 8. Generate Benchmark Results
    print("Step 8: Generating benchmark results...")
    try:
        subprocess.run([
            sys.executable, 'code/benchmark/generate_benchmark_results.py',
            '--predictions', 'data/derived/predictions.jsonl',
            '--vlm', 'data/derived/vlm_baseline.csv',
            '--ground_truth', 'data/derived/ground_truth.csv',
            '--output', 'data/results/benchmark_results.csv'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed at benchmark generation: {e}")
        sys.exit(1)
    
    # 9. Metrics (McNemar)
    print("Step 9: Calculating metrics...")
    try:
        subprocess.run([
            sys.executable, 'code/benchmark/metrics.py',
            '--input', 'data/results/benchmark_results.csv'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed at metrics calculation: {e}")
        sys.exit(1)
    
    # 10. Sensitivity Analysis
    print("Step 10: Running sensitivity analysis...")
    try:
        subprocess.run([
            sys.executable, 'code/benchmark/sensitivity.py',
            '--input', 'data/results/benchmark_results.csv',
            '--output', 'data/results/sensitivity_analysis.csv'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed at sensitivity analysis: {e}")
        sys.exit(1)
    
    # 11. Failure Analysis
    print("Step 11: Analyzing failures...")
    try:
        subprocess.run([
            sys.executable, 'code/benchmark/analyze_failures.py',
            '--results', 'data/results/benchmark_results.csv',
            '--output', 'data/derived/failure_classification.json'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed at failure analysis: {e}")
        sys.exit(1)
    
    # 12. Final Report
    print("Step 12: Generating final report...")
    try:
        subprocess.run([sys.executable, 'code/validate/final_report_generator.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed at final report generation: {e}")
        sys.exit(1)
    
    print("Pipeline completed successfully.")

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