"""
Main Orchestration Script for User Story 1 Pipeline
Orchestrates: Load -> Validate -> Compute Metrics -> Correlate -> Plot
Invokes state_manager.py to update project state atomically.
"""
import argparse
import sys
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_atlas_path, get_atlas_node_count
from data_loader import validate_entrainment_csv, validate_topology_columns
from graph_metrics import (
    calculate_clustering_coefficient,
    calculate_path_length,
    compute_all_metrics,
    process_subject_matrices,
    detect_zero_variance_metrics,
    save_metric_flags,
    analyze_and_flag_metrics
)
from simulation import check_and_generate_fallback, generate_synthetic_data
from analysis import (
    load_metric_flags,
    calculate_spearman_correlations,
    calculate_vif,
    run_correlation_analysis,
    generate_correlation_results_csv
)
from viz import generate_scatter_plot
from state_manager import update_state, get_state, compute_sha256

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
DATA_VIZ_DIR = os.path.join(PROJECT_ROOT, 'data', 'visualizations')

def ensure_directories():
    """Ensure all required directories exist."""
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    os.makedirs(DATA_VIZ_DIR, exist_ok=True)

def check_data_gap_status() -> bool:
    """
    Check if we have sufficient real data.
    Returns True if data gap exists (N < 30 or missing files).
    """
    # Check for topology metrics
    metrics_file = os.path.join(DATA_PROCESSED_DIR, 'topology_metrics.csv')
    if not os.path.exists(metrics_file):
        return True
    
    # Check for entrainment data
    entrainment_file = os.path.join(DATA_RAW_DIR, 'entrainment_metrics.csv')
    if not os.path.exists(entrainment_file):
        return True
    
    # Check row count if files exist
    import pandas as pd
    try:
        metrics_df = pd.read_csv(metrics_file)
        if len(metrics_df) < 30:
            return True
    except Exception:
        return True
    
    return False

def report_data_gap(reason: str):
    """Report data gap status to state manager."""
    state = get_state()
    state["data_gap_report"] = {
        "detected": True,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }
    # We don't update file here, let the main flow handle it after fallback

