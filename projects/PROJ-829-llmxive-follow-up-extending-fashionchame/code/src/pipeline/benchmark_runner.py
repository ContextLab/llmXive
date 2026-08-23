"""
Benchmark Runner for Task T037.
Executes the full benchmark pipeline on a representative subset and generates the final fidelity report.
"""
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import existing components from the project API surface
from src.data.stratified_subset import load_filtered_manifest, stratify_samples, save_stratified_subset
from src.data.loader import load_deepfashion2_streaming, process_batch, iterate_dataset
from src.pipeline.runner import run_text_adapter_pipeline_with_bottleneck_analysis
from src.pipeline.reporter import load_raw_scores, aggregate_scores_by_class, calculate_relative_loss, generate_report
from src.pipeline.streaming import process_batch_with_memory_check, get_current_memory_usage_bytes
from src.pipeline.manifest import calculate_file_hash, write_manifest
from src.metrics.latency import measure_inference_latency, evaluate_latency_pass_fail
from src.stats.significance import perform_anova, bonferroni_correction, analyze_significance
from src.stats.sensitivity import run_sensitivity_analysis
from src.data.prompt_gen import generate_prompt
from src.adapters.text_cross_attention import load_adapter_from_config

def load_settings() -> Dict[str, Any]:
    """Load configuration from settings.yaml."""
    from src.data.loader import load_config
    return load_config()

