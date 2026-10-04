"""
Emulator interface wrapper for interacting with the AndroidWorld dataset evaluation environment.

This module provides a thin abstraction over the AndroidWorld emulator to support
task execution, action sending, and crash detection for model evaluation.

Error Codes:
  EMU_CRASH: The emulator process crashed during execution
  EMU_TIMEOUT: The emulator operation timed out
  EMU_NOT_FOUND: The requested emulator binary or process was not found
"""

import os
import subprocess
import time
import signal
import sys
import re
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

# Error code definitions as required by the specification
class EmulatorErrorCode(Enum):
    EMU_CRASH = "EMU_CRASH"
    EMU_TIMEOUT = "EMU_TIMEOUT"
    EMU_NOT_FOUND = "EMU_NOT_FOUND"

class EmulatorError(Exception):
    """Custom exception for emulator-related errors."""
    def __init__(self, code: EmulatorErrorCode, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code.value}: {message}")

# Global state for emulator process
_emulator_process: Optional[subprocess.Popen] = None
_emulator_pid: Optional[int] = None
_emulator_timeout_seconds: int = 300  # Default 5 minute timeout

def _find_emulator_binary() -> Optional[Path]:
    """
    Locate the Android emulator binary in the system PATH or common installation locations.
    
    Returns:
        Path to the emulator binary if found, None otherwise.
    """
    # Common emulator binary names
    binary_names = ["emulator", "avdmanager", "sdkmanager"]
    
    # Check system PATH first
    for binary in binary_names:
        path = shutil.which(binary)
        if path:
            return Path(path)
    
    # Check common Android SDK locations
    sdk_paths = [
        Path(os.environ.get("ANDROID_HOME", "")) / "emulator" / "emulator",
        Path(os.environ.get("ANDROID_SDK_ROOT", "")) / "emulator" / "emulator",
        Path.home() / "Android" / "Sdk" / "emulator" / "emulator",
        Path("/usr/local/android-sdk/emulator/emulator"),
    ]
    
    for sdk_path in sdk_paths:
        if sdk_path.exists():
            return sdk_path
    
    return None

def _check_emulator_process() -> bool:
    """
    Check if the emulator process is currently running.
    
    Returns:
        True if the process is running, False otherwise.
    """
    global _emulator_pid
    if _emulator_pid is None:
        return False
    
    try:
        # Check if process exists
        os.kill(_emulator_pid, 0)
        return True
    except OSError:
        return False

