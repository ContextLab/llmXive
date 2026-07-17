import os
import sys
import json
import time
import subprocess
import psutil
from pathlib import Path
from datetime import datetime

# Ensure we can import from the code directory
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

def get_memory_usage_gb():
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024 * 1024)

def run_pipeline_step(step_name, script_path, description):
    """Run a pipeline step and return success status and timing."""
    print(f"Running: {description}")
    print(f"  Script: {script_path}")
    
    start_time = time.time()
    peak_memory = get_memory_usage_gb()
    
    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout per step
            cwd=str(code_root)
        )
        
        end_time = time.time()
        current_memory = get_memory_usage_gb()
        peak_memory = max(peak_memory, current_memory)
        
        if result.returncode != 0:
            print(f"  FAILED: {result.stderr}")
            return {
                "step": step_name,
                "description": description,
                "status": "failed",
                "error": result.stderr,
                "runtime_seconds": end_time - start_time,
                "peak_memory_gb": peak_memory
            }
        
        print(f"  SUCCESS: {result.stdout[-200:] if result.stdout else 'No output'}")
        return {
            "step": step_name,
            "description": description,
            "status": "success",
            "runtime_seconds": end_time - start_time,
            "peak_memory_gb": peak_memory
        }
        
    except subprocess.TimeoutExpired:
        return {
            "step": step_name,
            "description": description,
            "status": "timeout",
            "error": "Step exceeded 1 hour timeout",
            "runtime_seconds": 3600,
            "peak_memory_gb": peak_memory
        }
    except Exception as e:
        return {
            "step": step_name,
            "description": description,
            "status": "error",
            "error": str(e),
            "runtime_seconds": 0,
            "peak_memory_gb": peak_memory
        }

