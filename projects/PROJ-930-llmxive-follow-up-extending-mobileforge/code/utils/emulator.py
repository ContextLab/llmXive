"""
Headless Android emulator wrapper with robust retry logic for environment crashes.

Provides functions to launch, interact with, and monitor a headless Android emulator
instance, handling common failure modes like crashes, timeouts, and missing binaries.
"""

import os
import subprocess
import time
import signal
import sys
import re
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Error codes as constants (also available as an Enum for type safety)
class EmulatorErrorCode(str, Enum):
    EMU_CRASH = "EMU_CRASH"
    EMU_TIMEOUT = "EMU_TIMEOUT"
    EMU_NOT_FOUND = "EMU_NOT_FOUND"

# Module-level constants for backward compatibility
EMU_CRASH = EmulatorErrorCode.EMU_CRASH.value
EMU_TIMEOUT = EmulatorErrorCode.EMU_TIMEOUT.value
EMU_NOT_FOUND = EmulatorErrorCode.EMU_NOT_FOUND.value

@dataclass
class EmulatorError(Exception):
    """Custom exception for emulator-related errors."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        base = f"[{self.code}] {self.message}"
        if self.details:
            base += f" (Details: {self.details})"
        return base

# Global state to track emulator process
_emulator_process: Optional[subprocess.Popen] = None
_emulator_pid: Optional[int] = None
_last_error: Optional[EmulatorError] = None
_emulator_ready: bool = False

# Configuration constants
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 2.0  # seconds
DEFAULT_STARTUP_TIMEOUT = 120  # seconds
DEFAULT_ACTION_TIMEOUT = 30  # seconds
DEFAULT_AVD_NAME = "test_device"
DEFAULT_EMULATOR_BINARY = "emulator"
DEFAULT_ADB_BINARY = "adb"

def _find_emulator_binary() -> Tuple[bool, str]:
    """
    Locate the emulator binary in the system PATH.
    
    Returns:
        Tuple of (found: bool, path: str)
    """
    # Check common locations
    possible_paths = [
        DEFAULT_EMULATOR_BINARY,
        os.path.expanduser("~/Android/Sdk/emulator/emulator"),
        os.path.expanduser("~/Library/Android/sdk/emulator/emulator"),
        "/usr/lib/android-sdk/emulator/emulator",
    ]
    
    for path in possible_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return True, path
        
        # Try with 'which' for PATH resolution
        try:
            result = subprocess.run(
                ["which", path],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    
    return False, ""

def _find_adb_binary() -> Tuple[bool, str]:
    """
    Locate the ADB binary in the system PATH.
    
    Returns:
        Tuple of (found: bool, path: str)
    """
    possible_paths = [
        DEFAULT_ADB_BINARY,
        os.path.expanduser("~/Android/Sdk/platform-tools/adb"),
        os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),
        "/usr/lib/android-sdk/platform-tools/adb",
    ]
    
    for path in possible_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return True, path
        
        try:
            result = subprocess.run(
                ["which", path],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    
    return False, ""

def with_retry(max_retries: int = DEFAULT_RETRY_COUNT, delay: float = DEFAULT_RETRY_DELAY):
    """
    Decorator to add retry logic to emulator functions.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except EmulatorError as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay)
                        continue
                    raise
                except subprocess.TimeoutExpired as e:
                    last_exception = EmulatorError(
                        code=EMU_TIMEOUT,
                        message=f"Operation timed out after {delay * (attempt + 1):.1f}s",
                        details={"attempt": attempt + 1, "original_error": str(e)}
                    )
                    if attempt < max_retries:
                        time.sleep(delay)
                        continue
                    raise
                except Exception as e:
                    last_exception = EmulatorError(
                        code=EMU_CRASH,
                        message=f"Unexpected error: {str(e)}",
                        details={"attempt": attempt + 1, "error_type": type(e).__name__}
                    )
                    if attempt < max_retries:
                        time.sleep(delay)
                        continue
                    raise
            
            # Should not reach here, but just in case
            raise last_exception
        return wrapper
    return decorator

