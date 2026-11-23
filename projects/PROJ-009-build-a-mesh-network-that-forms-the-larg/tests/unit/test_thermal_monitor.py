"""
Unit tests for thermal_monitor.py
"""
import pytest
from unittest.mock import patch, mock_open, MagicMock
import sys
import os

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from orchestrator.thermal_monitor import (
    check_thermal_throttling_local,
    measure_thermal_metrics,
    ThermalStatus,
    _read_local_thermal_zone,
    _get_local_thermal_info
)

class TestReadLocalThermalZone:
    def test_read_valid_temperature(self):
        """Test reading a valid temperature from thermal zone."""
        with patch('builtins.open', mock_open(read_data='85000')):
            temp = _read_local_thermal_zone('/sys/class/thermal/thermal_zone0/temp')
            assert temp == 85000

    def test_read_invalid_temperature(self):
        """Test reading invalid temperature returns None."""
        with patch('builtins.open', mock_open(read_data='invalid')):
            temp = _read_local_thermal_zone('/sys/class/thermal/thermal_zone0/temp')
            assert temp is None

    def test_read_permission_error(self):
        """Test handling permission error."""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            temp = _read_local_thermal_zone('/sys/class/thermal/thermal_zone0/temp')
            assert temp is None

    def test_read_io_error(self):
        """Test handling IO error."""
        with patch('builtins.open', side_effect=IOError("IO Error")):
            temp = _read_local_thermal_zone('/sys/class/thermal/thermal_zone0/temp')
            assert temp is None

class TestGetLocalThermalInfo:
    @patch('os.path.exists', return_value=True)
    @patch('glob.glob', return_value=['/sys/class/thermal/thermal_zone0/temp'])
    @patch('builtins.open', mock_open(read_data='85000'))
    def test_normal_temperature(self, mock_glob, mock_exists):
        """Test with normal temperature."""
        result = _get_local_thermal_info()
        assert result['status'] == 'normal'
        assert result['throttling_detected'] is False
        assert result['temp_millidegrees'] == 85000

    @patch('os.path.exists', return_value=True)
    @patch('glob.glob', return_value=['/sys/class/thermal/thermal_zone0/temp'])
    @patch('builtins.open', mock_open(read_data='90000'))
    def test_throttled_temperature(self, mock_glob, mock_exists):
        """Test with throttled temperature."""
        result = _get_local_thermal_info()
        assert result['status'] == 'throttled'
        assert result['throttling_detected'] is True
        assert result['temp_millidegrees'] == 90000

    @patch('os.path.exists', return_value=True)
    @patch('glob.glob', return_value=[])
    def test_no_thermal_zones(self, mock_glob, mock_exists):
        """Test when no thermal zones are found."""
        result = _get_local_thermal_info()
        assert result['status'] == 'unknown'
        assert result['message'] == 'thermal_sensor_missing'
        assert result['temp_millidegrees'] is None

    @patch('os.path.exists', return_value=True)
    @patch('glob.glob', return_value=['/sys/class/thermal/thermal_zone0/temp'])
    @patch('builtins.open', side_effect=IOError("Cannot read"))
    def test_unreadable_zone(self, mock_glob, mock_exists):
        """Test when thermal zone cannot be read."""
        result = _get_local_thermal_info()
        assert result['status'] == 'unknown'
        assert result['message'] == 'thermal_sensor_missing'
        assert result['temp_millidegrees'] is None

    @patch('os.path.exists', return_value=True)
    @patch('glob.glob', return_value=['/sys/class/thermal/thermal_zone0/temp', '/sys/class/thermal/thermal_zone1/temp'])
    @patch('builtins.open')
    def test_multiple_zones_max_temp(self, mock_open_func, mock_glob, mock_exists):
        """Test with multiple zones, should return max temperature."""
        mock_open_func.side_effect = [
            mock_open(read_data='80000').return_value,  # Zone 0
            mock_open(read_data='95000').return_value   # Zone 1
        ]
        result = _get_local_thermal_info()
        assert result['temp_millidegrees'] == 95000
        assert result['status'] == 'throttled'

class TestCheckThermalThrottlingLocal:
    @patch('orchestrator.thermal_monitor._get_local_thermal_info')
    def test_returns_thermal_status(self, mock_get_info):
        """Test that check_thermal_throttling_local returns correct ThermalStatus."""
        mock_get_info.return_value = {
            'temp_millidegrees': 85000,
            'sensor_path': '/sys/class/thermal/thermal_zone0/temp',
            'status': 'normal',
            'message': None,
            'throttling_detected': False
        }
        
        result = check_thermal_throttling_local()
        
        assert isinstance(result, ThermalStatus)
        assert result.thermal_status == 'normal'
        assert result.thermal_throttling_detected is False
        assert result.current_temp_millidegrees == 85000

    @patch('orchestrator.thermal_monitor._get_local_thermal_info')
    def test_returns_throttled_status(self, mock_get_info):
        """Test with throttled temperature."""
        mock_get_info.return_value = {
            'temp_millidegrees': 95000,
            'sensor_path': '/sys/class/thermal/thermal_zone0/temp',
            'status': 'throttled',
            'message': None,
            'throttling_detected': True
        }
        
        result = check_thermal_throttling_local()
        
        assert result.thermal_status == 'throttled'
        assert result.thermal_throttling_detected is True

    @patch('orchestrator.thermal_monitor._get_local_thermal_info')
    def test_returns_unknown_status(self, mock_get_info):
        """Test with missing sensors."""
        mock_get_info.return_value = {
            'temp_millidegrees': None,
            'sensor_path': None,
            'status': 'unknown',
            'message': 'thermal_sensor_missing',
            'throttling_detected': False
        }
        
        result = check_thermal_throttling_local()
        
        assert result.thermal_status == 'unknown'
        assert result.thermal_throttling_detected is False
        assert result.message == 'thermal_sensor_missing'

class TestMeasureThermalMetrics:
    @patch('orchestrator.thermal_monitor.check_thermal_throttling_local')
    def test_local_measurement(self, mock_check):
        """Test local thermal measurement."""
        mock_check.return_value = ThermalStatus(
            thermal_throttling_detected=False,
            thermal_status='normal',
            current_temp_millidegrees=80000,
            sensor_path='/sys/class/thermal/thermal_zone0/temp',
            message=None
        )
        
        result = measure_thermal_metrics('localhost')
        
        assert result['node_ip'] == 'localhost'
        assert result['thermal_throttling_detected'] is False
        assert result['thermal_status'] == 'normal'
        assert result['current_temp_millidegrees'] == 80000

    @patch('orchestrator.thermal_monitor.check_thermal_throttling_remote')
    def test_remote_measurement(self, mock_check):
        """Test remote thermal measurement."""
        mock_ssh = MagicMock()
        mock_check.return_value = ThermalStatus(
            thermal_throttling_detected=True,
            thermal_status='throttled',
            current_temp_millidegrees=95000,
            sensor_path='/sys/class/thermal/thermal_zone0/temp',
            message=None
        )
        
        result = measure_thermal_metrics('192.168.1.100', mock_ssh)
        
        assert result['node_ip'] == '192.168.1.100'
        assert result['thermal_throttling_detected'] is True
        assert result['thermal_status'] == 'throttled'
        assert result['current_temp_millidegrees'] == 95000

if __name__ == "__main__":
    pytest.main([__file__, "-v"])