def run_full_benchmark(subset_size: int = 100, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run the full benchmark on a representative clip subset.
    
    Args:
        subset_size: Number of samples to process (stratified).
        output_dir: Directory to write outputs. Defaults to data/processed/.
    
    Returns:
        Dictionary containing benchmark results.
    """
    if output_dir is None:
        output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    settings = load_settings()
    
    # Step 1: Load filtered manifest
    filtered_manifest_path = Path("data/processed/filtered_subset_manifest.json")
    if not filtered_manifest_path.exists():
        raise FileNotFoundError(f"Filtered manifest not found at {filtered_manifest_path}. Run feasibility_filter first.")
    
    manifest_data = load_filtered_manifest(filtered_manifest_path)
    print(f"Loaded {len(manifest_data)} samples from filtered manifest.")

    # Step 2: Stratify and select subset
    stratified_data = stratify_samples(manifest_data, subset_size)
    print(f"Selected {len(stratified_data)} stratified samples.")

    # Save stratified subset manifest
    subset_manifest_path = output_dir / "stratified_subset_manifest.json"
    save_stratified_subset(stratified_data, subset_manifest_path)
    print(f"Saved stratified subset manifest to {subset_manifest_path}")

    # Step 3: Load adapter
    adapter_config_path = Path("code/config/adapter_config.yaml")
    if adapter_config_path.exists():
        adapter = load_adapter_from_config(adapter_config_path)
    else:
        # Fallback to default initialization if config not found
        from src.adapters.text_cross_attention import TextCrossAttentionAdapter
        adapter = TextCrossAttentionAdapter()
        print("Using default TextCrossAttentionAdapter (no config file found).")

    # Step 4: Process samples and collect raw scores
    raw_scores = []
    latency_scores = []
    sample_count = 0

    print("Starting benchmark execution...")
    start_time = time.time()

    for sample in stratified_data:
        # Check memory usage
        current_mem = get_current_memory_usage_bytes()
        if current_mem > settings.get("memory_trigger_gb", 6.5) * 1024 * 1024 * 1024:
            print("Memory threshold exceeded, triggering cleanup...")
            import gc
            gc.collect()

        try:
            # Generate prompt
            prompt = generate_prompt(sample, settings)
            
            # Run text adapter pipeline with bottleneck analysis
            result = run_text_adapter_pipeline_with_bottleneck_analysis(
                sample=sample,
                prompt=prompt,
                adapter=adapter,
                settings=settings
            )
            
            # Extract scores
            if result.get("lpips_score") is not None:
                raw_scores.append({
                    "sample_id": sample.get("id"),
                    "image_id": sample.get("image_id"),
                    "garment_class": sample.get("garment_feature_class"),
                    "lpips": result["lpips_score"],
                    "ssim": result.get("ssim_score", 0.0),
                    "latency_ms": result.get("inference_time_ms", 0.0)
                })
                latency_scores.append(result.get("inference_time_ms", 0.0))
                sample_count += 1

        except Exception as e:
            print(f"Error processing sample {sample.get('id')}: {e}")
            continue

    total_time = time.time() - start_time
    print(f"Benchmark completed in {total_time:.2f} seconds. Processed {sample_count} samples.")

    # Step 5: Save raw scores
    raw_scores_path = output_dir / "raw_fidelity_scores.json"
    with open(raw_scores_path, "w") as f:
        json.dump(raw_scores, f, indent=2)
    print(f"Saved raw scores to {raw_scores_path}")

    # Step 6: Aggregate scores by class and generate report
    aggregated = aggregate_scores_by_class(raw_scores)
    relative_loss = calculate_relative_loss(aggregated)
    report = generate_report(aggregated, relative_loss)
    
    # Add latency statistics
    if latency_scores:
        avg_latency = sum(latency_scores) / len(latency_scores)
        pass_fail = evaluate_latency_pass_fail(avg_latency, settings.get("latency_threshold_ms", 50))
        report["latency"] = {
            "average_ms": avg_latency,
            "status": pass_fail.get("status", "UNKNOWN"),
            "threshold_ms": settings.get("latency_threshold_ms", 50)
        }

    # Step 7: Perform statistical significance analysis
    try:
        anova_result = perform_anova(raw_scores, "garment_class", "lpips")
        bonferroni_result = bonferroni_correction(anova_result.get("p_value", 1.0), num_tests=3)
        report["significance"] = {
            "anova": anova_result,
            "bonferroni": bonferroni_result
        }
    except Exception as e:
        print(f"Warning: Statistical analysis failed: {e}")
        report["significance"] = {"error": str(e)}

    # Step 8: Run sensitivity analysis (if motion labels available)
    try:
        motion_labels_path = output_dir / "motion_labels.json"
        if motion_labels_path.exists():
            sensitivity_result = run_sensitivity_analysis(raw_scores, motion_labels_path)
            report["sensitivity"] = sensitivity_result
            
            # Save sensitivity analysis CSV
            sensitivity_csv_path = output_dir / "sensitivity_analysis.csv"
            with open(sensitivity_csv_path, "w") as f:
                f.write("threshold,fp_rate,fn_rate\n")
                for entry in sensitivity_result.get("threshold_analysis", []):
                    f.write(f"{entry['threshold']},{entry['fp_rate']},{entry['fn_rate']}\n")
            print(f"Saved sensitivity analysis to {sensitivity_csv_path}")
    except Exception as e:
        print(f"Warning: Sensitivity analysis skipped: {e}")

    # Step 9: Save final fidelity report
    report_path = output_dir / "fidelity_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved final fidelity report to {report_path}")

    # Step 10: Generate manifest for this run
    manifest_entries = [
        {"path": str(raw_scores_path.relative_to(Path("data/processed"))), "hash": calculate_file_hash(raw_scores_path)},
        {"path": str(report_path.relative_to(Path("data/processed"))), "hash": calculate_file_hash(report_path)},
        {"path": str(subset_manifest_path.relative_to(Path("data/processed"))), "hash": calculate_file_hash(subset_manifest_path)}
    ]
    
    run_manifest_path = output_dir / "benchmark_manifest.json"
    write_manifest(manifest_entries, run_manifest_path)
    print(f"Saved run manifest to {run_manifest_path}")

    return report

def main():
    parser = argparse.ArgumentParser(description="Run full benchmark pipeline (Task T037)")
    parser.add_argument("--subset-size", type=int, default=100, help="Number of samples to process")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory")
    args = parser.parse_args()

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        report = run_full_benchmark(subset_size=args.subset_size, output_dir=output_path)
        print("\n=== BENCHMARK COMPLETE ===")
        print(f"Report saved to: {output_path / 'fidelity_report.json'}")
        print(json.dumps(report, indent=2))
    except Exception as e:
        print(f"Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