def main():
    """Execute the full pipeline and generate final execution log."""
    print("=" * 60)
    print("EXECUTING FULL PIPELINE FOR T043")
    print("=" * 60)
    
    pipeline_start = time.time()
    initial_memory = get_memory_usage_gb()
    overall_peak_memory = initial_memory
    
    results = []
    
    # Step 1: Data Verification
    step = run_pipeline_step(
        "T012",
        code_root / "data/verify.py",
        "Data Source Verification and Schema Validation"
    )
    results.append(step)
    overall_peak_memory = max(overall_peak_memory, step.get("peak_memory_gb", 0))
    if step["status"] != "success":
        print("Pipeline failed at data verification. Aborting.")
        return generate_final_log(results, pipeline_start, overall_peak_memory, False)
    
    # Step 2: Data Download
    step = run_pipeline_step(
        "T013",
        code_root / "data/download.py",
        "Data Download (Streaming)"
    )
    results.append(step)
    overall_peak_memory = max(overall_peak_memory, step.get("peak_memory_gb", 0))
    if step["status"] != "success":
        print("Pipeline failed at data download. Aborting.")
        return generate_final_log(results, pipeline_start, overall_peak_memory, False)
    
    # Step 3: Preprocessing
    step = run_pipeline_step(
        "T014-T018",
        code_root / "data/preprocess.py",
        "Data Preprocessing (Normalization, Co-occurrence, Similarity, Role)"
    )
    results.append(step)
    overall_peak_memory = max(overall_peak_memory, step.get("peak_memory_gb", 0))
    if step["status"] != "success":
        print("Pipeline failed at preprocessing. Aborting.")
        return generate_final_log(results, pipeline_start, overall_peak_memory, False)
    
    # Step 4: Data Split
    step = run_pipeline_step(
        "T019",
        code_root / "data/split.py",
        "Train/Test Split and Downsampling"
    )
    results.append(step)
    overall_peak_memory = max(overall_peak_memory, step.get("peak_memory_gb", 0))
    if step["status"] != "success":
        print("Pipeline failed at data split. Aborting.")
        return generate_final_log(results, pipeline_start, overall_peak_memory, False)
    
    # Step 5: VIF Diagnostics
    step = run_pipeline_step(
        "T023",
        code_root / "models/diagnostics.py",
        "Variance Inflation Factor Calculation"
    )
    results.append(step)
    overall_peak_memory = max(overall_peak_memory, step.get("peak_memory_gb", 0))
    if step["status"] != "success":
        print("Pipeline failed at VIF diagnostics. Aborting.")
        return generate_final_log(results, pipeline_start, overall_peak_memory, False)
    
    # Step 6: Logistic Model
    step = run_pipeline_step(
        "T022",
        code_root / "models/fit_logistic.py",
        "Logistic Regression Model Fitting"
    )
    results.append(step)
    overall_peak_memory = max(overall_peak_memory, step.get("peak_memory_gb", 0))
    if step["status"] != "success":
        print("Pipeline failed at logistic model fitting. Aborting.")
        return generate_final_log(results, pipeline_start, overall_peak_memory, False)
    
    # Step 7: Likelihood Ratio Test
    step = run_pipeline_step(
        "T024",
        code_root / "models/diagnostics.py",
        "Likelihood Ratio Test"
    )
    results.append(step)
    overall_peak_memory = max(overall_peak_memory, step.get("peak_memory_gb", 0))
    if step["status"] != "success":
        print("Pipeline failed at LRT. Aborting.")
        return generate_final_log(results, pipeline_start, overall_peak_memory, False)
    
    # Step 8: Bayesian Model
    step = run_pipeline_step(
        "T025",
        code_root / "models/fit_bayesian.py",
        "Hierarchical Bayesian Model Fitting"
    )
    results.append(step)
    overall_peak_memory = max(overall_peak_memory, step.get("peak_memory_gb", 0))
    if step["status"] != "success":
        print("Pipeline failed at Bayesian model fitting. Aborting.")
        return generate_final_log(results, pipeline_start, overall_peak_memory, False)
    
    # Step 9: Evaluation Metrics
    step = run_pipeline_step(
        "T029",
        code_root / "evaluation/metrics.py",
        "Model Evaluation Metrics"
    )
    results.append(step)
    overall_peak_memory = max(overall_peak_memory, step.get("peak_memory_gb", 0))
    if step["status"] != "success":
        print("Pipeline failed at evaluation. Aborting.")
        return generate_final_log(results, pipeline_start, overall_peak_memory, False)
    
    # Step 10: Report Generation
    step = run_pipeline_step(
        "T030-T032",
        code_root / "evaluation/report.py",
        "Statistical Comparison and Report Generation"
    )
    results.append(step)
    overall_peak_memory = max(overall_peak_memory, step.get("peak_memory_gb", 0))
    
    pipeline_end = time.time()
    total_runtime = pipeline_end - pipeline_start
    
    # Determine overall success
    all_success = all(r["status"] == "success" for r in results)
    
    return generate_final_log(results, pipeline_start, overall_peak_memory, all_success)

def generate_final_log(results, start_time, peak_memory, success):
    """Generate the final execution log JSON."""
    end_time = time.time()
    
    log_data = {
        "execution_id": datetime.now().isoformat(),
        "task_id": "T043",
        "status": "success" if success else "failed",
        "total_runtime_seconds": end_time - start_time,
        "peak_memory_gb": round(peak_memory, 3),
        "steps": results,
        "artifacts_generated": [
            "data/verification_report.json",
            "data/downloaded_datasets/",
            "data/processed/cooccurrence_matrix.parquet",
            "data/processed/flavor_similarity.parquet",
            "data/processed/functional_role.parquet",
            "data/splits/train_test_split.parquet",
            "data/vif_results.json",
            "data/logistic_model.pkl",
            "data/lrt_result.json",
            "data/bayesian_model.pkl",
            "data/bayesian_convergence.json",
            "data/evaluation_metrics.json",
            "data/auc_delta_metrics.json",
            "data/model_comparison.json",
            "data/final_execution_log.json"
        ]
    }
    
    # Write the log
    output_path = code_root / "data/final_execution_log.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    print("\n" + "=" * 60)
    print("PIPELINE EXECUTION COMPLETE")
    print(f"Status: {'SUCCESS' if success else 'FAILED'}")
    print(f"Total Runtime: {log_data['total_runtime_seconds']:.2f} seconds")
    print(f"Peak Memory: {log_data['peak_memory_gb']:.3f} GB")
    print(f"Log saved to: {output_path}")
    print("=" * 60)
    
    return log_data

if __name__ == "__main__":
    main()