@with_retry(max_retries=DEFAULT_RETRY_COUNT, delay=DEFAULT_RETRY_DELAY)
def launch_emulator(
    avd_name: str = DEFAULT_AVD_NAME,
    headless: bool = True,
    no_window: bool = True,
    no_audio: bool = True,
    no_boot_complete: bool = False,
    extra_args: Optional[List[str]] = None
) -> int:
    """
    Launch a headless Android emulator instance.
    
    Args:
        avd_name: Name of the Android Virtual Device to launch
        headless: Run in headless mode (no GUI)
        no_window: Disable the window display
        no_audio: Disable audio
        no_boot_complete: Don't wait for boot completion
        extra_args: Additional arguments to pass to the emulator
    
    Returns:
        Process ID of the launched emulator
    
    Raises:
        EmulatorError: If emulator binary not found or launch fails
    """
    global _emulator_process, _emulator_pid, _emulator_ready
    
    # Check for emulator binary
    found, emulator_path = _find_emulator_binary()
    if not found:
        raise EmulatorError(
            code=EMU_NOT_FOUND,
            message="Android emulator binary not found in PATH or default locations",
            details={"searched_paths": [
                DEFAULT_EMULATOR_BINARY,
                os.path.expanduser("~/Android/Sdk/emulator/emulator"),
            ]}
        )
    
    # Build command
    cmd = [
        emulator_path,
        "-avd", avd_name,
        "-no-snapshot-save",
    ]
    
    if headless:
        cmd.append("-no-window")
    if no_window:
        cmd.append("-no-window")
    if no_audio:
        cmd.append("-no-audio")
    if no_boot_complete:
        cmd.append("-no-boot-anim")
    
    if extra_args:
        cmd.extend(extra_args)
    
    try:
        # Start the emulator process
        _emulator_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True  # Detach from terminal
        )
        _emulator_pid = _emulator_process.pid
        _emulator_ready = False
        
        # Wait a moment for the process to start
        time.sleep(2)
        
        # Check if process is still running
        if _emulator_process.poll() is not None:
            stdout, stderr = _emulator_process.communicate()
            raise EmulatorError(
                code=EMU_CRASH,
                message="Emulator process exited immediately after launch",
                details={
                    "returncode": _emulator_process.returncode,
                    "stdout": stdout.decode("utf-8", errors="ignore")[:500],
                    "stderr": stderr.decode("utf-8", errors="ignore")[:500]
                }
            )
        
        # Wait for emulator to be ready (ADB connection)
        _wait_for_adb_connection(timeout=DEFAULT_STARTUP_TIMEOUT)
        _emulator_ready = True
        
        return _emulator_pid
        
    except FileNotFoundError:
        raise EmulatorError(
            code=EMU_NOT_FOUND,
            message=f"Emulator binary not executable: {emulator_path}",
            details={"path": emulator_path}
        )
    except Exception as e:
        raise EmulatorError(
            code=EMU_CRASH,
            message=f"Failed to launch emulator: {str(e)}",
            details={"command": " ".join(cmd), "error": str(e)}
        )

