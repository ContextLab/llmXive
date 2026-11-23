"""
Hold-out Physics Check for Cold Rolling Texture Evolution.

This module validates that observed texture trends (e.g., Brass component increase)
align with known physical expectations for FCC metals under cold rolling.
It ensures all findings are explicitly framed as associational relationships,
avoiding causal claims, in compliance with FR-006.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union

import pandas as pd
import numpy as np

# Import from project API surface
from utils.logging import get_logger
from config import get_reductions, get_data_path

logger = get_logger(__name__)

# Known physical expectations for FCC cold rolling (associational trends)
# Based on standard literature (e.g., Hirsch & Lücke, 1988; Dillamore & Katoh, 1974)
PHYSICAL_TRENDS = {
    "Brass": {
        "direction": "increase",
        "description": "Brass component ({110}<112>) typically increases with reduction in FCC metals",
        "min_slope": 0.02  # Minimum expected increase per % reduction
    },
    "Copper": {
        "direction": "increase",
        "description": "Copper component ({112}<111>) generally increases with reduction",
        "min_slope": 0.015
    },
    "S": {
        "direction": "increase",
        "description": "S component ({123}<634>) shows increasing trend with reduction",
        "min_slope": 0.01
    },
    "Goss": {
        "direction": "variable",
        "description": "Goss component ({110}<001>) behavior is material-dependent and less predictable",
        "min_slope": None
    },
    "Cube": {
        "direction": "decrease",
        "description": "Cube component ({100}<001>) typically decreases with cold rolling",
        "max_slope": -0.01  # Maximum expected decrease per % reduction
    }
}

def load_descriptors() -> pd.DataFrame:
    """
    Load the processed texture descriptors from the consolidated output.

    Returns:
        pd.DataFrame: Descriptors with columns: sample_id, material, reduction,
                     brass_vol, copper_vol, s_vol, goss_vol, cube_vol, texture_index
    """
    data_path = get_data_path()
    descriptors_file = data_path / "processed" / "descriptors.csv"

    if not descriptors_file.exists():
        raise FileNotFoundError(
            f"Descriptors file not found at {descriptors_file}. "
            "Run the descriptor extraction pipeline first."
        )

    df = pd.read_csv(descriptors_file)
    logger.info(f"Loaded {len(df)} descriptor records from {descriptors_file}")
    return df

def validate_trend_direction(
    df: pd.DataFrame,
    component: str,
    material: Optional[str] = None
) -> Tuple[bool, float, str]:
    """
    Validate that a specific texture component follows the expected physical trend.

    Args:
        df: DataFrame with descriptor data
        component: Texture component name (e.g., 'Brass', 'Copper')
        material: Optional material filter (e.g., 'Al', 'Cu', 'Ni')

    Returns:
        Tuple of (passes_check, observed_slope, message)
    """
    if component not in PHYSICAL_TRENDS:
        raise ValueError(f"Unknown component: {component}")

    trend_info = PHYSICAL_TRENDS[component]
    expected_direction = trend_info["direction"]

    # Filter data
    subset = df.copy()
    if material:
        subset = subset[subset["material"] == material]

    if len(subset) < 2:
        return False, 0.0, f"Insufficient data points ({len(subset)}) for trend analysis"

    # Sort by reduction
    subset = subset.sort_values("reduction")

    # Calculate slope using linear regression
    x = subset["reduction"].values
    y = subset[f"{component}_vol"].values

    # Handle constant values
    if np.std(y) == 0:
        slope = 0.0
    else:
        # Simple linear regression: slope = cov(x,y) / var(x)
        slope = np.cov(x, y, bias=True)[0, 1] / np.var(x)

    # Check against expected direction
    passes = True
    message_parts = []

    if expected_direction == "increase":
        if slope >= trend_info.get("min_slope", 0):
            message_parts.append(
                f"PASS: {component} shows expected increasing trend "
                f"(slope={slope:.4f} >= {trend_info['min_slope']:.4f})"
            )
        else:
            passes = False
            message_parts.append(
                f"FAIL: {component} slope ({slope:.4f}) below expected minimum "
                f"({trend_info['min_slope']:.4f})"
            )

    elif expected_direction == "decrease":
        if slope <= trend_info.get("max_slope", 0):
            message_parts.append(
                f"PASS: {component} shows expected decreasing trend "
                f"(slope={slope:.4f} <= {trend_info['max_slope']:.4f})"
            )
        else:
            passes = False
            message_parts.append(
                f"FAIL: {component} slope ({slope:.4f}) above expected maximum "
                f"({trend_info['max_slope']:.4f})"
            )

    elif expected_direction == "variable":
        message_parts.append(
            f"INFO: {component} trend is variable (material-dependent), "
            f"observed slope={slope:.4f}"
        )

    else:
        message_parts.append(
            f"WARNING: Unknown trend direction for {component}"
        )

    return passes, slope, "; ".join(message_parts)

def run_physics_check(
    df: pd.DataFrame,
    components: Optional[List[str]] = None,
    materials: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run the complete physics check across all specified components and materials.

    Args:
        df: Descriptor DataFrame
        components: List of components to check (default: all known)
        materials: List of materials to check separately (default: all in data)

    Returns:
        Dictionary with check results and associational framing
    """
    if components is None:
        components = list(PHYSICAL_TRENDS.keys())

    results = {
        "checks": [],
        "summary": {},
        "associational_framing": {
            "statement": (
              "All findings in this report represent ASSOCIATIONAL relationships "
              "between cold rolling reduction and texture component volume fractions. "
              "These correlations are consistent with established physical models of "
              "FCC crystal plasticity but do not establish causation. Other factors "
              "(e.g., stacking fault energy, initial grain size, temperature) may "
              "influence the observed associations."
            ),
            "disclaimer": (
              "This analysis validates that observed trends align with known physical "
              "expectations. Deviations may indicate material-specific behavior, "
              "measurement uncertainty, or the influence of unmodeled variables."
            )
        }
    }

    materials_to_check = materials if materials else df["material"].unique().tolist()

    for material in materials_to_check:
        material_df = df[df["material"] == material]
        material_results = {"material": material, "checks": []}

        for component in components:
            passes, slope, message = validate_trend_direction(
                material_df, component, material
            )
            material_results["checks"].append({
                "component": component,
                "passes": passes,
                "observed_slope": slope,
                "message": message
            })

        results["checks"].append(material_results)

    # Summary statistics
    total_checks = sum(
        len(m["checks"]) for m in results["checks"]
    )
    passed_checks = sum(
        sum(1 for c in m["checks"] if c["passes"])
        for m in results["checks"]
    )

    results["summary"] = {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "pass_rate": passed_checks / total_checks if total_checks > 0 else 0.0,
        "overall_status": "PASS" if passed_checks == total_checks else "PARTIAL"
    }

    return results

