"""
Task T011d: Local Pilot Deployment
Configures and deploys the Streamlit app to a local/private URL for the pilot cohort.
Generates a deployment info file with the access link and configuration details.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

# Ensure we can import from the project root if running as a script
# In a real environment, the project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PROJECT_ROOT as CONFIG_PROJECT_ROOT, DATA_DIR

def ensure_streamlit_config(config_dir: Path) -> None:
    """Create .streamlit/config.toml if it doesn't exist with local server settings."""
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.toml"
    
    if not config_file.exists():
        config_content = """
        [server]
        headless = true
        address = "127.0.0.1"
        port = 8501
        enableCORS = false
        enableXsrfProtection = false
        maxUploadSize = 10
        
        [browser]
        gatherUsageStats = false
        """
        with open(config_file, 'w') as f:
            f.write(config_content.strip())
        print(f"Created Streamlit config at: {config_file}")
    else:
        print(f"Streamlit config already exists at: {config_file}")

def build_deployment_info(app_script: Path, port: int, cohort_size: int) -> Dict:
    """Build deployment information dictionary."""
    return {
        "deployment_id": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
        "app_script": str(app_script.relative_to(PROJECT_ROOT)),
        "access_url": f"http://127.0.0.1:{port}",
        "port": port,
        "cohort_size": cohort_size,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "ready",
        "instructions": (
            f"1. Ensure the pilot interface is ready at: {app_script}\n"
            f"2. Run: streamlit run {app_script}\n"
            f"3. Participants access: http://127.0.0.1:{port}\n"
            f"4. Expected cohort size: {cohort_size} participants\n"
            f"5. Data will be saved to: {DATA_DIR}/measurements/"
        )
    }

def write_deployment_info(info: Dict, output_path: Path) -> None:
    """Write deployment information to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(info, f, indent=2)
    print(f"Deployment info written to: {output_path}")

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Deploy Streamlit pilot interface for local cohort study"
    )
    parser.add_argument(
        "--app-script",
        type=Path,
        default="code/src/experiment/pilot_interface.py",
        help="Path to the Streamlit app script"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port for local Streamlit server"
    )
    parser.add_argument(
        "--cohort-size",
        type=int,
        default=20,
        help="Expected number of pilot participants"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/derived/deployment_info.json"),
        help="Output path for deployment info JSON"
    )
    parser.add_argument(
        "--start-server",
        action="store_true",
        help="Start the Streamlit server after generating deployment info"
    )
    parser.add_argument(
        "--background",
        action="store_true",
        help="Start the server in background mode (nohup-like behavior)"
    )
    return parser.parse_args()

def start_streamlit_server(app_script: Path, port: int, background: bool = False) -> Optional[subprocess.Popen]:
    """Start the Streamlit server."""
    if not app_script.exists():
        raise FileNotFoundError(f"App script not found: {app_script}")
    
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_script),
        "--server.address", "127.0.0.1",
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    if background:
        # Start in background (on Unix-like systems)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        print(f"Streamlit server started in background (PID: {process.pid})")
        return process
    else:
        # Start in foreground (blocking)
        print(f"Starting Streamlit server on http://127.0.0.1:{port}...")
        print("Press Ctrl+C to stop the server.")
        subprocess.run(cmd)
        return None

def main() -> int:
    """Main entry point for deployment task."""
    args = parse_arguments()
    
    # Resolve paths relative to project root
    app_script = args.app_script
    if not app_script.is_absolute():
        app_script = PROJECT_ROOT / app_script
    
    output_path = args.output
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    
    # Ensure Streamlit config exists
    streamlit_config_dir = PROJECT_ROOT / "code" / ".streamlit"
    ensure_streamlit_config(streamlit_config_dir)
    
    # Verify the app script exists
    if not app_script.exists():
        print(f"ERROR: App script not found at {app_script}")
        print("Please ensure the pilot interface is implemented first.")
        return 1
    
    # Build and save deployment info
    deployment_info = build_deployment_info(app_script, args.port, args.cohort_size)
    write_deployment_info(deployment_info, output_path)
    
    print("\n" + "="*60)
    print("DEPLOYMENT READY")
    print("="*60)
    print(f"Access URL: {deployment_info['access_url']}")
    print(f"Cohort Size: {deployment_info['cohort_size']}")
    print(f"App Script: {app_script}")
    print(f"Deployment Info: {output_path}")
    print("\nInstructions:")
    print(deployment_info["instructions"])
    print("="*60)
    
    # Optionally start the server
    if args.start_server:
        try:
            if args.background:
                start_streamlit_server(app_script, args.port, background=True)
                print("Server started in background. Deployment info saved.")
            else:
                start_streamlit_server(app_script, args.port, background=False)
                print("Server stopped.")
        except KeyboardInterrupt:
            print("\nServer stopped by user.")
            return 0
        except Exception as e:
            print(f"ERROR: Failed to start server: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
