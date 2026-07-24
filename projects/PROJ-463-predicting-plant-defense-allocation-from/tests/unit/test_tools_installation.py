import pytest
import subprocess
import sys
from pathlib import Path
from scripts.verify_tools import check_tool

class TestToolInstallation:
    """
    Tests to verify that HISAT2, fastp, and featureCounts are installed 
    and accessible in the system PATH.
    
    These tests assume the installation script (install_tools.sh) has been run
    successfully prior to execution in the CI/CD or local environment.
    """

    @pytest.mark.parametrize("tool_name", ["fastp", "hisat2", "featureCounts"])
    def test_tool_exists_in_path(self, tool_name):
        """
        Verify that each required tool is found in the system PATH.
        """
        installed, output = check_tool(tool_name)
        assert installed, f"Tool '{tool_name}' is not installed or not in PATH. Output: {output}"

    @pytest.mark.parametrize("tool_name", ["fastp", "hisat2", "featureCounts"])
    def test_tool_returns_version(self, tool_name):
        """
        Verify that each tool responds to a version flag, ensuring it is executable.
        """
        installed, output = check_tool(tool_name)
        assert installed, f"Tool '{tool_name}' did not return a version string."
        assert len(output) > 0, f"Tool '{tool_name}' returned an empty version string."
        # Basic sanity check: version strings usually contain numbers or the tool name
        assert any(char.isdigit() for char in output) or tool_name.lower() in output.lower(), \
            f"Tool '{tool_name}' returned unexpected output: {output}"

    def test_fastp_basic_help(self):
        """
        Quick sanity check that fastp can run with --help.
        """
        result = subprocess.run(
            ["fastp", "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, "fastp --help failed"
        assert "fastp" in result.stdout.lower() or "fastp" in result.stderr.lower()

    def test_hisat2_basic_help(self):
        """
        Quick sanity check that hisat2 can run with --help.
        """
        result = subprocess.run(
            ["hisat2", "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, "hisat2 --help failed"
        # HISAT2 often prints help to stderr
        assert "hisat2" in result.stdout.lower() or "hisat2" in result.stderr.lower()

    def test_featurecounts_basic_help(self):
        """
        Quick sanity check that featureCounts can run with -h.
        """
        result = subprocess.run(
            ["featureCounts", "-h"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, "featureCounts -h failed"
        assert "featurecounts" in result.stdout.lower() or "featurecounts" in result.stderr.lower()