def _wait_for_adb_connection(timeout: int = DEFAULT_STARTUP_TIMEOUT) -> bool:
    """
    Wait for ADB to detect the emulator.
    
    Args:
        timeout: Maximum time to wait in seconds
    
    Returns:
        True if ADB connection established, False otherwise
    """
    found, adb_path = _find_adb_binary()
    if not found:
        raise EmulatorError(
            code=EMU_NOT_FOUND,
            message="ADB binary not found - cannot wait for connection",
            details={"searched_paths": [DEFAULT_ADB_BINARY]}
        )
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                [adb_path, "devices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Check if emulator device is listed
                if "emulator-5554" in result.stdout or "device" in result.stdout:
                    return True
            
            time.sleep(2)
        except subprocess.TimeoutExpired:
            continue
        except Exception:
            continue
    
    return False

@with_retry(max_retries=3, delay=1.0)
def send_action(action_seq: List[str], timeout: int = DEFAULT_ACTION_TIMEOUT) -> Dict[str, Any]:
    """
    Send a sequence of actions to the emulator via ADB.
    
    Args:
        action_seq: List of ADB commands to execute (e.g., ["input tap 100 200", "input text hello"])
        timeout: Maximum time to wait for all actions in seconds
    
    Returns:
        Dictionary with execution results
    
    Raises:
        EmulatorError: If emulator is not running or actions fail
    """
    global _emulator_process
    
    if _emulator_process is None or _emulator_process.poll() is not None:
        raise EmulatorError(
            code=EMU_CRASH,
            message="Emulator is not running or has crashed",
            details={"process_state": "not_running" if _emulator_process is None else "exited"}
        )
    
    found, adb_path = _find_adb_binary()
    if not found:
        raise EmulatorError(
            code=EMU_NOT_FOUND,
            message="ADB binary not found",
            details={}
        )
    
    results = []
    start_time = time.time()
    
    for i, action in enumerate(action_seq):
        if time.time() - start_time > timeout:
            raise EmulatorError(
                code=EMU_TIMEOUT,
                message=f"Action sequence timed out after {timeout}s",
                details={"completed_actions": len(results), "current_action": action}
            )
        
        try:
            result = subprocess.run(
                [adb_path, "shell", action],
                capture_output=True,
                text=True,
                timeout=timeout - (time.time() - start_time)
            )
            
            results.append({
                "action": action,
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            })
            
        except subprocess.TimeoutExpired:
            raise EmulatorError(
                code=EMU_TIMEOUT,
                message=f"Action '{action}' timed out",
                details={"action_index": i}
            )
        except Exception as e:
            results.append({
                "action": action,
                "success": False,
                "error": str(e),
                "returncode": -1
            })
    
    return {
        "total_actions": len(action_seq),
        "successful": sum(1 for r in results if r.get("success", False)),
        "results": results,
        "elapsed_time": time.time() - start_time
    }

def check_crash() -> Dict[str, Any]:
    """
    Check if the emulator has crashed or become unresponsive.
    
    Returns:
        Dictionary with crash status and details
    """
    global _emulator_process, _emulator_ready
    
    if _emulator_process is None:
        return {
            "is_crashed": True,
            "reason": "No emulator process running",
            "details": {}
        }
    
    # Check if process is still running
    if _emulator_process.poll() is not None:
        stdout, stderr = _emulator_process.communicate()
        return {
            "is_crashed": True,
            "reason": "Emulator process exited",
            "details": {
                "returncode": _emulator_process.returncode,
                "stdout": stdout.decode("utf-8", errors="ignore")[:1000],
                "stderr": stderr.decode("utf-8", errors="ignore")[:1000]
            }
        }
    
    # Check ADB connection
    found, adb_path = _find_adb_binary()
    if not found:
        return {
            "is_crashed": True,
            "reason": "ADB binary not found",
            "details": {}
        }
    
    try:
        result = subprocess.run(
            [adb_path, "shell", "echo", "ping"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return {
                "is_crashed": True,
                "reason": "ADB shell command failed",
                "details": {
                    "returncode": result.returncode,
                    "stderr": result.stderr.strip()
                }
            }
        
        return {
            "is_crashed": False,
            "reason": None,
            "details": {
                "process_running": True,
                "adb_responsive": True
            }
        }
        
    except subprocess.TimeoutExpired:
        return {
            "is_crashed": True,
            "reason": "ADB shell command timed out",
            "details": {}
        }
    except Exception as e:
        return {
            "is_crashed": True,
            "reason": f"Error checking emulator status: {str(e)}",
            "details": {"error": str(e)}
        }

@with_retry(max_retries=2, delay=0.5)
def get_screenshot(output_path: Optional[str] = None) -> str:
    """
    Capture a screenshot from the emulator.
    
    Args:
        output_path: Optional path to save the screenshot. If None, returns base64 encoded image.
    
    Returns:
        Path to saved screenshot or base64 encoded image string
    
    Raises:
        EmulatorError: If emulator is crashed or screenshot fails
    """
    global _emulator_process
    
    crash_status = check_crash()
    if crash_status["is_crashed"]:
        raise EmulatorError(
            code=EMU_CRASH,
            message="Cannot take screenshot: emulator is crashed",
            details=crash_status["details"]
        )
    
    found, adb_path = _find_adb_binary()
    if not found:
        raise EmulatorError(
            code=EMU_NOT_FOUND,
            message="ADB binary not found",
            details={}
        )
    
    try:
        if output_path:
            # Take screenshot and pull to local file
            subprocess.run(
                [adb_path, "shell", "screencap", "-p", "/sdcard/screenshot.png"],
                capture_output=True,
                timeout=10
            )
            
            subprocess.run(
                [adb_path, "pull", "/sdcard/screenshot.png", output_path],
                capture_output=True,
                timeout=10
            )
            
            # Clean up remote file
            subprocess.run(
                [adb_path, "shell", "rm", "/sdcard/screenshot.png"],
                capture_output=True,
                timeout=5
            )
            
            return output_path
        else:
            # Take screenshot and pull as base64
            import base64
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                temp_path = tmp.name
            
            try:
                subprocess.run(
                    [adb_path, "shell", "screencap", "-p", "/sdcard/screenshot.png"],
                    capture_output=True,
                    timeout=10
                )
                
                subprocess.run(
                    [adb_path, "pull", "/sdcard/screenshot.png", temp_path],
                    capture_output=True,
                    timeout=10
                )
                
                with open(temp_path, "rb") as f:
                    image_data = f.read()
                
                base64_image = base64.b64encode(image_data).decode("utf-8")
                return base64_image
                
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                subprocess.run(
                    [adb_path, "shell", "rm", "/sdcard/screenshot.png"],
                    capture_output=True,
                    timeout=5
                )
                
    except subprocess.TimeoutExpired:
        raise EmulatorError(
            code=EMU_TIMEOUT,
            message="Screenshot capture timed out",
            details={}
        )
    except Exception as e:
        raise EmulatorError(
            code=EMU_CRASH,
            message=f"Failed to capture screenshot: {str(e)}",
            details={"error": str(e)}
        )

def stop_emulator(force: bool = False) -> Dict[str, Any]:
    """
    Stop the running emulator instance.
    
    Args:
        force: If True, forcefully kill the process
    
    Returns:
        Dictionary with stop status
    """
    global _emulator_process, _emulator_pid, _emulator_ready
    
    if _emulator_process is None:
        return {
            "success": True,
            "message": "No emulator process running",
            "details": {}
        }
    
    try:
        if _emulator_process.poll() is None:
            if force:
                _emulator_process.terminate()
                _emulator_process.wait(timeout=5)
            else:
                # Try graceful shutdown via ADB first
                found, adb_path = _find_adb_binary()
                if found:
                    try:
                        subprocess.run(
                            [adb_path, "shell", "am", "broadcast", "-a", "android.intent.action.SHUTDOWN"],
                            capture_output=True,
                            timeout=10
                        )
                        # Wait a bit for graceful shutdown
                        for _ in range(10):
                            if _emulator_process.poll() is not None:
                                break
                            time.sleep(1)
                        
                        if _emulator_process.poll() is None:
                            _emulator_process.terminate()
                            _emulator_process.wait(timeout=5)
                    except:
                        _emulator_process.terminate()
                        _emulator_process.wait(timeout=5)
                else:
                    _emulator_process.terminate()
                    _emulator_process.wait(timeout=5)
        
        stdout, stderr = _emulator_process.communicate()
        _emulator_process = None
        _emulator_pid = None
        _emulator_ready = False
        
        return {
            "success": True,
            "message": "Emulator stopped successfully",
            "details": {
                "returncode": _emulator_process.returncode if _emulator_process else None,
                "stdout": stdout.decode("utf-8", errors="ignore")[:500] if stdout else "",
                "stderr": stderr.decode("utf-8", errors="ignore")[:500] if stderr else ""
            }
        }
        
    except subprocess.TimeoutExpired:
        _emulator_process.kill()
        return {
            "success": False,
            "message": "Failed to stop emulator gracefully, force kill required",
            "details": {}
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error stopping emulator: {str(e)}",
            "details": {"error": str(e)}
        }

def get_emulator_status() -> Dict[str, Any]:
    """
    Get the current status of the emulator.
    
    Returns:
        Dictionary with emulator status information
    """
    global _emulator_process, _emulator_ready, _emulator_pid
    
    crash_status = check_crash()
    
    return {
        "is_running": _emulator_process is not None and _emulator_process.poll() is None,
        "is_ready": _emulator_ready,
        "is_crashed": crash_status["is_crashed"],
        "pid": _emulator_pid,
        "crash_reason": crash_status.get("reason"),
        "crash_details": crash_status.get("details", {})
    }

# Cleanup on module exit
def _cleanup():
    """Clean up emulator resources on module exit."""
    if _emulator_process is not None and _emulator_process.poll() is None:
        stop_emulator(force=True)

import atexit
atexit.register(_cleanup)
