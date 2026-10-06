import os
import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """
    Execute a shell command and return the result.
    
    Args:
        command: List of command arguments.
        check: If True, raise CalledProcessError on non-zero exit.
        
    Returns:
        CompletedProcess instance.
    """
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}")
        print(f"Return code: {e.returncode}")
        print(f"Stderr: {e.stderr}")
        if not check:
            return e
        raise


def ensure_ncbi_settings() -> bool:
    """
    Ensure ~/.ncbi/settings exists with basic configuration.
    
    Returns:
        True if settings are valid, False otherwise.
    """
    ncbi_dir = Path.home() / ".ncbi"
    settings_file = ncbi_dir / "settings"
    
    if not ncbi_dir.exists():
        print(f"Creating directory: {ncbi_dir}")
        ncbi_dir.mkdir(parents=True, exist_ok=True)
    
    if not settings_file.exists():
        print(f"Creating default settings file: {settings_file}")
        # Create a minimal valid settings file
        # These are the defaults used by SRA Toolkit
        default_content = """[DEFAULT]
; This is a default settings file for SRA Toolkit
; Generated automatically by install_sra_toolkit.py

[repository]
; Path to the repository
path = ~/ncbi/public

[lib]
; Library configuration
; No specific changes needed for basic operation
"""
        settings_file.write_text(default_content)
        print("Default settings file created successfully.")
    else:
        print(f"Settings file already exists: {settings_file}")
    
    return True


def verify_sra_toolkit() -> bool:
    """
    Verify that SRA Toolkit is installed and functional.
    
    Runs 'prefetch --help' to verify installation.
    
    Returns:
        True if verification passes, False otherwise.
    """
    print("Verifying SRA Toolkit installation...")
    
    try:
        result = run_command(["prefetch", "--help"], check=False)
        
        if result.returncode == 0:
            print("✓ SRA Toolkit is installed and functional.")
            print("  Output of 'prefetch --help' (first 5 lines):")
            lines = result.stdout.split('\n')[:5]
            for line in lines:
                print(f"    {line}")
            return True
        else:
            print("✗ 'prefetch --help' failed.")
            print(f"  Stderr: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("✗ 'prefetch' command not found in PATH.")
        print("  Please ensure SRA Toolkit is installed and added to PATH.")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during verification: {e}")
        return False


def install_sra_toolkit() -> bool:
    """
    Install SRA Toolkit via conda.
    
    This function attempts to install the sratoolkit package using conda.
    It assumes conda (or mamba) is available in the system PATH.
    
    Returns:
        True if installation succeeds, False otherwise.
    """
    print("Installing SRA Toolkit via conda...")
    
    # Try to find conda executable
    conda_candidates = ["conda", "mamba"]
    conda_exe = None
    
    for candidate in conda_candidates:
        try:
            result = run_command([candidate, "--version"], check=False)
            if result.returncode == 0:
                conda_exe = candidate
                print(f"Found conda executable: {conda_exe}")
                break
        except Exception:
            continue
    
    if conda_exe is None:
        print("✗ Could not find conda or mamba in PATH.")
        print("  Please install Miniconda/Anaconda or ensure it is in PATH.")
        return False
    
    # Install sratoolkit
    print(f"Running: {conda_exe} install -y -c bioconda -c conda-forge sratoolkit")
    try:
        result = run_command([
            conda_exe, "install", "-y", 
            "-c", "bioconda", "-c", "conda-forge", 
            "sratoolkit"
        ], check=False)
        
        if result.returncode == 0:
            print("✓ SRA Toolkit installed successfully.")
            return True
        else:
            print("✗ Failed to install SRA Toolkit via conda.")
            print(f"  Stderr: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Exception during installation: {e}")
        return False


def main():
    """
    Main entry point for SRA Toolkit installation and verification.
    
    Performs the following steps:
    1. Attempt to install SRA Toolkit via conda if not present.
    2. Ensure ~/.ncbi/settings exists.
    3. Verify installation by running 'prefetch --help'.
    """
    print("=" * 60)
    print("SRA Toolkit Installation and Verification")
    print("=" * 60)
    
    # Step 1: Check if already installed
    if verify_sra_toolkit():
        print("\nSRA Toolkit is already installed and verified.")
        ensure_ncbi_settings()
        return 0
    
    print("\nSRA Toolkit not found. Attempting installation...")
    
    # Step 2: Install
    if not install_sra_toolkit():
        print("\n✗ Installation failed. Please check the error messages above.")
        return 1
    
    # Step 3: Verify installation again
    if not verify_sra_toolkit():
        print("\n✗ Verification failed after installation.")
        print("  Please check if the conda environment is activated or PATH is set correctly.")
        return 1
    
    # Step 4: Configure settings
    print("\nConfiguring ~/.ncbi/settings...")
    if not ensure_ncbi_settings():
        print("✗ Failed to configure settings, but SRA Toolkit is installed.")
        print("  You may need to configure settings manually.")
    
    print("\n" + "=" * 60)
    print("SRA Toolkit installation and configuration complete!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())