import os
from pathlib import Path
from typing import Union

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure that a directory exists at the given path.
    If the directory (or any of its parents) does not exist, it is created.

    Parameters
    ----------
    path : Union[str, Path]
        The directory path to ensure.

    Returns
    -------
    Path
        The Path object representing the ensured directory.
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def main() -> None:
    """
    Create the required data directory structure for the project:
    - data/stimuli/
    - data/processed/
    - data/measurements/
    - data/raw/
    
    The function determines the project root relative to this file's location
    and creates each subdirectory under the root's `data/` folder.
    """
    # Determine the project root (assumes this file is located in <project_root>/code/)
    project_root = Path(__file__).resolve().parent.parent

    data_root = project_root / "data"
    subdirectories = ["stimuli", "processed", "measurements", "raw"]

    for subdir in subdirectories:
        ensure_directory(data_root / subdir)

if __name__ == "__main__":
    main()