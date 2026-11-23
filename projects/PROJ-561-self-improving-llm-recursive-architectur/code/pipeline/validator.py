"""
Pre-Application External Oracle Check module.

Validates modification proposals against fixed heuristics (parameter efficiency,
structural constraints) BEFORE application to the model.
"""

from schemas.modification_proposal import ModificationProposal
from config import get_config
from typing import Optional

# Import T014 logic if needed for distinctness, but T014 is in pipeline/model.py
# We rely on T071/T072 for specific pipeline steps if needed, but T059a is the
# "Pre-Application External Oracle Check" which focuses on heuristics and limits.

def validate_proposal_oracle(proposal: ModificationProposal) -> bool:
    """
    Validates the proposed modification against fixed heuristics BEFORE application.

    Logic:
    1. Reads the parameter limit from config.py (T008) to satisfy FR-019.
    2. Checks if the proposed modification type is allowed (layer_add, head_count_change).
    3. Checks if the magnitude is within reasonable bounds (e.g., > 0).
    4. (Implicit) The actual parameter count check against the limit is handled by T071,
       but this function ensures the proposal is structurally valid and the limit
       configuration is respected conceptually.

    Returns:
        True if the proposal passes the heuristic checks, False otherwise.
    """
    config = get_config()
    limit_percent = config.safety_constraints.max_param_increase_percent

    # 1. Validate modification type
    allowed_types = ['layer_add', 'head_count_change']
    if proposal.modification_type not in allowed_types:
        return False

    # 2. Validate magnitude
    # Magnitude must be positive for additions/increases.
    # If the spec allowed removals, we'd check > 0 or < 0 based on type.
    # T013 defines magnitude as int.
    if proposal.magnitude <= 0:
        return False

    # 3. Validate that the limit configuration exists and is valid
    if not isinstance(limit_percent, (int, float)) or limit_percent <= 0:
        # Configuration error, fail safe
        return False

    # 4. Structural check: ensure rationale is not empty (heuristic)
    if not proposal.rationale or len(proposal.rationale.strip()) == 0:
        return False

    return True


def check_parameter_constraint(proposal: ModificationProposal, baseline_params: int, limit_percent: float) -> bool:
    """
    Explicitly validates the proposed modification does not exceed the configured
    parameter limit (FR-019) BEFORE application.

    This implements the specific "step" mandated by FR-019.

    Args:
        proposal: The modification proposal.
        baseline_params: The current number of parameters in the model.
        limit_percent: The maximum allowed increase as a percentage (e.g., 0.30 for 30%).

    Returns:
        True if the proposed parameter count is within limits, False otherwise.
    """
    if limit_percent <= 0:
        return False

    # Estimate new parameter count based on modification type and magnitude.
    # Since we don't have the model weights here, we estimate based on a heuristic
    # or require the proposal to include estimated_param_count (from T013 schema).
    # T013 schema includes 'estimated_param_count'.
    if proposal.estimated_param_count is None:
        # If not estimated, we cannot validate strictly, but we can check if
        # the magnitude implies a massive change. For safety, we assume False if unknown.
        # However, T016 (Apply) will calculate real count.
        # Let's assume the proposal MUST have estimated_param_count for this check.
        return False

    max_allowed_params = baseline_params * (1 + limit_percent)

    return proposal.estimated_param_count <= max_allowed_params


def execute_distinctness_check(proposal: ModificationProposal, history: list) -> bool:
    """
    Enforces the distinctness constraint (FR-020) as a distinct pipeline step.

    Calls T014 logic (validate_modification_distinctness) wrapped as a pipeline step.

    Args:
        proposal: The current proposal.
        history: List of previous ModificationProposal objects.

    Returns:
        True if the proposal is distinct, False otherwise.
    """
    from pipeline.model import validate_modification_distinctness
    return validate_modification_distinctness(proposal, history)
