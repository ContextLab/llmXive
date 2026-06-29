"""
Logging infrastructure for the mindfulness-DMN research pipeline.

Provides JSON-formatted logging and QC report template generation.
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Default log configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_DIR = "data/logs"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# JSON log formatter
class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)

def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_dir: str = DEFAULT_LOG_DIR,
    json_format: bool = True,
    console_output: bool = True,
    file_output: bool = True,
) -> logging.Logger:
    """
    Configure logging infrastructure with JSON format and file output.

    Args:
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_dir: Directory to store log files
        json_format: Whether to use JSON formatting
        console_output: Whether to output to console
        file_output: Whether to output to file

    Returns:
        Root logger with configured handlers
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatter based on format preference
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler with rotation
    if file_output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"pipeline_{timestamp}.log"

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Also create a JSON-specific log file
        json_log_file = log_path / f"pipeline_{timestamp}_json.log"
        json_handler = logging.handlers.RotatingFileHandler(
            json_log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
        )
        json_handler.setLevel(log_level)
        json_handler.setFormatter(JsonFormatter())
        logger.addHandler(json_handler)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger with the configured handlers.

    Args:
        name: Logger name (e.g., 'preprocessing', 'analysis')

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

class QCReportGenerator:
    """
    Generator for QC reports with motion summary, SNR, and temporal SNR metrics.

    Uses HTML template to create structured QC reports.
    """

    def __init__(self, template_path: Optional[str] = None):
        """
        Initialize QC report generator.

        Args:
            template_path: Path to HTML template file. If None, uses embedded template.
        """
        if template_path is None:
            template_path = Path(__file__).parent / "qc_report_template.html"
        self.template_path = Path(template_path)
        self.template: Optional[str] = None
        self._load_template()

    def _load_template(self) -> None:
        """Load HTML template from file."""
        if self.template_path.exists():
            with open(self.template_path, "r", encoding="utf-8") as f:
                self.template = f.read()
        else:
            # Fallback to embedded template
            self.template = self._get_default_template()

    def _get_default_template(self) -> str:
        """Return default HTML template if file not found."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QC Report - Mindfulness-DMN Pipeline</title>
    <style>
  body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
  h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
  h2 { color: #555; margin-top: 30px; }
  .metric-card { background: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 10px 0; }
  .metric-value { font-size: 24px; font-weight: bold; color: #007bff; }
  .metric-label { color: #666; font-size: 14px; }
  table { width: 100%; border-collapse: collapse; margin: 20px 0; }
  th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
  th { background-color: #007bff; color: white; }
  tr:nth-child(even) { background-color: #f2f2f2; }
  .pass { color: #28a745; font-weight: bold; }
  .fail { color: #dc3545; font-weight: bold; }
  .warning { color: #ffc107; font-weight: bold; }
  .timestamp { color: #888; font-size: 12px; }
    </style>
</head>
<body>
    <h1>Quality Control Report</h1>
    <p class="timestamp">Generated: {{ timestamp }}</p>

    <h2>Dataset Information</h2>
    <div class="metric-card">
  <div class="metric-label">Dataset ID</div>
  <div class="metric-value">{{ dataset_id }}</div>
    </div>
    <div class="metric-card">
  <div class="metric-label">Subjects Processed</div>
  <div class="metric-value">{{ subjects_count }}</div>
    </div>

    <h2>Motion Summary</h2>
    <table>
  <thead>
      <tr>
          <th>Subject ID</th>
          <th>Mean Translation (mm)</th>
          <th>Max Translation (mm)</th>
          <th>Mean Rotation (deg)</th>
          <th>Max Rotation (deg)</th>
          <th>Status</th>
      </tr>
  </thead>
  <tbody>
      {{ motion_rows }}
  </tbody>
    </table>

    <h2>Signal-to-Noise Ratio (SNR)</h2>
    <table>
  <thead>
      <tr>
          <th>Subject ID</th>
          <th>Global SNR</th>
          <th>GM SNR</th>
          <th>WM SNR</th>
          <th>CSF SNR</th>
          <th>Status</th>
      </tr>
  </thead>
  <tbody>
      {{ snr_rows }}
  </tbody>
    </table>

    <h2>Temporal SNR (tSNR)</h2>
    <table>
  <thead>
      <tr>
          <th>Subject ID</th>
          <th>Global tSNR</th>
          <th>DMN tSNR</th>
          <th>Frontal tSNR</th>
          <th>Parietal tSNR</th>
          <th>Status</th>
      </tr>
  </thead>
  <tbody>
      {{ tsnr_rows }}
  </tbody>
    </table>

    <h2>Summary Statistics</h2>
    <div class="metric-card">
  <div class="metric-label">Subjects Passed Motion Threshold</div>
  <div class="metric-value">{{ motion_pass_count }} / {{ subjects_count }}</div>
    </div>
    <div class="metric-card">
  <div class="metric-label">Mean Global SNR</div>
  <div class="metric-value">{{ mean_global_snr }}</div>
    </div>
    <div class="metric-card">
  <div class="metric-label">Mean Global tSNR</div>
  <div class="metric-value">{{ mean_global_tsnr }}</div>
    </div>
</body>
</html>"""

    def generate_report(
        self,
        dataset_id: str,
        subjects_count: int,
        motion_data: list[dict],
        snr_data: list[dict],
        tsnr_data: list[dict],
        output_path: str,
    ) -> str:
        """
        Generate QC report HTML file.

        Args:
            dataset_id: Dataset identifier
            subjects_count: Number of subjects processed
            motion_data: List of motion metrics per subject
            snr_data: List of SNR metrics per subject
            tsnr_data: List of tSNR metrics per subject
            output_path: Path to write HTML report

        Returns:
            Path to generated report
        """
        if self.template is None:
            raise ValueError("Template not loaded")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generate motion rows
        motion_rows = ""
        motion_pass_count = 0
        for sub in motion_data:
            status = "PASS" if sub.get("passed", False) else "FAIL"
            status_class = "pass" if status == "PASS" else "fail"
            if sub.get("passed", False):
                motion_pass_count += 1
            motion_rows += f"""
      <tr>
          <td>{sub.get('subject_id', 'N/A')}</td>
          <td>{sub.get('mean_translation_mm', 0):.3f}</td>
          <td>{sub.get('max_translation_mm', 0):.3f}</td>
          <td>{sub.get('mean_rotation_deg', 0):.3f}</td>
          <td>{sub.get('max_rotation_deg', 0):.3f}</td>
          <td class="{status_class}">{status}</td>
      </tr>"""

        # Generate SNR rows
        snr_rows = ""
        global_snrs = []
        for sub in snr_data:
            status = "PASS" if sub.get("passed", False) else "FAIL"
            status_class = "pass" if status == "PASS" else "fail"
            global_snrs.append(sub.get("global_snr", 0))
            snr_rows += f"""
      <tr>
          <td>{sub.get('subject_id', 'N/A')}</td>
          <td>{sub.get('global_snr', 0):.2f}</td>
          <td>{sub.get('gm_snr', 0):.2f}</td>
          <td>{sub.get('wm_snr', 0):.2f}</td>
          <td>{sub.get('csf_snr', 0):.2f}</td>
          <td class="{status_class}">{status}</td>
      </tr>"""

        # Generate tSNR rows
        tsnr_rows = ""
        global_tsns = []
        for sub in tsnr_data:
            status = "PASS" if sub.get("passed", False) else "FAIL"
            status_class = "pass" if status == "PASS" else "fail"
            global_tsns.append(sub.get("global_tsnr", 0))
            tsnr_rows += f"""
      <tr>
          <td>{sub.get('subject_id', 'N/A')}</td>
          <td>{sub.get('global_tsnr', 0):.2f}</td>
          <td>{sub.get('dmn_tsnr', 0):.2f}</td>
          <td>{sub.get('frontal_tsnr', 0):.2f}</td>
          <td>{sub.get('parietal_tsnr', 0):.2f}</td>
          <td class="{status_class}">{status}</td>
      </tr>"""

        # Calculate summary statistics
        mean_global_snr = sum(global_snrs) / len(global_snrs) if global_snrs else 0
        mean_global_tsnr = sum(global_tsns) / len(global_tsns) if global_tsns else 0

        # Replace template placeholders
        report_html = self.template.replace("{{ timestamp }}", timestamp)
        report_html = report_html.replace("{{ dataset_id }}", dataset_id)
        report_html = report_html.replace("{{ subjects_count }}", str(subjects_count))
        report_html = report_html.replace("{{ motion_rows }}", motion_rows.strip())
        report_html = report_html.replace("{{ snr_rows }}", snr_rows.strip())
        report_html = report_html.replace("{{ tsnr_rows }}", tsnr_rows.strip())
        report_html = report_html.replace("{{ motion_pass_count }}", str(motion_pass_count))
        report_html = report_html.replace("{{ mean_global_snr }}", f"{mean_global_snr:.2f}")
        report_html = report_html.replace("{{ mean_global_tsnr }}", f"{mean_global_tsnr:.2f}")

        # Write report to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_html)

        return str(output_path)

# Convenience function for quick logging setup
def quick_setup(log_dir: str = DEFAULT_LOG_DIR) -> logging.Logger:
    """
    Quick setup with default configuration.

    Args:
        log_dir: Directory for log files

    Returns:
        Configured root logger
    """
    return setup_logging(log_dir=log_dir, json_format=True)