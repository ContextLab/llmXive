# QIIME 2 Installation Guide

## Important Notice
Per Constitution Principle I, **QIIME 2 must NOT be installed via pip**.
It must be installed using Conda or Docker.

## Option 1: Conda (Recommended for Local Development)

1. **Install Miniconda** (if not already installed):
 - Download from: https://docs.conda.io/en/latest/miniconda.html
 - Follow installation instructions for your OS.

2. **Run the setup script**:
 ```bash
 cd code
 chmod +x setup_qiime2_conda.sh
./setup_qiime2_conda.sh
 ```

3. **Activate the environment**:
 ```bash
 conda activate qiime2-2023.9
 ```

4. **Install additional Python dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

5. **Verify installation**:
 ```bash
 qiime --version
 ```

## Option 2: Docker (Recommended for Reproducibility)

1. **Install Docker**:
 - Download from: https://www.docker.com/get-started

2. **Pull the QIIME 2 Docker image**:
 ```bash
 docker pull quay.io/qiime2/q2-2023.9
 ```

3. **Run a QIIME 2 command via Docker**:
 ```bash
 docker run -it --rm -v $(pwd):/data quay.io/qiime2/q2-2023.9 \
 qiime --version
 ```

## Troubleshooting

- **"conda: command not found"**: Ensure Miniconda is installed and added to your PATH.
- **Environment conflicts**: Create a fresh conda environment before installing QIIME 2.
- **Network issues**: Ensure you have a stable internet connection for downloading packages.

## Reference
- QIIME 2 Documentation: https://docs.qiime2.org/
- QIIME 2 Installation Guide: 