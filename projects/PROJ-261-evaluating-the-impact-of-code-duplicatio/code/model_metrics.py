# Existing contents of model_metrics.py are preserved.
# The new implementation is appended at the end of the file.

# ----------------------------------------------------------------------
# Re-export semantic distance calculation from semantic_cloner module.
# ----------------------------------------------------------------------
try:
    # Import the function that implements semantic distance using TF‑IDF.
    from semantic_cloner import compute_semantic_distance_batch  # noqa: F401
except Exception as import_error:
    # If the import fails (e.g., missing dependency), expose a clear error.
    def compute_semantic_distance_batch(*args, **kwargs):
        """Placeholder that raises an informative error if semantic_cloner cannot be loaded."""
        raise ImportError(
            "Semantic distance computation is unavailable because the "
            "semantic_cloner module could not be imported."
        ) from import_error