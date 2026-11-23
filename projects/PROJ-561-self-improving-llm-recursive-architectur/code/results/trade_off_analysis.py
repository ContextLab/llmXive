import json
import os
from typing import List, Dict, Any, Optional
from results.trajectory_schema import read_trajectory, TrajectoryData
from config import get_config

def compute_trade_off_metrics(traj_data: TrajectoryData) -> List[Dict[str, Any]]:
    """
    Compute resource-performance trade-off metrics for each cycle.
    
    Calculates:
    - performance_per_flop: (gsm8k_accuracy + arc_accuracy) / total_flops
    - performance_per_hour: (gsm8k_accuracy + arc_accuracy) / training_time_hours
    
    Returns a list of dictionaries, one per cycle, containing the original
    metrics plus the computed trade-off ratios.
    """
    results = []
    
    for entry in traj_data.entries:
        # Avoid division by zero
        if entry.flops == 0 or entry.training_time_seconds == 0:
            continue
        
        # Aggregate performance score (simple sum of accuracies)
        # Note: ECE is an error metric, so we don't include it in the "higher is better" score
        performance_score = (entry.gsm8k_accuracy or 0.0) + (entry.arc_accuracy or 0.0)
        
        # Convert time to hours
        training_time_hours = entry.training_time_seconds / 3600.0
        
        # Compute ratios
        perf_per_flop = performance_score / entry.flops
        perf_per_hour = performance_score / training_time_hours
        
        cycle_metrics = {
            "cycle_number": entry.cycle_number,
            "param_count": entry.param_count,
            "gsm8k_accuracy": entry.gsm8k_accuracy,
            "arc_accuracy": entry.arc_accuracy,
            "wikitext2_ece": entry.wikitext2_ece,
            "flops": entry.flops,
            "training_time_seconds": entry.training_time_seconds,
            "performance_score": performance_score,
            "performance_per_flop": perf_per_flop,
            "performance_per_hour": perf_per_hour
        }
        
        results.append(cycle_metrics)
        
        # Detect diminishing returns: if perf_per_flop or perf_per_hour decreases
        # compared to the previous cycle (and we have a previous cycle)
        if len(results) > 1:
            prev = results[-2]
            curr = results[-1]
            
            diminishing_flops = curr["performance_per_flop"] < prev["performance_per_flop"]
            diminishing_hours = curr["performance_per_hour"] < prev["performance_per_hour"]
            
            if diminishing_flops or diminishing_hours:
                curr["diminishing_returns_detected"] = True
                if diminishing_flops and diminishing_hours:
                    curr["diminishing_returns_reason"] = "Both FLOP and time efficiency decreased"
                elif diminishing_flops:
                    curr["diminishing_returns_reason"] = "FLOP efficiency decreased"
                else:
                    curr["diminishing_returns_reason"] = "Time efficiency decreased"
            else:
                curr["diminishing_returns_detected"] = False
        else:
            results[-1]["diminishing_returns_detected"] = False
    
    return results

def generate_summary_statistics(metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate summary statistics across all cycles.
    
    Identifies:
    - Best cycle by performance_per_flop
    - Best cycle by performance_per_hour
    - Best cycle by raw performance score
    - Cycle where diminishing returns first appeared
    """
    if not metrics_list:
        return {
            "total_cycles": 0,
            "status": "No data available"
        }
    
    best_flop = max(metrics_list, key=lambda x: x["performance_per_flop"])
    best_hour = max(metrics_list, key=lambda x: x["performance_per_hour"])
    best_score = max(metrics_list, key=lambda x: x["performance_score"])
    
    # Find first cycle with diminishing returns
    diminishing_cycle = None
    for m in metrics_list:
        if m.get("diminishing_returns_detected", False):
            diminishing_cycle = m["cycle_number"]
            break
    
    return {
        "total_cycles": len(metrics_list),
        "best_efficiency_flops": {
            "cycle": best_flop["cycle_number"],
            "value": best_flop["performance_per_flop"]
        },
        "best_efficiency_time": {
            "cycle": best_hour["cycle_number"],
            "value": best_hour["performance_per_hour"]
        },
        "best_raw_performance": {
            "cycle": best_score["cycle_number"],
            "score": best_score["performance_score"]
        },
        "first_diminishing_returns_cycle": diminishing_cycle,
        "overall_trend": "improving" if diminishing_cycle is None else "diminishing_returns_at_cycle_" + str(diminishing_cycle)
    }

def main():
    """
    Main entry point for T033.
    
    Reads trajectory data from results/trajectory.json, computes trade-off
    metrics, and writes the analysis to results/trade_off_analysis.json.
    """
    config = get_config()
    trajectory_path = os.path.join(config.results_dir, "trajectory.json")
    output_path = os.path.join(config.results_dir, "trade_off_analysis.json")
    
    if not os.path.exists(trajectory_path):
        raise FileNotFoundError(
            f"Trajectory file not found at {trajectory_path}. "
            "Run the pipeline cycles first to generate trajectory data."
        )
    
    # Read trajectory
    traj_data = read_trajectory(trajectory_path)
    
    if not traj_data.entries:
        raise ValueError(
            f"Trajectory file {trajectory_path} contains no entries. "
            "Cannot compute trade-off metrics without cycle data."
        )
    
    # Compute metrics
    metrics_list = compute_trade_off_metrics(traj_data)
    
    # Generate summary
    summary = generate_summary_statistics(metrics_list)
    
    # Construct final output
    analysis_output = {
        "analysis_timestamp": traj_data.timestamp,
        "summary": summary,
        "cycle_metrics": metrics_list
    }
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_output, f, indent=2)
    
    print(f"Trade-off analysis written to: {output_path}")
    print(f"Summary: {summary}")

if __name__ == "__main__":
    main()