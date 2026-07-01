"""
Task T013: Verify no CUDA-related errors occur when running on a GPU-less runner.

This script attempts to import torch and check CUDA availability.
It is designed to run in a CPU-only environment (CUDA_VISIBLE_DEVICES="")
and must exit cleanly (code 0) if no GPU is detected, or fail loudly (code 1)
if an unexpected CUDA import error occurs.

It writes the verification result to outputs/health/cuda_verification.json.
"""
import os
import sys
import json
import torch

# Ensure we are forcing CPU mode as per T005
os.environ["CUDA_VISIBLE_DEVICES"] = ""

OUTPUT_PATH = "outputs/health/cuda_verification.json"

def main():
    result = {
        "task_id": "T013",
        "status": "unknown",
        "torch_version": torch.__version__,
        "cuda_available": False,
        "error_message": None,
        "reason": "Verification successful"
    }

    try:
        # Attempt to initialize CUDA context
        # In a CPU-only env, this should return False or raise a specific error
        # if the driver is missing but we expect it to be missing.
        # We specifically check if torch.cuda.is_available() returns False
        # without raising an ImportError for the CUDA backend.
        
        is_available = torch.cuda.is_available()
        result["cuda_available"] = is_available

        if is_available:
            # If it says available but we forced CUDA_VISIBLE_DEVICES="",
            # something is misconfigured, but strictly speaking, no "error" occurred.
            # However, for a GPU-less runner, we expect False.
            result["status"] = "warning"
            result["reason"] = "CUDA reported available despite forced CPU mode. Check environment."
        else:
            result["status"] = "success"
            result["reason"] = "CUDA correctly reported as unavailable on CPU-only runner."

        # Additional check: Try to get device count to ensure no crash
        try:
            device_count = torch.cuda.device_count()
            result["cuda_device_count"] = device_count
        except Exception as e:
            # This should not happen if is_available is False, but handle gracefully
            result["error_message"] = str(e)
            result["status"] = "failure"
            result["reason"] = f"Failed to query device count: {e}"

    except ImportError as e:
        # This is the critical failure case for a CPU-only runner that expects
        # torch to work without CUDA. If torch itself fails to import, that's fatal.
        # However, usually torch imports fine but CUDA backend is missing.
        # We catch this to distinguish between "No CUDA" and "Broken Torch".
        if "CUDA" in str(e) or "cudart" in str(e):
            result["status"] = "success"
            result["reason"] = "CUDA backend missing as expected on CPU runner (ImportError caught)."
            result["error_message"] = str(e)
        else:
            result["status"] = "failure"
            result["reason"] = f"Unexpected ImportError: {e}"
            result["error_message"] = str(e)
    except Exception as e:
        result["status"] = "failure"
        result["reason"] = f"Unexpected error during CUDA check: {e}"
        result["error_message"] = str(e)

    # Write result to disk
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Verification complete. Result written to {OUTPUT_PATH}")
    print(f"Status: {result['status']}")
    print(f"Reason: {result['reason']}")

    # Exit with 0 if verification passed (no blocking CUDA errors)
    if result["status"] in ["success", "warning"]:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()