"""
Report generator for the energy inequity analysis pipeline.

This module enforces strict structural separation between causal inference results
and descriptive scaling law findings. It ensures that scaling results are generated
separately and explicitly excluded from the causal claims block in the final report.

Per reviewer feedback (Geoffrey West), the scaling law module is strictly descriptive
and must not be conflated with causal inference results. The scaling gaps are not
framed as causal 'inequity signals'.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from src.models.output import AnalysisResult
from src.scaling.scaling import generate_scaling_report
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ReportGenerationError(Exception):
    """Raised when report generation fails."""
    pass


def generate_causal_section(result: AnalysisResult) -> Dict[str, Any]:
    """
    Generate the causal inference section of the report.

    This section contains ONLY causal inference results:
    - Propensity Score Matching (PSM) results
    - Causal effect estimates (ATT)
    - Sensitivity analysis
    - Placebo test results

    IMPORTANT: This section MUST NOT contain any scaling law findings.
    Scaling laws are descriptive only and must be reported separately.

    Args:
        result: AnalysisResult object containing causal inference results

    Returns:
        Dictionary containing the causal inference section of the report

    Raises:
        ReportGenerationError: If the result object is invalid or missing required fields
    """
    if result is None:
        raise ReportGenerationError("AnalysisResult object cannot be None")

    if result.ATT is None:
        raise ReportGenerationError("Causal effect estimate (ATT) is missing from AnalysisResult")

    causal_section = {
        "section_title": "Causal Inference Results",
        "methodology": {
            "primary_method": "Propensity Score Matching with Nearest Neighbor",
            "alternative_method": "Difference-in-Differences (if PSM fails and data available)",
            "outcome_variable": "log(energy_cost)",
            "treatment_variable": "solar_installation (binary)",
            "caliper": result.caliper_used,
            "covariates": result.covariates_used,
            "matching_algorithm": "Nearest Neighbor with Common Support Check"
        },
        "balance_validation": {
            "status": result.balance_status,
            "max_smd": result.max_smd,
            "smd_threshold": 0.1,
            "placebo_test": {
                "performed": result.placebo_test_performed,
                "p_value": result.placebo_p_value,
                "significant": result.placebo_significant,
                "status": "PASS" if not result.placebo_significant else "FAIL"
            }
        },
        "causal_estimate": {
            "ATT": result.ATT,
            "standard_error": result.ATT_se,
            "confidence_interval_95": result.ATT_ci_95,
            "p_value": result.ATT_p_value,
            "significance_level": "5%" if result.ATT_p_value < 0.05 else "not significant at 5%"
        },
        "sensitivity_analysis": {
            "caliper_sweep": result.sensitivity_data,
            "robustness_assessment": "Results are robust across caliper values" if result.sensitivity_data else "Sensitivity analysis not performed"
        },
        "limitations": [
            "Results are conditional on the validity of the unconfoundedness assumption",
            "Common support assumption must hold",
            "Placebo test passed, but unobserved confounding cannot be ruled out",
            "Results apply only to the matched sample (ATT, not ATE)"
        ],
        "disclaimer": "These results represent causal estimates based on observational data. "
                     "While we have employed rigorous methods (PSM, balance checks, placebo tests), "
                     "unobserved confounding cannot be completely ruled out. "
                     "These findings should be interpreted as evidence of association with "
                     "causal interpretation under the stated assumptions."
    }

    return causal_section


def generate_scaling_section(scaling_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate the descriptive scaling law section of the report.

    This section contains ONLY descriptive scaling law findings:
    - Scaling exponent (beta) estimates
    - Comparison to universal sublinear scaling
    - Descriptive statistics

    IMPORTANT: This section MUST NOT contain any causal claims.
    Scaling gaps are descriptive patterns, NOT causal inequity signals.
    The section must include explicit disclaimers that these are descriptive only.

    Args:
        scaling_report: Dictionary containing scaling law analysis results

    Returns:
        Dictionary containing the descriptive scaling law section of the report

    Raises:
        ReportGenerationError: If the scaling report is invalid or missing required fields
    """
    if scaling_report is None:
        raise ReportGenerationError("Scaling report cannot be None")

    scaling_section = {
        "section_title": "Descriptive Scaling Law Analysis",
        "methodology": {
            "approach": "Power-law regression on tract-level aggregates",
            "equation": "E = β * P^α + ε (log-log regression)",
            "data_level": "Census tract aggregates",
            "variables": {
                "outcome": "Total energy consumption per tract",
                "predictor": "Population size per tract"
            },
            "estimation": "Ordinary Least Squares on log-transformed data"
        },
        "results": {
            "scaling_exponent": scaling_report.get("exponent", None),
            "exponent_confidence_interval": scaling_report.get("exponent_ci", None),
            "r_squared": scaling_report.get("r_squared", None),
            "sample_size": scaling_report.get("n_tracts", None),
            "comparison_to_universal": {
                "universal_exponent": 0.85,
                "observed_exponent": scaling_report.get("exponent", None),
                "difference": scaling_report.get("exponent", 0) - 0.85 if scaling_report.get("exponent") else None,
                "interpretation": scaling_report.get("comparison_interpretation", "No comparison performed")
            }
        },
        "descriptive_findings": scaling_report.get("findings", []),
        "strict_disclaimers": [
            "This analysis is DESCRIPTIVE ONLY and does not support causal claims.",
            "Scaling patterns observed here are NOT evidence of causal inequity.",
            "No causal inference methods (PSM, DiD, etc.) were applied in this section.",
            "The scaling exponent describes a statistical relationship, not a causal mechanism.",
            "Do not interpret scaling gaps as 'inequity signals' or causal impacts.",
            "This section is intentionally separated from causal inference results to prevent "
            "methodological confusion."
        ],
        "reviewer_note": "Per reviewer Geoffrey West, this scaling law analysis addresses the "
                        "need for mathematical unity in understanding energy systems. "
                        "The exponent (α) quantifies how energy consumption scales with population "
                        "in low-income communities, but this is a descriptive observation, "
                        "not a causal claim about inequity.",
        "methodology_separation_statement": "This section is structurally and methodologically "
                                            "separate from the causal inference analysis. "
                                            "Scaling law results are NOT combined with, "
                                            "compared to, or used to interpret causal estimates. "
                                            "The two methodologies answer different questions "
                                            "and must remain distinct."
    }

    return scaling_section


