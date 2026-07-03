# API Keys Setup Guide

This project requires API keys to access external materials science databases.
Follow the steps below to configure your environment.

## 1. Get API Keys

### Materials Project
1. Register at https://materialsproject.org/dashboard
2. Navigate to your account settings to generate an API key.
3. Copy the key.

### OpenKIM (Optional)
1. Visit https://openkim.org/
2. Register if required for your intended usage.
3. Generate or retrieve your API key.

## 2. Configure Environment Variables

1. Copy the template file to your local environment:
 ```bash
 cp.env.example.env
 ```
 *(Note: If.env.example doesn't exist, create a new file named `.env` based on the template in the repository root.)*

2. Open `.env` in a text editor and replace the placeholder values with your actual keys:
 ```
 MP_API_KEY=your_actual_materials_project_key
 OPENKIM_API_KEY=your_actual_openkim_key
 ```

## 3. Verify Configuration

The Python scripts in `code/` will automatically load these variables using the `python-dotenv` package.
To verify they are loaded correctly, run a test script or check the logs during the data download phase (`code/download.py`).

## Security Note
- **Never** commit the `.env` file to version control.
- The `.gitignore` file is configured to ignore `.env` automatically.
- If you accidentally commit it, remove it from the git history immediately and rotate your API keys.
