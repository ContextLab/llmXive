"""
Blockers module: Defines the RestrictedActionError and library policies.

This module establishes the whitelist (allowed) and blacklist (blocked) of
Python libraries to enforce the 2D spatial reasoning constraint (FR-001).
"""

class RestrictedActionError(Exception):
    """
    Raised when an attempt is made to import or use a blocked library
    or perform a restricted action within the SpatialClaw kernel.
    """
    def __init__(self, message: str, library_name: str = None, action: str = None):
        self.library_name = library_name
        self.action = action
        super().__init__(message)

# Configuration: Allowed 2D libraries
# These libraries are permitted for geometric operations.
ALLOWED_LIBRARIES = frozenset({
    "shapely",
    "numpy",
    "scipy",
    "pandas",
    "matplotlib",
    "pytest",
    "statsmodels",
    "datasets",
    "huggingface_hub",
    "yaml",
    "json",
    "logging",
    "random",
    "time",
    "sys",
    "os",
    "collections",
    "itertools",
})

# Configuration: Blocked 3D libraries
# These libraries are explicitly forbidden to enforce the 2D constraint.
BLOCKED_LIBRARIES = frozenset({
    "trimesh",
    "pytorch3d",
    "open3d",
    "open3d-python",
    "torch3d",
    "k3d",
    "mayavi",
    "vtk",
})

def check_library_policy(module_name: str) -> None:
    """
    Validates if a module name is allowed or blocked.

    Args:
        module_name: The name of the module being imported (e.g., 'trimesh').

    Raises:
        RestrictedActionError: If the module is in the blocked list.
    """
    if module_name in BLOCKED_LIBRARIES:
        raise RestrictedActionError(
            f"Attempted to import blocked 3D library: '{module_name}'. "
            f"SpatialClaw kernel enforces 2D-only operations. "
            f"Blocked libraries: {sorted(BLOCKED_LIBRARIES)}",
            library_name=module_name,
            action="import"
        )

    # Optional: Warn if not explicitly allowed but not blocked (neutral zone)
    # For strictness, we currently only block the explicit blacklist.
    # Future: If strict whitelist mode is required, uncomment below:
    # if module_name not in ALLOWED_LIBRARIES:
    #     raise RestrictedActionError(
    #         f"Module '{module_name}' is not in the allowed list.",
    #         library_name=module_name,
    #         action="import"
    #     )