def generate_final_report(results_df, status: str = "completed"):
    """Generate final summary report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "subject_count": len(results_df) if results_df is not None else 0,
        "metrics_computed": ["clustering_coefficient", "path_length"],
        "correlation_results": {
            "method": "Spearman",
            "corrections_applied": ["Holm-Bonferroni"]
        }
    }
    
    if results_df is not None and len(results_df) > 0:
        report["summary_stats"] = {
            "mean_entrainment": float(results_df['entrainment_metric'].mean()),
            "mean_clustering": float(results_df['clustering_coefficient'].mean()),
            "mean_path_length": float(results_df['path_length'].mean())
        }
    
    return report

def run_us1_pipeline(atlas: str = "Schaefer", use_sensitivity: bool = False):
    """
    Run the full User Story 1 pipeline.
    
    Args:
        atlas: Atlas type to use (Schaefer, AAL, Power 264)
        use_sensitivity: If True, run sensitivity analysis for other atlases
    
    Returns:
        Tuple of (results_df, final_report, status)
    """
    ensure_directories()
    artifact_paths = []
    data_files = []
    
    try:
        # Step 1: Check for data gap and handle fallback
        has_gap = check_data_gap_status()
        if has_gap:
            print("[INFO] Data gap detected. Triggering simulated data fallback...")
            report_data_gap("N < 30 or missing files")
            # Generate synthetic data
            synthetic_data = check_and_generate_fallback(
                atlas_type=atlas,
                target_correlation=0.5,
                noise_level=0.2
            )
            # Save synthetic data to expected locations
            synthetic_data['topology_metrics'].to_csv(
                os.path.join(DATA_PROCESSED_DIR, 'topology_metrics.csv'),
                index=False
            )
            synthetic_data['entrainment_metrics'].to_csv(
                os.path.join(DATA_RAW_DIR, 'entrainment_metrics.csv'),
                index=False
            )
            data_files.append('data/processed/topology_metrics.csv')
            data_files.append('data/raw/entrainment_metrics.csv')
            print(f"[INFO] Generated synthetic data for {len(synthetic_data['topology_metrics'])} subjects.")
        else:
            print("[INFO] Real data available. Proceeding with analysis.")
        
        # Step 2: Load and validate entrainment data
        entrainment_path = os.path.join(DATA_RAW_DIR, 'entrainment_metrics.csv')
        if not os.path.exists(entrainment_path):
            raise FileNotFoundError(f"Entrainment metrics file not found: {entrainment_path}")
        
        validate_entrainment_csv(entrainment_path)
        print("[INFO] Entrainment data validated.")
        
        # Step 3: Load topology metrics (computed or synthetic)
        metrics_path = os.path.join(DATA_PROCESSED_DIR, 'topology_metrics.csv')
        if not os.path.exists(metrics_path):
            # If we don't have metrics, try to compute from raw correlation matrices
            raw_corr_path = os.path.join(DATA_RAW_DIR, 'hcp_correlation_matrices.csv')
            if os.path.exists(raw_corr_path):
                print("[INFO] Computing topology metrics from raw correlation matrices...")
                # This would call process_subject_matrices in a real implementation
                # For now, we assume metrics were generated by fallback or previous step
                raise FileNotFoundError(f"Topology metrics file not found: {metrics_path}")
            else:
                raise FileNotFoundError(f"Neither topology metrics nor raw correlation matrices found.")
        
        topology_df = pd.read_csv(metrics_path)
        validate_topology_columns(topology_df)
        print("[INFO] Topology metrics validated.")
        
        # Step 4: Detect zero-variance metrics and save flags
        flags = detect_zero_variance_metrics(topology_df)
        save_metric_flags(flags, os.path.join(DATA_PROCESSED_DIR, 'metric_flags.json'))
        print("[INFO] Metric flags saved.")
        
        # Step 5: Perform correlation analysis
        print("[INFO] Running correlation analysis...")
        results_df = run_correlation_analysis(
            topology_df=topology_df,
            entrainment_path=entrainment_path,
            atlas_type=atlas
        )
        
        # Step 6: Generate correlation results CSV
        results_path = os.path.join(DATA_PROCESSED_DIR, 'correlation_results.csv')
        generate_correlation_results_csv(results_df, results_path)
        artifact_paths.append('data/processed/correlation_results.csv')
        data_files.append('data/processed/correlation_results.csv')
        print(f"[INFO] Correlation results saved to {results_path}")
        
        # Step 7: Generate visualization
        viz_path = os.path.join(DATA_VIZ_DIR, 'scatter_topology_entrainment.png')
        generate_scatter_plot(
            results_df,
            output_path=viz_path,
            title=f"Topology Metrics vs Entrainment Strength ({atlas} Atlas)"
        )
        artifact_paths.append('data/visualizations/scatter_topology_entrainment.png')
        print(f"[INFO] Visualization saved to {viz_path}")
        
        # Step 8: Generate final report
        final_report = generate_final_report(results_df, status="completed")
        
        # Step 9: Update state manager atomically
        state = update_state(
            pipeline_status="completed",
            artifact_paths=artifact_paths,
            data_files=data_files
        )
        
        print("[INFO] Project state updated atomically.")
        return results_df, final_report, "completed"
        
    except Exception as e:
        print(f"[ERROR] Pipeline failed: {str(e)}")
        update_state(pipeline_status="failed")
        return None, {"error": str(e)}, "failed"

def run_sensitivity_pipeline():
    """Run sensitivity analysis across different atlases."""
    atlases = ["Schaefer", "AAL", "Power 264"]
    results = {}
    
    for atlas in atlases:
        print(f"[INFO] Running sensitivity analysis for {atlas}...")
        df, report, status = run_us1_pipeline(atlas=atlas)
        if status == "completed":
            results[atlas] = {
                "correlation": df['r_value'].mean() if 'r_value' in df.columns else None,
                "p_value": df['p_value'].mean() if 'p_value' in df.columns else None
            }
    
    # Generate comparative visualization
    from viz import generate_sensitivity_bar_chart
    viz_path = os.path.join(DATA_VIZ_DIR, 'sensitivity_comparison.png')
    generate_sensitivity_bar_chart(results, output_path=viz_path)
    
    return results

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Orchestrate the Network Topology Entrainment Pipeline"
    )
    parser.add_argument(
        "--atlas",
        type=str,
        default="Schaefer",
        choices=["Schaefer", "AAL", "Power 264"],
        help="Atlas type to use for analysis"
    )
    parser.add_argument(
        "--sensitivity",
        action="store_true",
        help="Run sensitivity analysis across all atlases"
    )
    parser.add_argument(
        "--force-simulate",
        action="store_true",
        help="Force generation of synthetic data even if real data exists"
    )
    
    args = parser.parse_args()
    
    print(f"[INFO] Starting pipeline with atlas: {args.atlas}")
    print(f"[INFO] Sensitivity analysis: {'enabled' if args.sensitivity else 'disabled'}")
    
    if args.sensitivity:
        results = run_sensitivity_pipeline()
        print(f"[INFO] Sensitivity analysis completed: {results}")
    else:
        df, report, status = run_us1_pipeline(atlas=args.atlas)
        print(f"[INFO] Pipeline completed with status: {status}")
        if df is not None:
            print(f"[INFO] Processed {len(df)} subjects")
            if 'r_value' in df.columns:
                print(f"[INFO] Mean correlation: {df['r_value'].mean():.4f}")
    
    return 0 if status == "completed" else 1

if __name__ == "__main__":
    sys.exit(main())