def generate_report(results: Dict[str, Any]) -> str:
    """
    Generate a human-readable report with explicit associational framing.

    Args:
        results: Output from run_physics_check()

    Returns:
        Formatted report string
    """
    lines = [
        "=" * 80,
        "HOLD-OUT PHYSICS CHECK REPORT",
        "=" * 80,
        "",
        "ASSOCIATIONAL FRAMING:",
        "-" * 40,
        results["associational_framing"]["statement"],
        "",
        results["associational_framing"]["disclaimer"],
        "",
        "SUMMARY:",
        "-" * 40,
        f"Total checks performed: {results['summary']['total_checks']}",
        f"Checks passed: {results['summary']['passed_checks']}",
        f"Pass rate: {results['summary']['pass_rate']:.1%}",
        f"Overall status: {results['summary']['overall_status']}",
        "",
        "DETAILED RESULTS BY MATERIAL:",
        "-" * 40,
    ]

    for material_result in results["checks"]:
        lines.append(f"\nMaterial: {material_result['material']}")
        for check in material_result["checks"]:
            status = "✓ PASS" if check["passes"] else "✗ FAIL"
            lines.append(f"  {status} | {check['component']}: {check['message']}")

    lines.extend([
        "",
        "=" * 80,
        "END OF REPORT",
        "=" * 80,
    ])

    return "\n".join(lines)

def main():
    """
    Main entry point for the physics check script.
    Loads descriptors, runs validation, and outputs a report.
    """
    logger.info("Starting physics check validation")

    try:
        # Load data
        df = load_descriptors()

        # Run physics check
        results = run_physics_check(df)

        # Generate and print report
        report = generate_report(results)
        print(report)

        # Save report to file
        data_path = get_data_path()
        report_file = data_path / "processed" / "physics_check_report.txt"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(report)
        logger.info(f"Report saved to {report_file}")

        # Exit with appropriate code
        if results["summary"]["overall_status"] == "PASS":
            sys.exit(0)
        else:
            logger.warning("Physics check completed with partial failures")
            sys.exit(0)  # Non-fatal for pipeline

    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Physics check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
