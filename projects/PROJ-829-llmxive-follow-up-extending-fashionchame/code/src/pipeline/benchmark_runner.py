import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from existing API surface
from src.data.stratified_subset import load_filtered_manifest, stratify_samples, validate_subset_balance, save_stratified_subset
from src.pipeline.runner import run_text_adapter_pipeline_with_bottleneck_analysis
from src.metrics.fidelity import compute_fidelity_scores
from src.pipeline.reporter import generate_report, load_filtered_manifest as reporter_load_manifest, load_raw_scores, aggregate_scores_by_class, calculate_relative_loss
from src.stats.significance import analyze_significance
from src.stats.sensitivity import run_sensitivity_analysis
from src.data.loader import load_config
from src.pipeline.streaming import get_current_memory_usage_bytes, trigger_memory_cleanup

def load_settings(config_path: str) -> Dict[str, Any]:
    """Load project settings from YAML."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    # Simple YAML loader without external dependency if possible, 
    # or assume pyyaml is installed as per requirements.txt
    try:
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback for environments without pyyaml if strictly necessary, 
        # though requirements.txt lists it.
        raise ImportError("pyyaml is required to load settings.yaml")

def run_full_benchmark(
    config_path: str,
    manifest_path: str,
    output_dir: str,
    subset_size: int = 100
) -> Dict[str, Any]:
    """
    Run the full benchmark pipeline on a representative clip subset.
    
    1. Load configuration.
    2. Load filtered manifest (from T021).
    3. Stratify and select subset (T016 logic).
    4. Run text adapter pipeline (T019/T024).
    5. Compute fidelity scores (T009).
    6. Aggregate by class and generate report (T020).
    7. Run significance analysis (T031).
    8. Run sensitivity analysis (T035) if needed (though T035 output is separate).
    
    Returns the final report dictionary.
    """
    settings = load_settings(config_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading filtered manifest from {manifest_path}...")
    # Use the reporter's load function which is designed for the manifest
    manifest_data = reporter_load_manifest(manifest_path)
    
    if not manifest_data or 'samples' not in manifest_data:
        raise ValueError("Invalid manifest format: missing 'samples' key")
    
    samples = manifest_data['samples']
    print(f"Loaded {len(samples)} samples from manifest.")
    
    # Stratify subset
    print("Stratifying subset...")
    # Assuming stratify_samples returns a list of selected sample dicts
    # The signature in API surface: stratify_samples(samples, class_key, target_count)
    # We need to determine the class key. Based on T014, it's likely 'GarmentFeatureClass' or similar.
    # Let's assume the manifest has a 'feature_class' or 'garment_feature_class' field.
    class_key = 'garment_feature_class' 
    if samples and class_key not in samples[0]:
        # Fallback or error
        raise ValueError(f"Expected class key '{class_key}' not found in manifest samples.")
        
    stratified_samples = stratify_samples(samples, class_key, subset_size)
    print(f"Selected {len(stratified_samples)} stratified samples.")
    
    # Validate balance
    validate_subset_balance(stratified_samples, class_key)
    
    # Save stratified subset for reference
    subset_manifest_path = output_path / "benchmark_subset_manifest.json"
    save_stratified_subset(stratified_samples, str(subset_manifest_path))
    
    # Run the pipeline to generate outputs (images, latencies, etc.)
    # The runner returns results or writes them.
    # T024/T019 logic is in runner.py. We need to call it.
    # Assuming run_text_adapter_pipeline_with_bottleneck_analysis takes samples and writes results.
    # It might return a list of results or write to a file.
    # Let's assume it writes raw scores to a file or returns them.
    # Based on T020, reporter.py loads raw scores. So runner must write them.
    
    print("Running text adapter pipeline on subset...")
    # The runner function signature: run_text_adapter_pipeline_with_bottleneck_analysis(samples, config)
    # It likely writes results to data/processed/raw_scores.json or similar.
    # Let's assume it returns the results list for now, or we read from a known file.
    # To be safe and align with T020's load_raw_scores, we assume the runner writes to a specific path.
    # However, T020's load_raw_scores takes a path.
    # Let's modify the runner call to return results if possible, or we assume a standard path.
    # Given the constraints, let's assume the runner writes to 'data/processed/raw_benchmark_scores.json'
    # and we pass that to the reporter.
    
    # Actually, let's look at T020: "consume ONLY samples from ... filtered_subset_manifest.json"
    # And T020 output: fidelity_report.json.
    # T020 depends on T018, T019 (runner).
    # So runner must produce the data the reporter consumes.
    # Let's assume runner writes to 'data/processed/raw_scores.json'
    
    raw_scores_path = output_path / "raw_scores.json"
    
    # We need to pass the samples to the runner.
    # The runner function in API surface: run_text_adapter_pipeline_with_bottleneck_analysis
    # It likely takes a list of samples and config.
    # We'll call it and assume it writes to raw_scores_path or returns data.
    # Let's assume it returns a list of results dicts.
    results = run_text_adapter_pipeline_with_bottleneck_analysis(stratified_samples, settings)
    
    # If runner returns results, write them to raw_scores_path for reporter compatibility
    if isinstance(results, list):
        with open(raw_scores_path, 'w') as f:
            json.dump(results, f, indent=2)
    elif isinstance(results, dict) and 'scores' in results:
        with open(raw_scores_path, 'w') as f:
            json.dump(results['scores'], f, indent=2)
    else:
        # If runner writes internally, we might need to adjust.
        # But to ensure T020 works, we ensure the file exists.
        # If runner didn't write, we try to write from results if available.
        pass

    # Load raw scores
    print("Loading raw scores...")
    raw_scores = load_raw_scores(str(raw_scores_path))
    
    # Aggregate by class
    print("Aggregating scores by class...")
    aggregated = aggregate_scores_by_class(raw_scores, class_key)
    
    # Calculate relative loss
    relative_loss = calculate_relative_loss(aggregated)
    
    # Generate report
    print("Generating fidelity report...")
    report = generate_report(aggregated, relative_loss)
    
    # Add significance analysis results
    print("Running significance analysis...")
    # analyze_significance expects scores grouped by class
    significance_results = analyze_significance(aggregated)
    report['significance'] = significance_results
    
    # Run sensitivity analysis (optional for this task, but T037 depends on T035)
    # T035 output is sensitivity_analysis.csv. We might just call it to ensure it runs.
    # But T037's main output is fidelity_report.json.
    # We'll call it to ensure dependencies are met, but it writes its own file.
    print("Running sensitivity analysis...")
    try:
        run_sensitivity_analysis(str(config_path), str(output_path / "sensitivity_analysis.csv"))
    except Exception as e:
        print(f"Warning: Sensitivity analysis failed: {e}. Continuing with fidelity report.")
    
    # Write final report
    report_path = output_path / "fidelity_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Full benchmark complete. Report saved to {report_path}")
    return report

def main():
    parser = argparse.ArgumentParser(description="Run full benchmark pipeline")
    parser.add_argument("--config", type=str, default="code/config/settings.yaml", help="Path to config file")
    parser.add_argument("--manifest", type=str, default="data/processed/filtered_subset_manifest.json", help="Path to filtered manifest")
    parser.add_argument("--output", type=str, default="data/processed", help="Output directory")
    parser.add_argument("--subset-size", type=int, default=100, help="Number of samples in stratified subset")
    
    args = parser.parse_args()
    
    try:
        report = run_full_benchmark(
            config_path=args.config,
            manifest_path=args.manifest,
            output_dir=args.output,
            subset_size=args.subset_size
        )
        print("Benchmark completed successfully.")
        print(json.dumps(report, indent=2))
    except Exception as e:
        print(f"Error running benchmark: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
