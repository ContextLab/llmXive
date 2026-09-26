"""
Unit tests for the Android emulator wrapper.

These tests verify the functionality of launch_emulator, send_action,
check_crash, get_screenshot, and error handling without requiring
a real Android emulator to be running.
"""

import pytest
import subprocess
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
from pathlib import Path

from utils.emulator import (
    EmulatorError,
    EMU_CRASH,
    EMU_TIMEOUT,
    EMU_NOT_FOUND,
    launch_emulator,
    send_action,
    check_crash,
    get_screenshot,
    stop_emulator,
    get_emulator_status,
    _find_emulator_binary,
    _find_adb_binary,
    with_retry,
    DEFAULT_RETRY_COUNT,
    DEFAULT_RETRY_DELAY
)


class TestEmulatorError:
    """Test the EmulatorError exception class."""
    
    def test_error_creation(self):
        """Test creating an EmulatorError with basic fields."""
        error = EmulatorError(code=EMU_CRASH, message="Test crash")
        assert error.code == EMU_CRASH
        assert error.message == "Test crash"
        assert error.details is None
        assert "EMU_CRASH" in str(error)
        assert "Test crash" in str(error)
    
    def test_error_with_details(self):
        """Test EmulatorError with additional details."""
        details = {"attempt": 1, "reason": "timeout"}
        error = EmulatorError(code=EMU_TIMEOUT, message="Timeout occurred", details=details)
        assert error.details == details
        assert "Details" in str(error)
    
    def test_error_codes(self):
        """Test that error codes match expected values."""
        assert EMU_CRASH == "EMU_CRASH"
        assert EMU_TIMEOUT == "EMU_TIMEOUT"
        assert EMU_NOT_FOUND == "EMU_NOT_FOUND"


class TestFindEmulatorBinary:
    """Test the emulator binary detection logic."""
    
    @patch('utils.emulator.os.path.isfile')
    @patch('utils.emulator.os.access')
    def test_emulator_found_in_default_path(self, mock_access, mock_isfile):
        """Test finding emulator in default path."""
        mock_isfile.return_value = True
        mock_access.return_value = True
        
        with patch('utils.emulator.DEFAULT_EMULATOR_BINARY', '/usr/bin/emulator'):
            found, path = _find_emulator_binary()
            assert found is True
            assert path == '/usr/bin/emulator'
    
    @patch('utils.emulator.subprocess.run')
    def test_emulator_found_via_which(self, mock_run):
        """Test finding emulator via which command."""
        mock_run.return_value = MagicMock(returncode=0, stdout='/usr/bin/emulator\n')
        
        with patch('utils.emulator.os.path.isfile', return_value=False):
            found, path = _find_emulator_binary()
            assert found is True
            assert path == '/usr/bin/emulator'
    
    @patch('utils.emulator.subprocess.run')
    def test_emulator_not_found(self, mock_run):
        """Test when emulator is not found."""
        mock_run.return_value = MagicMock(returncode=1, stdout='')
        
        with patch('utils.emulator.os.path.isfile', return_value=False):
            found, path = _find_emulator_binary()
            assert found is False
            assert path == ""