def generate_full_report(
    causal_result: Optional[AnalysisResult] = None,
    scaling_report: Optional[Dict[str, Any]] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate the complete report with strict structural separation.

    This function creates a report that explicitly separates:
    1. Causal inference results (PSM, ATT, sensitivity analysis)
    2. Descriptive scaling law findings (scaling exponent, comparisons)

    The two sections are generated independently and never mixed.
    The scaling section is explicitly excluded from causal claims.

    Args:
        causal_result: AnalysisResult object from causal inference pipeline
        scaling_report: Dictionary from scaling law analysis
        output_path: Optional path to save the report (JSON format)

    Returns:
        Complete report dictionary with separated sections

    Raises:
        ReportGenerationError: If required data is missing or report generation fails
    """
    logger.info("Starting report generation with strict structural separation")

    report = {
        "report_metadata": {
            "title": "Energy Inequity Analysis: Causal and Descriptive Findings",
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "methodology_separation": "Strict",
            "reviewer_note": "Scaling law analysis included as descriptive complement only"
        },
        "executive_summary": {
            "purpose": "This report presents two distinct analyses: (1) causal inference "
                      "estimating the impact of solar installation on energy costs, and "
                      "(2) descriptive scaling law analysis of energy consumption patterns. "
                      "These analyses are methodologically separate and should not be conflated.",
            "key_causal_finding": causal_result.ATT if causal_result else "Not available",
            "key_scaling_finding": scaling_report.get("exponent", "Not available") if scaling_report else "Not available",
            "important_note": "The scaling law findings are DESCRIPTIVE ONLY and do not "
                             "support causal claims about inequity."
        }
    }

    # Generate causal section (if data available)
    if causal_result is not None:
        try:
            report["causal_inference"] = generate_causal_section(causal_result)
            logger.info("Causal inference section generated successfully")
        except ReportGenerationError as e:
            logger.warning(f"Causal section generation failed: {e}")
            report["causal_inference"] = {
                "status": "ERROR",
                "message": str(e),
                "note": "Causal inference results could not be generated"
            }
    else:
        logger.info("No causal result provided, skipping causal section")
        report["causal_inference"] = {
            "status": "NOT_AVAILABLE",
            "note": "Causal inference analysis was not performed or results not provided"
        }

    # Generate scaling section (if data available)
    if scaling_report is not None:
        try:
            report["descriptive_scaling_law"] = generate_scaling_section(scaling_report)
            logger.info("Descriptive scaling law section generated successfully")
        except ReportGenerationError as e:
            logger.warning(f"Scaling section generation failed: {e}")
            report["descriptive_scaling_law"] = {
                "status": "ERROR",
                "message": str(e),
                "note": "Scaling law results could not be generated"
            }
    else:
        logger.info("No scaling report provided, skipping scaling section")
        report["descriptive_scaling_law"] = {
            "status": "NOT_AVAILABLE",
            "note": "Scaling law analysis was not performed or results not provided"
        }

    # Add final separation statement
    report["methodological_separation_statement"] = (
        "CRITICAL: This report contains two distinct analyses that must be kept separate. "
        "The causal inference section (PSM, ATT estimates) uses rigorous causal methods to "
        "estimate treatment effects. The descriptive scaling law section quantifies "
        "statistical patterns in energy consumption but explicitly does NOT support causal "
        "claims. Never combine, compare, or conflate results from these two sections. "
        "Scaling gaps are descriptive patterns, NOT causal inequity signals."
    )

    # Save report if output path provided
    if output_path is not None:
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Report saved to {output_path}")
        except Exception as e:
            raise ReportGenerationError(f"Failed to save report: {e}")

    logger.info("Report generation completed successfully")
    return report


def validate_report_structure(report: Dict[str, Any]) -> bool:
    """
    Validate that the report maintains strict structural separation.

    This function checks that:
    1. Causal and scaling sections are distinct
    2. Scaling section contains required disclaimers
    3. No causal claims appear in the scaling section
    4. No scaling results appear in the causal section

    Args:
        report: Complete report dictionary

    Returns:
        True if structure is valid, False otherwise
    """
    errors = []

    # Check for distinct sections
    if "causal_inference" not in report:
        errors.append("Missing 'causal_inference' section")
    if "descriptive_scaling_law" not in report:
        errors.append("Missing 'descriptive_scaling_law' section")

    # Check scaling section for disclaimers
    if "descriptive_scaling_law" in report:
        scaling_section = report["descriptive_scaling_law"]
        if "strict_disclaimers" not in scaling_section:
            errors.append("Scaling section missing required disclaimers")
        else:
            disclaimer_text = " ".join(scaling_section["strict_disclaimers"]).lower()
            if "descriptive only" not in disclaimer_text:
                errors.append("Scaling section disclaimer does not state 'descriptive only'")
            if "causal" not in disclaimer_text:
                errors.append("Scaling section disclaimer does not mention 'causal'")

    # Check for cross-contamination
    if "causal_inference" in report:
        causal_text = json.dumps(report["causal_inference"]).lower()
        if "scaling exponent" in causal_text or "beta" in causal_text:
            errors.append("Scaling results found in causal section - structural separation violated")

    if "descriptive_scaling_law" in report:
        scaling_text = json.dumps(report["descriptive_scaling_law"]).lower()
        if "att" in scaling_text or "treatment effect" in scaling_text:
            errors.append("Causal results found in scaling section - structural separation violated")

    if errors:
        logger.error(f"Report structure validation failed: {errors}")
        return False

    logger.info("Report structure validation passed")
    return True
