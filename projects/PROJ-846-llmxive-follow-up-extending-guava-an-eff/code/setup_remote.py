import os
import subprocess
import sys
from pathlib import Path

def setup_remote(remote_name: str, remote_url: str, repo_root: Path) -> bool:
    """
    Configures a remote repository URL for the git repository.
    
    Args:
        remote_name: Name of the remote (e.g., 'origin')
        remote_url: URL of the remote repository
        repo_root: Path to the repository root directory
        
    Returns:
        True if remote was successfully configured, False otherwise
        
    Raises:
        RuntimeError: If git is not available or remote configuration fails
    """
    try:
        # Check if git is available
        subprocess.run(
            ["git", "--version"],
            check=True,
            cwd=repo_root,
            capture_output=True
        )
        
        # Check if remote already exists
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", remote_name],
                check=True,
                cwd=repo_root,
                capture_output=True,
                text=True
            )
            current_url = result.stdout.strip()
            if current_url == remote_url:
                print(f"Remote '{remote_name}' already configured with URL: {remote_url}")
                return True
            else:
                print(f"Removing existing remote '{remote_name}' with URL: {current_url}")
                subprocess.run(
                    ["git", "remote", "remove", remote_name],
                    check=True,
                    cwd=repo_root
                )
        except subprocess.CalledProcessError:
            # Remote doesn't exist, which is fine
            pass
        
        # Add the remote
        subprocess.run(
            ["git", "remote", "add", remote_name, remote_url],
            check=True,
            cwd=repo_root
        )
        
        print(f"Successfully configured remote '{remote_name}' with URL: {remote_url}")
        return True
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to configure git remote: {e.stderr.decode().strip() if e.stderr else str(e)}"
        print(error_msg)
        raise RuntimeError(error_msg) from e
    except FileNotFoundError:
        print("Git is not installed or not in PATH")
        raise RuntimeError("Git is not available") from None

def main():
    """
    Main entry point for setting up the remote repository.
    Uses default values: remote_name='origin', remote_url from environment or example.
    """
    repo_root = Path.cwd()
    
    # Default remote name
    remote_name = "origin"
    
    # Get remote URL from environment variable or use a placeholder
    remote_url = os.environ.get("GIT_REMOTE_URL", "https://github.com/example/PROJ-846-llmxive-follow-up-extending-guava-an-eff.git")
    
    if remote_url == "https://github.com/example/PROJ-846-llmxive-follow-up-extending-guava-an-eff.git":
        print("Warning: Using placeholder remote URL. Set GIT_REMOTE_URL environment variable to configure the actual remote.")
        print("Example: export GIT_REMOTE_URL=https://github.com/your-org/your-repo.git")
    
    try:
        setup_remote(remote_name, remote_url, repo_root)
        print("Remote setup complete.")
    except RuntimeError as e:
        print(f"Remote setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