class TestCheckEmulatorProcess:
    """Test the check_crash function."""
    
    def test_no_process_running(self):
        """Test check_crash when no emulator process exists."""
        with patch('utils.emulator._emulator_process', None):
            result = check_crash()
            assert result["is_crashed"] is True
            assert "No emulator process running" in result["reason"]
    
    @patch('utils.emulator.subprocess.run')
    def test_process_exited(self, mock_run):
        """Test check_crash when process has exited."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Process exited
        mock_process.communicate.return_value = (b"", b"Crash log")
        
        with patch('utils.emulator._emulator_process', mock_process):
            result = check_crash()
            assert result["is_crashed"] is True
            assert "Emulator process exited" in result["reason"]
    
    @patch('utils.emulator._find_adb_binary')
    @patch('utils.emulator.subprocess.run')
    def test_process_running_but_adb_unresponsive(self, mock_run, mock_find_adb):
        """Test check_crash when ADB is unresponsive."""
        mock_find_adb.return_value = (True, '/usr/bin/adb')
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="adb", timeout=5)
        
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process still running
        
        with patch('utils.emulator._emulator_process', mock_process):
            result = check_crash()
            assert result["is_crashed"] is True
            assert "ADB shell command timed out" in result["reason"]
    
    @patch('utils.emulator._find_adb_binary')
    @patch('utils.emulator.subprocess.run')
    def test_emulator_healthy(self, mock_run, mock_find_adb):
        """Test check_crash when emulator is healthy."""
        mock_find_adb.return_value = (True, '/usr/bin/adb')
        mock_run.return_value = MagicMock(returncode=0, stdout="ping\n")
        
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        
        with patch('utils.emulator._emulator_process', mock_process):
            result = check_crash()
            assert result["is_crashed"] is False
            assert result["reason"] is None


class TestLaunchEmulator:
    """Test the launch_emulator function."""
    
    @patch('utils.emulator._find_emulator_binary')
    def test_launch_when_binary_not_found(self, mock_find):
        """Test launch_emulator raises error when binary not found."""
        mock_find.return_value = (False, "")
        
        with pytest.raises(EmulatorError) as excinfo:
            launch_emulator()
        
        assert excinfo.value.code == EMU_NOT_FOUND
        assert "not found" in str(excinfo.value).lower()
    
    @patch('utils.emulator._find_emulator_binary')
    @patch('utils.emulator.subprocess.Popen')
    @patch('utils.emulator._wait_for_adb_connection')
    def test_successful_launch(self, mock_wait, mock_popen, mock_find):
        """Test successful emulator launch."""
        mock_find.return_value = (True, '/usr/bin/emulator')
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        mock_wait.return_value = True
        
        with patch('utils.emulator.time.sleep'):
            pid = launch_emulator()
        
        assert pid == 12345
        mock_popen.assert_called_once()
    
    @patch('utils.emulator._find_emulator_binary')
    @patch('utils.emulator.subprocess.Popen')
    def test_launch_crashes_immediately(self, mock_popen, mock_find):
        """Test launch when emulator crashes immediately."""
        mock_find.return_value = (True, '/usr/bin/emulator')
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = 1  # Exited
        mock_process.communicate.return_value = (b"", b"Crash log")
        mock_popen.return_value = mock_process
        
        with pytest.raises(EmulatorError) as excinfo:
            launch_emulator()
        
        assert excinfo.value.code == EMU_CRASH
        assert "exited immediately" in str(excinfo.value).lower()


class TestSendAction:
    """Test the send_action function."""
    
    @patch('utils.emulator._find_adb_binary')
    def test_send_action_no_emulator(self, mock_find):
        """Test send_action raises error when no emulator running."""
        mock_find.return_value = (True, '/usr/bin/adb')
        
        with patch('utils.emulator._emulator_process', None):
            with pytest.raises(EmulatorError) as excinfo:
                send_action(["input tap 100 200"])
            
            assert excinfo.value.code == EMU_CRASH
            assert "not running" in str(excinfo.value).lower()
    
    @patch('utils.emulator._find_adb_binary')
    @patch('utils.emulator.subprocess.run')
    def test_successful_action_sequence(self, mock_run, mock_find):
        """Test sending a sequence of actions."""
        mock_find.return_value = (True, '/usr/bin/adb')
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        
        with patch('utils.emulator._emulator_process', mock_process):
            result = send_action(["input tap 100 200", "input text hello"])
        
        assert result["total_actions"] == 2
        assert result["successful"] == 2
        assert len(result["results"]) == 2
    
    @patch('utils.emulator._find_adb_binary')
    @patch('utils.emulator.subprocess.run')
    def test_action_timeout(self, mock_run, mock_find):
        """Test action sequence timeout."""
        mock_find.return_value = (True, '/usr/bin/adb')
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="adb", timeout=5)
        
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        
        with patch('utils.emulator._emulator_process', mock_process):
            with pytest.raises(EmulatorError) as excinfo:
                send_action(["input tap 100 200"], timeout=1)
        
        assert excinfo.value.code == EMU_TIMEOUT


class TestCheckCrash:
    """Additional tests for check_crash."""
    
    def test_crash_detection_no_process(self):
        """Verify crash detection when process is None."""
        with patch('utils.emulator._emulator_process', None):
            result = check_crash()
            assert result["is_crashed"] is True
    
    def test_crash_detection_exited_process(self):
        """Verify crash detection when process has exited."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 1
        mock_process.communicate.return_value = (b"", b"Error")
        
        with patch('utils.emulator._emulator_process', mock_process):
            result = check_crash()
            assert result["is_crashed"] is True


