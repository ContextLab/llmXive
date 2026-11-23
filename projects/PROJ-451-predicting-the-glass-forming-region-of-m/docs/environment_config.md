# Environment Configuration Guide

This project uses environment variables and a `.env` file to manage sensitive configuration, such as API keys, and optional paths.

## Setup

1. **Copy the example file**:
 ```bash
 cp.env.example.env
 ```

2. **Configure API Keys**:
 Open `.env` in a text editor and replace `your_api_key_here` with your actual **Materials Project API Key**.
 ```env
 MATERIALS_PROJECT_API_KEY=your_actual_api_key
 ```
 You can obtain a key by registering at [Materials Project](https://next-gen.materialsproject.org/).

3. **Optional: Custom Dataset Path**:
 If you wish to load data from a specific location instead of the default `data/` directories, set the `CUSTOM_DATASET_PATH` variable in `.env`:
 ```env
 CUSTOM_DATASET_PATH=/absolute/path/to/your/data.csv
 ```

## Usage in Code

The configuration is managed centrally in `code/config.py`.

* **Initialize**: Call `init_environment()` at the very start of your script (e.g., in `main.py` or `code/main.py`) to load the `.env` file.
 ```python
 from config import init_environment
 init_environment()
 ```

* **Get API Key**:
 ```python
 from config import get_materials_project_api_key
 api_key = get_materials_project_api_key()
 ```

* **Get Data Paths**:
 ```python
 from config import get_data_path, get_raw_data_path, get_processed_data_path
 data_dir = get_data_path()
 raw_dir = get_raw_data_path()
 ```

* **Ensure Directories**:
 The function `ensure_data_directories()` creates the necessary folder structure (`data/raw`, `data/processed`, `data/results`) if they don't exist.
 ```python
 from config import ensure_data_directories
 ensure_data_directories()
 ```

## Security Note

* **Never commit `.env` to version control**. The file is listed in `.gitignore` (or should be) to prevent accidental exposure of API keys.
* Always use `.env.example` to document required variables without exposing secrets.
