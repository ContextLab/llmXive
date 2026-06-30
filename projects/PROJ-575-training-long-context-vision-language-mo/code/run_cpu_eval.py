import json
import os
from src.eval.model_loader import load_model
from src.eval.evaluator import run_inference
from src.eval.output_writer import serialize_results
from src.eval.evaluator import validate_benchmark_result

# Placeholder for main execution logic
# This script serves as the entry point, delegating to the new modules.
def main():
    model = load_model()
    results = run_inference(model)
    
    # Ensure results have the exact columns specified in FR-003
    required_columns = ['context_length', 'task_type', 'model_baseline_score', 'model_target_score']
    if results:
        for result in results:
            missing_cols = [col for col in required_columns if col not in result]
            if missing_cols:
                raise ValueError(f"Result missing required columns: {missing_cols}")
    
    # Validate against BenchmarkResult schema
    validate_benchmark_result(results)
    
    # Save to results/sample_results.json
    output_dir = 'results'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'sample_results.json')
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    serialize_results(results)

if __name__ == "__main__":
    main()
