import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from existing API surface
# Note: analysis.py provides welch_t_test, calculate_cohen_d, etc., but T022
# is a report generation task that aggregates results from T019, T020, T021.
# We assume T019, T020, T021 have already written their intermediate results
# to data/results/ or data/processed/ as per the task chain.
# Specifically:
#   - T019 writes bonferroni results (likely to data/results/bonferroni_results.json or similar)
#   - T020 writes effect sizes (likely to data/results/effect_sizes.json or similar)
#   - T021 writes power analysis (likely to data/results/statistical_report.json with power/MDES)
#
# However, looking at the provided API surface for task_t021_power_analysis:
#   It has functions: load_cleaned_dataset, load_statistical_report, save_statistical_report, calculate_power_and_mdes, run_power_analysis, main
#   And task_t021 is marked as completed, so we expect data/results/statistical_report.json to exist with power/MDES.
#
# For T022, we need to:
#   1. Load the cleaned dataset (to get group stats if needed, but mostly for context)
#   2. Load the statistical analysis results (from T018, T019, T020) - but note: T021 already updated the report with power/MDES.
#   3. Load the power analysis results (which T021 already integrated into the report)
#   4. Compile a final report that includes: p-values, corrected p-values, effect sizes, power, MDES.
#
# Given the dependencies, it's likely that T021 (power analysis) has already written the final report structure
# to data/results/statistical_report.json. However, T022 is tasked with generating that report.
#
# Let's re-read the task: "Generate `data/results/statistical_report.json` containing p-values, corrected p-values, effect sizes, power, MDES, and power analysis results."
#
# Since T021 is a dependency and it writes to the same file, we must ensure we are not overwriting T021's work but rather
# T022 is the task that finalizes the report. However, the task chain says T022 depends on T019, T020, T021.
#
# Approach:
#   We will assume that T019 and T020 have written their results to temporary files or that the main analysis (T018) wrote a base report.
#   Then T021 updated that report with power and MDES.
#   Now T022 is responsible for ensuring the final report is complete and saved to data/results/statistical_report.json.
#
# But note: the provided API surface for task_t021_power_analysis has a function `save_statistical_report` and `run_power_analysis` that likely
# writes the report with power/MDES. So T022 might be redundant? However, the task exists and must be implemented.
#
# Alternative interpretation: T022 is the task that aggregates all the results from T019 (bonferroni), T020 (effect sizes), and T021 (power) into one report.
# Since T021 already writes to the same file, we must coordinate.
#
# Let's look at the task_t021_power_analysis API: it has `load_statistical_report` and `save_statistical_report`. So T021 reads a base report (from T018/T019/T020?),
# adds power/MDES, and saves. Then T022 might be intended to do the same? But that would be duplication.
#
# Given the ambiguity, I will implement T022 as follows:
#   - It will load the cleaned dataset (to verify data exists)
#   - It will load the statistical results from T019 (bonferroni) and T020 (effect sizes) if they are in separate files, OR
#     if T021 has already written the report, then T022 will just validate and re-save it (ensuring it meets the spec).
#   - However, the task says "Generate", so we must create the report from the components.
#
# Since the task dependencies are T019, T020, T021, and T021 already writes the report, I think the intention is that T022 is the final step that
# compiles the report by reading the intermediate results from T019 and T020 (if they are in separate files) and T021's power analysis.
#
# But the provided API surface for task_t021_power_analysis shows it writes to the same report file. So to avoid conflict, we assume:
#   T019 writes bonferroni results to a temporary file (e.g., data/results/bonferroni_temp.json)
#   T020 writes effect sizes to a temporary file (e.g., data/results/effect_sizes_temp.json)
#   T021 writes power analysis to the main report (data/results/statistical_report.json) but without the full context? 
#   Then T022 merges them.
#
# However, the task description for T021 says: "Append power and MDES values to `data/results/statistical_report.json`". So T021 updates the report.
# Then T022 is supposed to generate the same report? This is confusing.
#
# Given the constraints, I will implement T022 to:
#   1. Load the cleaned dataset (to get group information if needed)
#   2. Load the statistical results from the main analysis (which should have been written by T018, then updated by T019 and T020, and then T021)
#   3. Ensure the report has all required fields: p-values, corrected p-values, effect sizes, power, MDES.
#   4. Save the report to data/results/statistical_report.json.
#
# Since T021 is a dependency and it writes to the same file, we assume that by the time T022 runs, the report already exists with power/MDES.
# But T022 must generate it. So we will recompute the report from the raw data? That would be inefficient and duplicate work.
#
# Another possibility: T022 is the task that runs the entire analysis pipeline (T018, T019, T020, T021) and then generates the report.
# But the task says "Generate", and it depends on T019, T020, T021, meaning those have already run.
#
# I will implement T022 as a report compiler that:
#   - Reads the base statistical results (from T018) - but we don't have a task that writes that to a file? 
#   - Instead, we rely on the fact that T021 has already written the report to data/results/statistical_report.json.
#   - So T022 will load that report, validate it has all required fields, and then save it again (ensuring it's complete).
#
# However, the task says "Generate", so we must create it. Let's look at the provided example content for data/results/statistical_report.json.
# It has a specific structure. We must produce that.
#
# Given the confusion, I will implement T022 to:
#   1. Load the cleaned dataset (data/processed/cleaned_dataset.csv)
#   2. If the report file already exists (from T021), load it and verify it has all fields. If not, we might need to recompute.
#   3. But the task says T022 depends on T021, so the report should exist.
#   4. We will load the report, check for missing fields, and if missing, we will compute them? But that would require the raw analysis functions.
#
# Since the task is to generate the report and it depends on T019, T020, T021, I think the intended flow is:
#   T019 writes bonferroni results to a file (e.g., data/results/bonferroni_results.json)
#   T020 writes effect sizes to a file (e.g., data/results/effect_sizes.json)
#   T021 writes power analysis to a file (e.g., data/results/power_analysis.json)
#   Then T022 merges these into the final report.
#
# But the provided API surface for task_t021_power_analysis shows it writes to the same report file (statistical_report.json).
#
# After re-examining the task descriptions:
#   T021: "Append power and MDES values to `data/results/statistical_report.json`"
#   T022: "Generate `data/results/statistical_report.json` containing ..."
#
# This suggests that T021 updates the report, and T022 is the task that ensures the report is complete and final.
# However, the task says T022 depends on T021, so the report should already have power/MDES.
#
# I will implement T022 as follows:
#   - Load the cleaned dataset (to get group info)
#   - Load the existing statistical_report.json (from T021)
#   - Verify it has all required fields (p-values, corrected p-values, effect sizes, power, MDES)
#   - If any field is missing, we will compute it using the analysis functions (but note: we don't have the base t-test results stored separately)
#   - Save the report.
#
# However, the task says "Generate", so we must create it from scratch? But that would require re-running the analysis.
#
# Given the time constraints and the fact that T021 has already written the report, I will assume that T022 is intended to be the final step that
# compiles the report by reading the intermediate results from T019 and T020 (if they are in separate files) and T021's power analysis.
# But since T021 writes to the same file, I think the best approach is to:
#   - Load the report from T021
#   - Ensure it has the structure as per the example
#   - Save it again (this is a no-op if it's already complete, but it satisfies the task)
#
# However, the task might be expecting T022 to run the entire analysis. But the dependencies say T019, T020, T021 are already done.
#
# I will implement T022 to:
#   1. Load the cleaned dataset (to verify data exists)
#   2. Load the statistical report that T021 wrote (data/results/statistical_report.json)
#   3. If the report is missing or incomplete, we will compute the missing parts using the analysis functions (but we don't have the base t-test results stored)
#   4. Save the report.
#
# Since we don't have the base t-test results stored separately, and T021 already wrote the report, I think the safest is to:
#   - Load the report from T021
#   - Validate it has all required fields
#   - Save it again (this ensures the file is present and complete)
#
# But the task says "Generate", so we must create it. Let's look at the example structure.
#
# I will implement T022 to generate the report by:
#   - Loading the cleaned dataset
#   - Running the analysis (t-test, bonferroni, effect size, power) again? But that would duplicate work and might not match T021's results.
#
# Given the ambiguity, I will follow the example structure and generate the report from the cleaned dataset, using the analysis functions from analysis.py.
# This ensures the report is generated as per the task, even if it duplicates work from T019, T020, T021.
# But note: the task says it depends on T019, T020, T021, meaning those have already run. So we should use their results.
#
# After careful thought, I think the intended design is:
#   T018 runs the t-test and writes results to a temporary file.
#   T019 applies bonferroni and writes to another temporary file.
#   T020 computes effect sizes and writes to another temporary file.
#   T021 computes power and MDES and writes to the main report (updating it).
#   T022 then compiles the final report by reading all temporary files and the main report, and saves the final version.
#
# However, the provided API surface does not show temporary files. So I will assume that T021 has written the final report to data/results/statistical_report.json,
# and T022 is responsible for ensuring it is complete and saved.
#
# Implementation:
#   We will load the cleaned dataset (to get group info) and the existing report (from T021).
#   We will then verify the report has all required fields. If not, we will compute them (but we don't have the base t-test results stored, so we might need to re-run the analysis).
#   However, to avoid duplication, we will assume the report from T021 is complete and just save it again.
#
# But the task says "Generate", so we must create it. I will implement T022 to generate the report from the cleaned dataset by re-running the analysis.
# This is inefficient but ensures the report is generated as per the task.
#
# Steps for T022:
#   1. Load cleaned dataset (data/processed/cleaned_dataset.csv)
#   2. Split into nostalgia and control groups based on stimulus_type.
#   3. For each metric (perseverative_errors, categories_completed):
#        - Run Welch's t-test (using analysis.welch_t_test)
#        - Apply bonferroni correction (using analysis.bonferroni_correction)
#        - Calculate effect size (using analysis.calculate_cohen_d and analysis.calculate_effect_size_ci)
#        - Calculate power and MDES (using analysis.calculate_power_and_mdes)
#   4. Compile the report in the structure of the example.
#   5. Save to data/results/statistical_report.json.
#
# This approach ensures the report is generated from the data, satisfying the task requirement.
# It also uses the existing API surface (analysis.py functions) as required.
#
# Note: This duplicates the work of T018, T019, T020, T021, but since T022 is a separate task and the dependencies are met (the data exists), it is acceptable.
#
# However, the task says T022 depends on T019, T020, T021, which suggests we should use their results. But without knowing where they stored their results,
# we cannot load them. So we recompute.
#
# Given the constraints, I will recompute the report from the cleaned dataset.

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_cleaned_dataset() -> pd.DataFrame:
    """Load the cleaned dataset from data/processed/cleaned_dataset.csv."""
    path = Path("data/processed/cleaned_dataset.csv")
    if not path.exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {path}")
    return pd.read_csv(path)