class TestGetScreenshot:
    """Test the get_screenshot function."""
    
    @patch('utils.emulator.check_crash')
    def test_screenshot_when_crashed(self, mock_check):
        """Test get_screenshot raises error when emulator crashed."""
        mock_check.return_value = {"is_crashed": True, "reason": "Test crash", "details": {}}
        
        with pytest.raises(EmulatorError) as excinfo:
            get_screenshot()
        
        assert excinfo.value.code == EMU_CRASH
        assert "crashed" in str(excinfo.value).lower()
    
    @patch('utils.emulator._find_adb_binary')
    @patch('utils.emulator.check_crash')
    def test_screenshot_success_to_file(self, mock_check, mock_find):
        """Test successful screenshot capture to file."""
        mock_check.return_value = {"is_crashed": False}
        mock_find.return_value = (True, '/usr/bin/adb')
        
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        
        with patch('utils.emulator.subprocess.run', return_value=MagicMock(returncode=0)):
            with patch('utils.emulator._emulator_process', mock_process):
                result = get_screenshot(output_path="/tmp/test.png")
        
        assert result == "/tmp/test.png"
    
    @patch('utils.emulator._find_adb_binary')
    @patch('utils.emulator.check_crash')
    @patch('utils.emulator.tempfile.NamedTemporaryFile')
    @patch('builtins.open', new_callable=mock_open, read_data=b"fake_image_data")
    @patch('utils.emulator.os.remove')
    @patch('utils.emulator.os.path.exists')
    def test_screenshot_success_base64(self, mock_exists, mock_remove, mock_open_file, mock_temp, mock_check, mock_find):
        """Test successful screenshot capture as base64."""
        mock_check.return_value = {"is_crashed": False}
        mock_find.return_value = (True, '/usr/bin/adb')
        mock_temp.return_value.__enter__.return_value.name = "/tmp/temp.png"
        mock_exists.return_value = True
        
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        
        with patch('utils.emulator.subprocess.run', return_value=MagicMock(returncode=0)):
            with patch('utils.emulator._emulator_process', mock_process):
                result = get_screenshot()
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestStopEmulator:
    """Test the stop_emulator function."""
    
    def test_stop_no_process(self):
        """Test stop_emulator when no process is running."""
        with patch('utils.emulator._emulator_process', None):
            result = stop_emulator()
            assert result["success"] is True
            assert "No emulator process running" in result["message"]
    
    @patch('utils.emulator.subprocess.run')
    def test_stop_graceful(self, mock_run):
        """Test graceful emulator stop."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.wait.return_value = None
        
        with patch('utils.emulator._emulator_process', mock_process):
            result = stop_emulator(force=False)
            assert result["success"] is True
    
    @patch('utils.emulator.subprocess.run')
    def test_stop_force(self, mock_run):
        """Test force stop of emulator."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.wait.return_value = None
        
        with patch('utils.emulator._emulator_process', mock_process):
            result = stop_emulator(force=True)
            assert result["success"] is True


class TestWithRetry:
    """Test the retry decorator."""
    
    def test_retry_on_failure_then_success(self):
        """Test that function retries on failure then succeeds."""
        call_count = 0
        
        @with_retry(max_retries=3, delay=0.01)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise EmulatorError(code=EMU_CRASH, message="Temporary failure")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_exhausted(self):
        """Test that function raises after max retries exhausted."""
        call_count = 0
        
        @with_retry(max_retries=2, delay=0.01)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise EmulatorError(code=EMU_CRASH, message="Always fails")
        
        with pytest.raises(EmulatorError) as excinfo:
            always_fail()
        
        assert excinfo.value.code == EMU_CRASH
        assert call_count == 3  # Initial + 2 retries
    
    def test_retry_on_timeout(self):
        """Test retry on subprocess timeout."""
        call_count = 0
        
        @with_retry(max_retries=2, delay=0.01)
        def timeout_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise subprocess.TimeoutExpired(cmd="test", timeout=1)
            return "success"
        
        result = timeout_function()
        assert result == "success"
        assert call_count == 2


class TestGetEmulatorStatus:
    """Test the get_emulator_status function."""
    
    def test_status_no_process(self):
        """Test status when no emulator running."""
        with patch('utils.emulator._emulator_process', None):
            with patch('utils.emulator.check_crash', return_value={"is_crashed": True}):
                status = get_emulator_status()
                assert status["is_running"] is False
                assert status["is_ready"] is False
                assert status["is_crashed"] is True
    
    @patch('utils.emulator.check_crash')
    def test_status_running_process(self, mock_check):
        """Test status when emulator is running."""
        mock_check.return_value = {"is_crashed": False}
        
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        
        with patch('utils.emulator._emulator_process', mock_process):
            with patch('utils.emulator._emulator_ready', True):
                with patch('utils.emulator._emulator_pid', 12345):
                    status = get_emulator_status()
                    assert status["is_running"] is True
                    assert status["is_ready"] is True
                    assert status["is_crashed"] is False
                    assert status["pid"] == 12345