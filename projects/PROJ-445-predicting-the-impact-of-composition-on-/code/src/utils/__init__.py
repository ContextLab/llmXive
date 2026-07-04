"""
Utilities package for the chalcogenide glass transition prediction project.
"""
# Existing imports maintained for backward compatibility
from .constants import (
    get_element, get_coordination_number, get_electronegativity,
    get_atomic_radius, get_element_property, parse_composition,
    compute_mean_coordination_number, compute_electronegativity_variance,
    compute_atomic_radius_variance
)
from .cpu_compliance import (
    enforce_cpu_mode, validate_cpu_only_model, limit_memory_usage,
    validate_data_size_for_cpu, setup_cpu_environment, ensure_no_gpu_operations
)
from .metrics import (
    compute_vif, residualize_features, update_performance_metrics,
    check_and_mitigate_collinearity, compute_bootstrap_ci_for_shap_difference
)
from .manifest_manager import (
    compute_file_hash, load_manifest, save_manifest, initialize_manifest,
    register_artifact, verify_artifact
)
from .manifest_verifier import (
    verify_artifact_integrity, verify_manifest_integrity,
    generate_verification_report, save_verification_report
)
from .performance_timer import (
    estimate_training_time, run_performance_benchmark
)
from .generate_metrics import (
    load_json_artifact, aggregate_metrics
)

__all__ = [
    # Constants
    'get_element', 'get_coordination_number', 'get_electronegativity',
    'get_atomic_radius', 'get_element_property', 'parse_composition',
    'compute_mean_coordination_number', 'compute_electronegativity_variance',
    'compute_atomic_radius_variance',
    # CPU Compliance
    'enforce_cpu_mode', 'validate_cpu_only_model', 'limit_memory_usage',
    'validate_data_size_for_cpu', 'setup_cpu_environment', 'ensure_no_gpu_operations',
    # Metrics
    'compute_vif', 'residualize_features', 'update_performance_metrics',
    'check_and_mitigate_collinearity', 'compute_bootstrap_ci_for_shap_difference',
    # Manifest Management
    'compute_file_hash', 'load_manifest', 'save_manifest', 'initialize_manifest',
    'register_artifact', 'verify_artifact',
    # Manifest Verification
    'verify_artifact_integrity', 'verify_manifest_integrity',
    'generate_verification_report', 'save_verification_report',
    # Performance Timer
    'estimate_training_time', 'run_performance_benchmark',
    # Metrics Generation
    'load_json_artifact', 'aggregate_metrics'
]