def load_statistical_analysis_results() -> Optional[Dict[str, Any]]:
    """
    Load statistical analysis results from intermediate files (if they exist).
    Since we are recomputing, we return None and compute from scratch.
    """
    # We don't use intermediate results; we compute from scratch.
    return None

def load_power_analysis_results() -> Optional[Dict[str, Any]]:
    """
    Load power analysis results from intermediate files (if they exist).
    Since we are recomputing, we return None and compute from scratch.
    """
    return None

def run_analysis_pipeline(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Run the analysis pipeline for each metric (perseverative_errors, categories_completed).
    Returns a list of comparison results.
    """
    from analysis import welch_t_test, bonferroni_correction, calculate_cohen_d, calculate_effect_size_ci, calculate_power_and_mdes

    metrics = ["perseverative_errors", "categories_completed"]
    comparisons = []

    for metric in metrics:
        if metric not in df.columns:
            logger.error(f"Metric {metric} not found in dataset")
            continue

        # Split into groups
        nostalgia_group = df[df["stimulus_type"] == "nostalgia"][metric].dropna()
        control_group = df[df["stimulus_type"] == "control"][metric].dropna()

        if len(nostalgia_group) < 2 or len(control_group) < 2:
            logger.warning(f"Insufficient data for {metric}: nostalgia={len(nostalgia_group)}, control={len(control_group)}")
            continue

        # Welch's t-test
        t_stat, p_raw = welch_t_test(nostalgia_group, control_group)

        # Bonferroni correction (we have 2 metrics, so correction factor is 2)
        p_corrected = bonferroni_correction(p_raw, n_comparisons=2)

        # Effect size
        cohen_d = calculate_cohen_d(nostalgia_group, control_group)
        ci_lower, ci_upper = calculate_effect_size_ci(cohen_d, len(nostalgia_group), len(control_group), alpha=0.05)

        # Power and MDES
        power, mdes = calculate_power_and_mdes(
            effect_size=cohen_d,
            n1=len(nostalgia_group),
            n2=len(control_group),
            alpha=0.05,
            power_target=0.8
        )

        comparison = {
            "metric": metric,
            "group_nostalgia": {
                "n": len(nostalgia_group),
                "mean": float(nostalgia_group.mean()),
                "std": float(nostalgia_group.std())
            },
            "group_control": {
                "n": len(control_group),
                "mean": float(control_group.mean()),
                "std": float(control_group.std())
            },
            "t_statistic": float(t_stat),
            "p_value_raw": float(p_raw),
            "p_value_corrected": float(p_corrected),
            "effect_size": {
                "cohen_d": float(cohen_d),
                "ci_95_lower": float(ci_lower),
                "ci_95_upper": float(ci_upper)
            },
            "power_analysis": {
                "statistical_power": float(power),
                "minimum_detectable_effect_size": float(mdes),
                "alpha": 0.05,
                "sample_size_nostalgia": len(nostalgia_group),
                "sample_size_control": len(control_group)
            }
        }
        comparisons.append(comparison)

    return comparisons

def run_power_pipeline(comparisons: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run power analysis pipeline (already included in comparisons, but we can aggregate).
    """
    # The power analysis is already done per comparison.
    # We can compute summary statistics.
    powers = [comp["power_analysis"]["statistical_power"] for comp in comparisons]
    mdes_values = [comp["power_analysis"]["minimum_detectable_effect_size"] for comp in comparisons]

    return {
        "average_power": float(np.mean(powers)) if powers else 0.0,
        "average_mdes": float(np.mean(mdes_values)) if mdes_values else 0.0
    }

def compile_final_report(comparisons: List[Dict[str, Any]], power_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compile the final report in the required structure.
    """
    significant_at_05 = sum(1 for comp in comparisons if comp["p_value_corrected"] < 0.05)
    significant_at_01 = sum(1 for comp in comparisons if comp["p_value_corrected"] < 0.01)

    report = {
        "report_metadata": {
            "task_id": "T022",
            "description": "Statistical Report: p-values, effect sizes, power, MDES",
            "analysis_method": "Welch's independent samples t-test",
            "correction_method": "Bonferroni"
        },
        "comparisons": comparisons,
        "summary": {
            "total_comparisons": len(comparisons),
            "significant_at_alpha_05": significant_at_05,
            "significant_at_alpha_01": significant_at_01,
            "average_power": power_summary["average_power"],
            "average_mdes": power_summary["average_mdes"]
        }
    }
    return report

def save_report(report: Dict[str, Any], output_path: str = "data/results/statistical_report.json") -> None:
    """Save the report to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved to {output_path}")

def main():
    """Main function to generate the statistical report."""
    logger.info("Starting T022: Generate statistical report")

    # Load cleaned dataset
    df = load_cleaned_dataset()
    logger.info(f"Loaded {len(df)} records from cleaned dataset")

    # Run analysis pipeline
    comparisons = run_analysis_pipeline(df)
    logger.info(f"Generated {len(comparisons)} comparisons")

    # Run power pipeline (aggregate)
    power_summary = run_power_pipeline(comparisons)

    # Compile final report
    report = compile_final_report(comparisons, power_summary)

    # Save report
    save_report(report)

    logger.info("T022 completed successfully")

if __name__ == "__main__":
    main()
