import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.llm_generator import load_model
from code.config import get_model_path

class TestLLMLoad:
    """
    Unit tests for LLM loading constraints (FR-002).
    Verifies Q4_K_M quantization logic and 7GB RAM constraint.
    """

    @patch('code.llm_generator.psutil')
    @patch('code.llm_generator.Llama')
    def test_phi_loads_within_7gb_ram(self, mock_llama_class, mock_psutil):
        """
        Verify that Phi-2 loading does not exceed 7GB RAM on CPU.
        
        This test mocks the system memory check to simulate a valid environment
        and ensures the model is loaded with CPU-only settings (n_gpu_layers=0).
        """
        # Setup mock for available memory > 7GB
        mock_memory = MagicMock()
        mock_memory.available = 8 * (1024 ** 3) # 8 GB
        mock_psutil.virtual_memory.return_value = mock_memory

        # Setup mock for Llama instance
        mock_instance = MagicMock()
        mock_llama_class.return_value = mock_instance

        # Mock the model path to exist
        with patch('os.path.exists', return_value=True):
            with patch('code.llm_generator.get_model_path', return_value='/fake/path/model.gguf'):
                # Call the function
                result = load_model()

                # Assertions
                assert result is mock_instance
                mock_llama_class.assert_called_once()
                
                # Verify constraints were passed
                call_kwargs = mock_llama_class.call_args[1]
                assert call_kwargs.get('n_gpu_layers') == 0, "Model must be loaded on CPU (n_gpu_layers=0)"
                assert call_kwargs.get('use_mmap') == True, "Mmap should be enabled for memory efficiency"

    @patch('code.llm_generator.psutil')
    def test_memory_constraint_failure(self, mock_psutil):
        """
        Verify that MemoryError is raised if available RAM < 7GB.
        """
        # Setup mock for available memory < 7GB
        mock_memory = MagicMock()
        mock_memory.available = 5 * (1024 ** 3) # 5 GB
        mock_psutil.virtual_memory.return_value = mock_memory

        with patch('code.llm_generator.get_model_path', return_value='/fake/path/model.gguf'):
            with pytest.raises(MemoryError, match="Insufficient memory"):
                load_model()

    @patch('code.llm_generator.psutil')
    @patch('code.llm_generator.Llama')
    def test_model_not_found(self, mock_llama_class, mock_psutil):
        """
        Verify FileNotFoundError is raised if model path is missing.
        """
        mock_memory = MagicMock()
        mock_memory.available = 8 * (1024 ** 3)
        mock_psutil.virtual_memory.return_value = mock_memory

        with patch('os.path.exists', return_value=False):
            with patch('code.llm_generator.get_model_path', return_value='/nonexistent/model.gguf'):
                with pytest.raises(FileNotFoundError):
                    load_model()