def _get_emulator_screenshot_path() -> Path:
    """
    Generate a path for the emulator screenshot.
    
    Returns:
        Path to the screenshot file.
    """
    screenshot_dir = Path("data/evaluation/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time() * 1000)
    return screenshot_dir / f"screenshot_{timestamp}.png"

def launch_emulator(avd_name: Optional[str] = None, timeout: int = 300) -> bool:
    """
    Launch the Android emulator with the specified AVD (Android Virtual Device).
    
    Args:
        avd_name: Name of the AVD to launch. If None, uses the default AVD.
        timeout: Maximum time in seconds to wait for the emulator to boot.
    
    Returns:
        True if the emulator launched successfully, False otherwise.
    
    Raises:
        EmulatorError: If the emulator binary is not found or fails to start.
    """
    global _emulator_process, _emulator_pid, _emulator_timeout_seconds
    
    _emulator_timeout_seconds = timeout
    
    # Find emulator binary
    emulator_path = _find_emulator_binary()
    if not emulator_path:
        raise EmulatorError(
            EmulatorErrorCode.EMU_NOT_FOUND,
            "Android emulator binary not found in PATH or common SDK locations. "
            "Please install Android SDK and set ANDROID_HOME or ANDROID_SDK_ROOT."
        )
    
    # Check if already running
    if _check_emulator_process():
        return True
    
    # Build command
    cmd = [str(emulator_path)]
    if avd_name:
        cmd.extend(["-avd", avd_name])
    else:
        # Try to find any available AVD
        avd_path = emulator_path.parent.parent / "avd"
        if avd_path.exists():
            avds = list(avd_path.glob("*.ini"))
            if avds:
                cmd.extend(["-avd", avds[0].stem])
    
    cmd.extend([
        "-no-window",
        "-no-snapshot",
        "-camera-back", "none",
        "-camera-front", "none",
        "-gpu", "swiftshader_indirect",
        "-accel", "auto"
    ])
    
    try:
        # Start emulator process
        _emulator_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        _emulator_pid = _emulator_process.pid
        
        # Wait for emulator to boot
        start_time = time.time()
        boot_complete = False
        
        while time.time() - start_time < timeout:
            if not _check_emulator_process():
                raise EmulatorError(
                    EmulatorErrorCode.EMU_CRASH,
                    "Emulator process crashed during startup"
                )
            
            # Check for boot completion signal
            if _emulator_process.stdout:
                line = _emulator_process.stdout.readline()
                if b"boot completed" in line.lower() or b"sys.boot_completed" in line.lower():
                    boot_complete = True
                    break
            
            time.sleep(1)
        
        if not boot_complete:
            raise EmulatorError(
                EmulatorErrorCode.EMU_TIMEOUT,
                f"Emulator failed to boot within {timeout} seconds"
            )
        
        return True
        
    except FileNotFoundError:
        raise EmulatorError(
            EmulatorErrorCode.EMU_NOT_FOUND,
            f"Emulator binary not found: {emulator_path}"
        )
    except Exception as e:
        raise EmulatorError(
            EmulatorErrorCode.EMU_CRASH,
            f"Failed to launch emulator: {str(e)}"
        )

def send_action(action_seq: List[str], timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Send a sequence of actions to the emulator.
    
    Args:
        action_seq: List of actions to perform (e.g., ["tap", "swipe", "input_text"]).
        timeout: Optional timeout for the action sequence.
    
    Returns:
        Dictionary containing action execution results.
    
    Raises:
        EmulatorError: If the emulator is not running or the action fails.
    """
    global _emulator_process, _emulator_timeout_seconds
    
    if timeout is None:
        timeout = _emulator_timeout_seconds
    
    # Check if emulator is running
    if not _check_emulator_process():
        raise EmulatorError(
            EmulatorErrorCode.EMU_NOT_FOUND,
            "Emulator is not running. Call launch_emulator() first."
        )
    
    results = {
        "actions_executed": 0,
        "actions_failed": 0,
        "details": []
    }
    
    # Use ADB to send actions (assuming ADB is available)
    adb_path = shutil.which("adb")
    if not adb_path:
        # Try to find ADB in Android SDK
        sdk_root = Path(os.environ.get("ANDROID_SDK_ROOT", ""))
        adb_path = sdk_root / "platform-tools" / "adb"
        if not adb_path.exists():
            raise EmulatorError(
                EmulatorErrorCode.EMU_NOT_FOUND,
                "ADB not found. Please install Android Platform Tools."
            )
        adb_path = str(adb_path)
    
    for action in action_seq:
        try:
            # Parse action format: "action_type:parameters"
            if ":" in action:
                action_type, params = action.split(":", 1)
            else:
                action_type = action
                params = ""
            
            # Execute action via ADB shell
            if action_type == "tap":
                # Format: tap x y
                coords = params.split()
                if len(coords) != 2:
                    raise ValueError(f"Invalid tap coordinates: {params}")
                cmd = ["input", "tap", coords[0], coords[1]]
            
            elif action_type == "swipe":
                # Format: swipe x1 y1 x2 y2 duration
                swipe_params = params.split()
                if len(swipe_params) != 4:
                    raise ValueError(f"Invalid swipe parameters: {params}")
                cmd = ["input", "swipe"] + swipe_params
            
            elif action_type == "input_text":
                # Format: input_text "text"
                text = params.strip('"')
                cmd = ["input", "text", text.replace(" ", "%s")]
            
            elif action_type == "key":
                # Format: key key_code
                key_code = params
                cmd = ["input", "keyevent", key_code]
            
            else:
                raise ValueError(f"Unknown action type: {action_type}")
            
            # Execute via ADB
            process = subprocess.Popen(
                [adb_path, "shell"] + cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                results["actions_executed"] += 1
                results["details"].append({
                    "action": action,
                    "status": "success"
                })
            else:
                results["actions_failed"] += 1
                results["details"].append({
                    "action": action,
                    "status": "failed",
                    "error": stderr.decode() if stderr else "Unknown error"
                })
            
        except subprocess.TimeoutExpired:
            results["actions_failed"] += 1
            results["details"].append({
                "action": action,
                "status": "timeout"
            })
        except Exception as e:
            results["actions_failed"] += 1
            results["details"].append({
                "action": action,
                "status": "error",
                "error": str(e)
            })
    
    return results

def check_crash() -> Tuple[bool, Optional[str]]:
    """
    Check if the emulator has crashed.
    
    Returns:
        Tuple of (is_crashed, error_message).
    """
    global _emulator_process, _emulator_pid
    
    if not _check_emulator_process():
        # Process is not running
        if _emulator_pid is not None:
            return True, "Emulator process terminated unexpectedly"
        return False, None
    
    # Check for crash indicators in logcat (if available)
    try:
        adb_path = shutil.which("adb")
        if not adb_path:
            return False, None
        
        # Check for ANR or crash in logcat
        process = subprocess.Popen(
            [adb_path, "shell", "logcat", "-d", "-s", "AndroidRuntime", "FATAL"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        
        stdout, _ = process.communicate()
        log_output = stdout.decode()
        
        if "FATAL" in log_output or "CRASH" in log_output:
            return True, log_output[:500]  # Return first 500 chars
        
    except Exception:
        pass
    
    return False, None

def get_screenshot() -> Optional[Path]:
    """
    Capture a screenshot from the emulator.
    
    Returns:
        Path to the screenshot file, or None if capture failed.
    
    Raises:
        EmulatorError: If the emulator is not running.
    """
    if not _check_emulator_process():
        raise EmulatorError(
            EmulatorErrorCode.EMU_NOT_FOUND,
            "Emulator is not running. Call launch_emulator() first."
        )
    
    try:
        adb_path = shutil.which("adb")
        if not adb_path:
            raise EmulatorError(
                EmulatorErrorCode.EMU_NOT_FOUND,
                "ADB not found. Please install Android Platform Tools."
            )
        
        # Create local screenshot path
        local_path = _get_emulator_screenshot_path()
        
        # Capture screenshot to device
        device_path = "/tmp/screenshot.png"
        process = subprocess.Popen(
            [adb_path, "shell", "screencap", "-p", device_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )
        process.communicate()
        
        # Pull screenshot to local
        process = subprocess.Popen(
            [adb_path, "pull", device_path, str(local_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )
        stdout, stderr = process.communicate()
        
        if process.returncode == 0 and local_path.exists():
            return local_path
        else:
            # Try alternative method: screenshot via ADB shell
            process = subprocess.Popen(
                [adb_path, "shell", "screencap", "-p"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                with open(local_path, "wb") as f:
                    f.write(stdout)
                return local_path
        
        return None
        
    except Exception as e:
        raise EmulatorError(
            EmulatorErrorCode.EMU_CRASH,
            f"Failed to capture screenshot: {str(e)}"
        )

def stop_emulator() -> bool:
    """
    Stop the running emulator process.
    
    Returns:
        True if the emulator was stopped successfully.
    """
    global _emulator_process, _emulator_pid
    
    if not _check_emulator_process():
        return False
    
    try:
        # Send kill signal to process group
        if _emulator_process:
            os.killpg(os.getpgid(_emulator_process.pid), signal.SIGTERM)
            _emulator_process.wait(timeout=30)
        
        # Clean up PID
        _emulator_pid = None
        _emulator_process = None
        return True
        
    except Exception:
        # Force kill if graceful shutdown fails
        try:
            if _emulator_pid:
                os.kill(_emulator_pid, signal.SIGKILL)
            _emulator_pid = None
            _emulator_process = None
            return True
        except Exception:
            return False

def get_emulator_status() -> Dict[str, Any]:
    """
    Get the current status of the emulator.
    
    Returns:
        Dictionary containing emulator status information.
    """
    is_running = _check_emulator_process()
    is_crashed, crash_msg = check_crash()
    
    return {
        "running": is_running,
        "crashed": is_crashed,
        "crash_message": crash_msg,
        "pid": _emulator_pid,
        "timeout_seconds": _emulator_timeout_seconds
    }

# Convenience function with retry logic
def with_retry(max_retries: int = 3, delay: float = 2.0):
    """
    Decorator to add retry logic to emulator functions.
    
    Args:
        max_retries: Maximum number of retry attempts.
        delay: Delay between retries in seconds.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except EmulatorError as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                        continue
                    raise
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                        continue
                    raise
            raise last_exception
        return wrapper
    return decorator

# Import shutil at module level for binary detection
import shutil
