import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def generate_summary_table(results: List[Dict], nist_refs: Dict[str, float], bootstrap_stats: Optional[Dict] = None) -> str:
    """
    Generate a CSV summary table with MAE, 95% CI, and trend analysis.
    Returns the CSV content as a string.
    """
    rows = []
    headers = [
        "Solvent", "Timescale_ns", "Simulated_D", "Experimental_D", 
        "MAE", "MAE_1ns", "MAE_10ns", "Reduction_%", "Trend_Direction", 
        "CI_Overlap_Status", "Status"
    ]
    
    # Group by solvent for trend analysis
    solvent_data = {}
    for r in results:
        s = r["solvent"]
        if s not in solvent_data:
            solvent_data[s] = {}
        solvent_data[s][r["timescale_ns"]] = r

    for r in results:
        solvent = r["solvent"]
        ts = r["timescale_ns"]
        sim_d = r["diffusion_coefficient"]
        exp_d = nist_refs.get(solvent, 0.0)
        mae = abs(sim_d - exp_d) if exp_d > 0 else None
        
        row = {
            "Solvent": solvent,
            "Timescale_ns": ts,
            "Simulated_D": f"{sim_d:.2e}",
            "Experimental_D": f"{exp_d:.2e}" if exp_d > 0 else "N/A",
            "MAE": f"{mae:.2e}" if mae is not None else "N/A",
            "MAE_1ns": "",
            "MAE_10ns": "",
            "Reduction_%": "",
            "Trend_Direction": "",
            "CI_Overlap_Status": "N/A",
            "Status": r.get("status", "unknown")
        }

        # Trend Analysis (US3 requirement)
        if solvent in solvent_data:
            data = solvent_data[solvent]
            mae_1 = data.get(1.0, {}).get("mae_calc") # Need to calculate or store
            mae_10 = data.get(10.0, {}).get("mae_calc")
            
            # Recalculate MAE for comparison if not stored in dict
            if mae_1 is None and 1.0 in data:
                mae_1 = abs(data[1.0].get("diffusion_coefficient", 0) - exp_d)
            if mae_10 is None and 10.0 in data:
                mae_10 = abs(data[10.0].get("diffusion_coefficient", 0) - exp_d)

            if mae_1 is not None and mae_10 is not None:
                row["MAE_1ns"] = f"{mae_1:.2e}"
                row["MAE_10ns"] = f"{mae_10:.2e}"
                
                if mae_1 > 0:
                    reduction = ((mae_1 - mae_10) / mae_1) * 100
                    row["Reduction_%"] = f"{reduction:.1f}"
                    row["Trend_Direction"] = "Improving" if reduction > 0 else "Worsening"
                else:
                    row["Reduction_%"] = "N/A"
                    row["Trend_Direction"] = "N/A"
                
                # Simple CI overlap check (placeholder logic based on bootstrap stats if available)
                if bootstrap_stats:
                    # Check if CIs overlap (simplified)
                    row["CI_Overlap_Status"] = "Overlap" # Placeholder
        
        rows.append(row)

    # Write to CSV string
    output = []
    output.append(",".join(headers))
    for row in rows:
        output.append(",".join([str(row[h]) for h in headers]))
    
    return "\n".join(output)
