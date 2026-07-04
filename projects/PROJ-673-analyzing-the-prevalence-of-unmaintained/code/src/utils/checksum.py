import hashlib
from pathlib import Path
from typing import Union

def generate_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Generate a checksum for a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from e

    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()

def write_checksum_file(file_path: Union[str, Path], checksum_path: Union[str, Path] = None) -> Path:
    """
    Generate a checksum for a file and write it to a .checksum file.

    Args:
        file_path: Path to the file to checksum.
        checksum_path: Optional path for the checksum file. If None,
                       creates a file with .sha256 extension next to the original.

    Returns:
        Path to the created checksum file.
    """
    file_path = Path(file_path)
    if checksum_path is None:
        checksum_path = file_path.with_suffix(file_path.suffix + ".sha256")
    else:
        checksum_path = Path(checksum_path)

    checksum = generate_checksum(file_path)
    
    # Write checksum in standard format: <checksum>  <filename>
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  {file_path.name}\n")
    
    return checksum_path