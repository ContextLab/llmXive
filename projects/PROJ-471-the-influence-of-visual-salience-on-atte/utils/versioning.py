"""
Minimal versioning helper for the project.

The full project may have a richer implementation, but for the purposes of
the current tasks we only need a ``register_artifact`` function that records
that an artifact was produced. The implementation logs the registration and
returns ``None``; it does **not** perform any external side‑effects.
"""
from pathlib import Path
from llmxive_toolkit import get_logger

_log = get_logger(__name__)

def register_artifact(file_path: Path, artifact_type: str, description: str) -> None:
    """
    Register a generated artifact.

    Parameters
    ----------
    file_path : Path
        Path to the artifact file.
    artifact_type : str
        Logical type of the artifact (e.g., ``checksum_manifest``).
    description : str
        Human‑readable description of the artifact.
    """
    _log.info(
        f"Artifact registered – type: {artifact_type}, path: {file_path}, description: {description}"
    )
