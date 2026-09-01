import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass

class Configuration:
    """Configuration class for the application."""
    
    def __init__(self):
        load_dotenv()
        
        # Project settings
        self.project_root = Path(os.getenv("PROJECT_ROOT", "."))
        self.log_file = self.project_root / "logs" / "app.log"
        self.log_level = self._get_log_level()
        self.json_log_format = os.getenv("JSON_LOG_FORMAT", "true").lower() == "true"
        
        # Data paths
        self.data_raw_dir = self.project_root / "data" / "raw"
        self.data_processed_dir = self.project_root / "data" / "processed"
        self.data_reports_dir = self.project_root / "data" / "reports"
        
        # API settings
        self.gdelt_api_base = os.getenv("GDELT_API_BASE", "https://api.gdeltproject.org/api/v2")
        self.google_trends_api = os.getenv("GOOGLE_TRENDS_API", "https://trends.google.com/trends/api")
        
        # Validation
        self._validate()
    
    def _get_log_level(self) -> int:
        """Get the log level from environment variables."""
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return level_map.get(level_str, logging.INFO)
    
    def _validate(self) -> None:
        """Validate the configuration."""
        if not self.project_root.exists():
            raise ConfigError(f"Project root does not exist: {self.project_root}")
        
        # Ensure required directories exist
        for dir_path in [self.data_raw_dir, self.data_processed_dir, self.data_reports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

def main():
    """Main entry point for configuration validation."""
    try:
        config = Configuration()
        print("Configuration loaded successfully")
        print(f"Project root: {config.project_root}")
        print(f"Log file: {config.log_file}")
        print(f"Log level: {logging.getLevelName(config.log_level)}")
    except ConfigError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()