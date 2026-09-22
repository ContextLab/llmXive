"""
llmXive Narrative Generation Module

Contains agents and utilities for generating baseline narratives,
counterfactual inspections, and final story synthesis.
"""

from .baseline import (
    compute_pairwise_correlations,
    identify_strongest_relationship,
    generate_narrative,
    run_baseline_analysis,
    main as baseline_main,
)
from .flag_propagator import (
    propagate_low_power_flag,
    write_propagated_report,
    main as propagator_main,
)
from .inspector import (
    compute_partial_correlation,
    bootstrap_stability_analysis,
    determine_validity_status,
    run_inspector_analysis,
    main as inspector_main,
)
from .query_generator import (
    QueryGenerationError,
    QuerySyntaxError,
    QueryTimeoutError,
    generate_counterfactual_query,
    run_query_generation_pipeline,
    main as query_gen_main,
)
from .sensitivity_aggregator import (
    load_json_file,
    aggregate_sensitivity_report,
    run_aggregation_pipeline,
)

__all__ = [
    # Baseline
    "compute_pairwise_correlations",
    "identify_strongest_relationship",
    "generate_narrative",
    "run_baseline_analysis",
    "baseline_main",
    # Flag Propagation
    "propagate_low_power_flag",
    "write_propagated_report",
    "propagator_main",
    # Inspector
    "compute_partial_correlation",
    "bootstrap_stability_analysis",
    "determine_validity_status",
    "run_inspector_analysis",
    "inspector_main",
    # Query Generation
    "QueryGenerationError",
    "QuerySyntaxError",
    "QueryTimeoutError",
    "generate_counterfactual_query",
    "run_query_generation_pipeline",
    "query_gen_main",
    # Sensitivity Aggregation
    "load_json_file",
    "aggregate_sensitivity_report",
    "run_aggregation_pipeline",
]
