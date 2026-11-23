import hashlib

def compute_file_sha256(filepath: str) -> str:
    """Compute SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_and_store_checksum(filepath: str, output_path: str) -> str:
    """
    Compute the SHA‑256 checksum of ``filepath`` and write it to ``output_path``.
    Returns the computed checksum string.

    This helper is used by various pipeline components that need to
    persist a checksum alongside a data artifact.
    """
    checksum = compute_file_sha256(filepath)
    # Ensure the directory for the output exists
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as out_f:
        out_f.write(checksum)
    return checksum
