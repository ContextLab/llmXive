"""
Secure deletion workflow for participant data.

Implements Constitution VII compliance by securely overwriting file contents
before deletion to prevent data recovery.

Workflow:
1. Open file in binary write mode
2. Overwrite content 3 times with random bytes (os.urandom)
3. Flush and fsync to ensure data is written to disk
4. Close file
5. Unlink (delete) the file
"""

import os
import sys
import logging
from pathlib import Path
from typing import Union

# Configure logging to use project's logging infrastructure if available
# Otherwise fallback to basic config
try:
    from logs.experiment import get_logger
    logger = get_logger("data_deletion")
except ImportError:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("data_deletion")


def secure_delete_file(file_path: Union[str, Path]) -> bool:
    """
    Securely delete a file by overwriting content 3 times with random data
    before unlinking.

    Args:
        file_path: Path to the file to be securely deleted.

    Returns:
        True if deletion was successful, False otherwise.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.warning(f"File does not exist, nothing to delete: {file_path}")
        return True

    if not file_path.is_file():
        logger.error(f"Path is not a file: {file_path}")
        return False

    file_size = file_path.stat().st_size
    logger.info(f"Securely deleting file: {file_path} (size: {file_size} bytes)")

    try:
        # Perform 3 passes of overwriting with random data
        for i in range(3):
            logger.debug(f"Overwrite pass {i + 1}/3 for {file_path}")
            with open(file_path, 'wb') as f:
                # Write random bytes for the entire file size
                remaining = file_size
                while remaining > 0:
                    # Write in chunks to avoid memory issues with very large files
                    chunk_size = min(remaining, 1024 * 1024)  # 1MB chunks
                    random_data = os.urandom(chunk_size)
                    f.write(random_data)
                    remaining -= chunk_size

                # Ensure all data is written to disk
                f.flush()
                os.fsync(f.fileno())

            logger.debug(f"Pass {i + 1} complete for {file_path}")

        # Final fsync on the directory to ensure metadata is updated
        # before deletion
        file_parent = file_path.parent
        if file_parent.exists():
            with open(file_parent, 'r') as parent_dir:
                os.fsync(parent_dir.fileno())

        # Delete the file
        os.unlink(file_path)
        logger.info(f"Successfully securely deleted: {file_path}")
        return True

    except PermissionError as e:
        logger.error(f"Permission denied while deleting {file_path}: {e}")
        return False
    except OSError as e:
        logger.error(f"OS error while deleting {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while deleting {file_path}: {e}")
        return False


def secure_delete_directory(dir_path: Union[str, Path], recursive: bool = True) -> dict:
    """
    Securely delete all files in a directory.

    Args:
        dir_path: Path to the directory.
        recursive: If True, delete files in subdirectories as well.

    Returns:
        Dictionary with 'success' count and 'failed' list.
    """
    dir_path = Path(dir_path)
    results = {"success": 0, "failed": []}

    if not dir_path.exists():
        logger.warning(f"Directory does not exist: {dir_path}")
        return results

    if not dir_path.is_dir():
        logger.error(f"Path is not a directory: {dir_path}")
        return results

    files_to_delete = []
    if recursive:
        for root, _, files in os.walk(dir_path):
            for file in files:
                files_to_delete.append(Path(root) / file)
    else:
        files_to_delete = [dir_path / f for f in os.listdir(dir_path) 
                          if (dir_path / f).is_file()]

    for file_path in files_to_delete:
        if secure_delete_file(file_path):
            results["success"] += 1
        else:
            results["failed"].append(str(file_path))

    # Try to remove the directory itself if it's empty
    if recursive and dir_path.exists():
        try:
            dir_path.rmdir()
            logger.info(f"Removed empty directory: {dir_path}")
        except OSError:
            logger.debug(f"Directory not empty or cannot be removed: {dir_path}")

    return results


def main():
    """
    Command-line interface for secure deletion.

    Usage:
        python code/analysis/data_deletion.py <file_or_directory_path> [--recursive]
    """
    if len(sys.argv) < 2:
        print("Usage: python code/analysis/data_deletion.py <path> [--recursive]")
        print("  Deletes the file or directory securely by overwriting 3x then unlinking.")
        sys.exit(1)

    target_path = sys.argv[1]
    recursive = "--recursive" in sys.argv

    if not os.path.exists(target_path):
        print(f"Error: Path does not exist: {target_path}")
        sys.exit(1)

    if os.path.isfile(target_path):
        success = secure_delete_file(target_path)
        sys.exit(0 if success else 1)
    elif os.path.isdir(target_path):
        results = secure_delete_directory(target_path, recursive=recursive)
        print(f"Deletion complete. Success: {results['success']}, Failed: {len(results['failed'])}")
        if results['failed']:
            print("Failed files:")
            for f in results['failed']:
                print(f"  - {f}")
        sys.exit(0 if len(results['failed']) == 0 else 1)
    else:
        print(f"Error: Unknown path type: {target_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()