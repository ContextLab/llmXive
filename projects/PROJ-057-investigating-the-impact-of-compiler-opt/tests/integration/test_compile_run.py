"""
Integration tests for the compile and run pipeline.
Specifically verifies GCC 11+/Clang 14+ availability and execution of a MatMul kernel.
"""
import os
import sys
import subprocess
import tempfile
import shutil
import json
import hashlib
from pathlib import Path
import pytest

# Ensure the code directory is in the path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from benchmarks.compile_runner import CompileRunner
from benchmarks.config import ConfigManager, create_default_manager


def get_compiler_version(compiler_path: str) -> tuple:
    """
    Extract major and minor version numbers from a compiler.
    Returns (major, minor) or raises an error if parsing fails.
    """
    try:
        result = subprocess.run(
            [compiler_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            raise RuntimeError(f"Compiler {compiler_path} returned error code {result.returncode}")
        
        output = result.stdout
        major, minor = 0, 0
        
        if "gcc" in compiler_path or "g++" in compiler_path:
            # GCC version format usually appears as "gcc (Ubuntu 11.3.0-1ubuntu1~22.04) 11.3.0"
            # or "g++ (GCC) 11.3.0"
            parts = output.split()
            for i, part in enumerate(parts):
                if part.isdigit():
                    major = int(part)
                    if i + 1 < len(parts) and "." in parts[i + 1]:
                        minor = int(parts[i + 1].split('.')[1])
                    break
                # Sometimes version is next to the word "GCC"
                if "GCC" in part:
                    next_part = parts[i + 1] if i + 1 < len(parts) else ""
                    if "." in next_part:
                        version_parts = next_part.split(".")
                        major = int(version_parts[0])
                        minor = int(version_parts[1]) if len(version_parts) > 1 else 0
                        break
        elif "clang" in compiler_path or "clang++" in compiler_path:
            # Clang version format: "clang version 14.0.0"
            parts = output.split()
            for i, part in enumerate(parts):
                if part == "version":
                    version_str = parts[i + 1] if i + 1 < len(parts) else "0.0"
                    version_parts = version_str.split(".")
                    major = int(version_parts[0])
                    minor = int(version_parts[1]) if len(version_parts) > 1 else 0
                    break
        
        return major, minor
    except Exception as e:
        raise RuntimeError(f"Failed to determine compiler version for {compiler_path}: {e}")


def check_compiler_availability():
    """
    Checks if GCC >= 11 or Clang >= 14 is available on the system.
    Returns the path to a suitable compiler and its version.
    Raises RuntimeError if no suitable compiler is found.
    """
    compilers = [
        ("g++", 11),
        ("clang++", 14)
    ]
    
    for compiler_name, min_version in compilers:
        try:
            # Check if the compiler is in the PATH
            compiler_path = shutil.which(compiler_name)
            if compiler_path:
                major, minor = get_compiler_version(compiler_path)
                if major > min_version or (major == min_version and minor >= 0):
                    return compiler_path, (major, minor)
        except Exception:
            continue
    
    raise RuntimeError(
        "No suitable compiler found. Requires GCC >= 11 or Clang >= 14. "
        "Please install one of these compilers."
    )


@pytest.fixture(scope="module")
def compiler_info():
    """
    Pytest fixture to determine the compiler to use for the test suite.
    """
    return check_compiler_availability()


@pytest.fixture(scope="module")
def temp_build_dir():
    """
    Creates a temporary directory for compilation artifacts.
    """
    tmpdir = tempfile.mkdtemp(prefix="llmxive_compile_test_")
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)


def create_dummy_matmul_kernel(tmp_path: Path):
    """
    Creates a minimal, valid C++ MatMul kernel file for testing compilation.
    This kernel does a trivial matrix multiplication to ensure the compiler works.
    """
    kernel_code = """
    #include <iostream>
    #include <vector>
    #include <chrono>
    #include <cstring>

    void matmul(const float* A, const float* B, float* C, int N) {
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                float sum = 0.0f;
                for (int k = 0; k < N; ++k) {
                    sum += A[i * N + k] * B[k * N + j];
                }
                C[i * N + j] = sum;
            }
        }
    }

    int main() {
        int N = 16; // Small matrix for quick test
        std::vector<float> A(N * N, 1.0f);
        std::vector<float> B(N * N, 2.0f);
        std::vector<float> C(N * N, 0.0f);

        auto start = std::chrono::high_resolution_clock::now();
        matmul(A.data(), B.data(), C.data(), N);
        auto end = std::chrono::high_resolution_clock::now();

        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        
        // Verify result: 16 * 1.0 * 2.0 = 32.0
        bool success = true;
        for (float val : C) {
            if (val != 32.0f) {
                success = false;
                break;
            }
        }

        std::cout << "N=" << N << ", Latency=" << duration.count() << "us, Success=" << (success ? "true" : "false") << std::endl;
        
        return success ? 0 : 1;
    }
    """
    kernel_file = tmp_path / "matmul_test.cpp"
    with open(kernel_file, "w") as f:
        f.write(kernel_code)
    return kernel_file


def test_compile_and_run_matmul(compiler_info, temp_build_dir):
    """
    Integration test: Verify GCC 11+/Clang 14+ availability and execution of a MatMul kernel.
    
    Steps:
    1. Verify a suitable compiler is available (done by fixture).
    2. Create a dummy C++ MatMul kernel.
    3. Use CompileRunner to compile the kernel with a standard flag (e.g., -O2).
    4. Execute the resulting binary.
    5. Verify the binary executed successfully and produced expected output.
    6. Verify the SHA-256 hash of the binary is generated and valid.
    """
    compiler_path, version = compiler_info
    kernel_file = create_dummy_matmul_kernel(temp_build_dir)
    output_binary = temp_build_dir / "matmul_test_bin"
    
    # Configure the runner
    # We create a minimal config for this specific test
    config_manager = create_default_manager()
    
    # Define a specific config for the test
    test_config_id = "test_compile_run_O2"
    flags = ["-O2"]
    
    # Instantiate CompileRunner
    runner = CompileRunner(
        compiler_path=compiler_path,
        output_dir=temp_build_dir,
        config_manager=config_manager
    )
    
    # Compile the kernel
    try:
        binary_path, sha256_hash = runner.compile(
            source_path=kernel_file,
            config_id=test_config_id,
            flags=flags
        )
    except Exception as e:
        pytest.fail(f"Compilation failed: {e}")
    
    # Verify binary exists
    assert binary_path.exists(), f"Compiled binary not found at {binary_path}"
    
    # Verify SHA-256 hash is non-empty and correct
    assert sha256_hash, "SHA-256 hash is empty"
    
    with open(binary_path, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest()
    assert actual_hash == sha256_hash, "Computed hash does not match reported hash"
    
    # Execute the binary
    try:
        result = subprocess.run(
            [str(binary_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check return code
        assert result.returncode == 0, f"Binary execution failed with code {result.returncode}. Stderr: {result.stderr}"
        
        # Verify output contains expected success message
        assert "Success=true" in result.stdout, f"Expected success in output, got: {result.stdout}"
        assert "Latency=" in result.stdout, f"Expected latency measurement in output, got: {result.stdout}"
        
    except subprocess.TimeoutExpired:
        pytest.fail("Binary execution timed out")
    except Exception as e:
        pytest.fail(f"Binary execution failed with exception: {e}")
    
    # If we reach here, the test passed
    # Log the successful run details (optional but good for debugging)
    print(f"Test passed: Compiler {compiler_path} v{version}, Binary {binary_path.name}, Hash {sha256_hash}")
    print(f"Output: {result.stdout.strip()}")