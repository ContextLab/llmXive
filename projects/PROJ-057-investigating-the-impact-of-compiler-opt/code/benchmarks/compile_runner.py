"""
Compile Runner for Compiler Optimization Benchmarks.
Orchestrates compilation of C++ kernels with varying optimization flags
and computes SHA-256 hashes for binary verification.
"""
import os
import sys
import subprocess
import hashlib
import argparse
import tempfile
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

# Configuration
COMPILERS = {
    "g++": "g++",
    "clang++": "clang++"
}

DEFAULT_COMPILER = "g++"
KERNELS_DIR = Path("code/kernels")
BINARY_DIR = Path("data/binaries")

def ensure_dirs():
    """Ensure required directories exist."""
    BINARY_DIR.mkdir(parents=True, exist_ok=True)

def get_compiler_path(compiler_name: str) -> Optional[str]:
    """Find the compiler in PATH."""
    try:
        result = subprocess.run(["which", compiler_name], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compile_kernel(
    kernel_path: str,
    compiler: str,
    flags: List[str],
    output_path: str,
    std: str = "c++17"
) -> Tuple[bool, str, str]:
    """
    Compile a C++ kernel with specified flags.
    
    Args:
        kernel_path: Path to the .cpp source file.
        compiler: Compiler name (e.g., 'g++').
        flags: List of compiler flags.
        output_path: Path for the output binary.
        std: C++ standard version.
    
    Returns:
        Tuple of (success, message, hash_or_error).
    """
    cmd = [
        compiler,
        f"-std={std}",
        "-o", output_path,
        kernel_path
    ]
    cmd.extend(flags)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        # Compute hash of the binary
        binary_hash = compute_sha256(output_path)
        return True, "Compilation successful", binary_hash
    except subprocess.CalledProcessError as e:
        return False, f"Compilation failed: {e.stderr}", str(e.stderr)

def run_test():
    """
    Run a test compilation to verify the system works.
    Creates a dummy binary and prints its SHA-256 hash.
    """
    ensure_dirs()
    
    # Create a minimal dummy C++ file in a temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_src = Path(tmpdir) / "dummy.cpp"
        dummy_src.write_text("""
        int main() { return 0; }
        """)
        
        dummy_bin = Path(tmpdir) / "dummy_binary"
        
        compiler = get_compiler_path(DEFAULT_COMPILER)
        if not compiler:
            print(f"Error: {DEFAULT_COMPILER} not found in PATH.", file=sys.stderr)
            sys.exit(1)
        
        success, message, result = compile_kernel(
            str(dummy_src),
            compiler,
            [],  # No special flags for test
            str(dummy_bin)
        )
        
        if success:
            print(f"Test compilation successful.")
            print(f"Binary: {dummy_bin}")
            print(f"SHA-256: {result}")
        else:
            print(f"Test compilation failed: {message}", file=sys.stderr)
            sys.exit(1)

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Compile C++ kernels with optimization flags.")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a test compilation to verify the system."
    )
    parser.add_argument(
        "--kernel",
        type=str,
        help="Path to the kernel source file."
    )
    parser.add_argument(
        "--compiler",
        type=str,
        default=DEFAULT_COMPILER,
        help=f"Compiler to use (default: {DEFAULT_COMPILER})."
    )
    parser.add_argument(
        "--flags",
        nargs="+",
        default=[],
        help="Compiler flags (e.g., -O2 -march=native)."
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output binary path."
    )

    args = parser.parse_args()

    if args.test:
        run_test()
        return

    if not args.kernel or not args.output:
        parser.error("--kernel and --output are required unless --test is specified.")

    ensure_dirs()
    compiler = get_compiler_path(args.compiler)
    if not compiler:
        print(f"Error: Compiler '{args.compiler}' not found in PATH.", file=sys.stderr)
        sys.exit(1)

    success, message, result = compile_kernel(
        args.kernel,
        compiler,
        args.flags,
        args.output
    )

    if success:
        print(f"Compilation successful: {args.output}")
        print(f"SHA-256: {result}")
    else:
        print(f"Compilation failed: {message}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()