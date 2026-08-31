# The Influence of Chatbot Politeness on User-Perceived Quality

## Environment Configuration

This project requires an environment variable `HF_TOKEN` to access Hugging Face datasets.

### Local Development

1. Copy the template:
 ```bash
 cp.env.example.env
 ```
2. Edit `.env` and add your Hugging Face token:
 ```
 HF_TOKEN=your_actual_token_here
 ```
3. The `.env` file is listed in `.gitignore` and will not be committed.

### CI/CD (GitHub Actions)

Do **not** store secrets in the repository. Instead, inject the token via GitHub Actions environment variables:
1. Go to **Settings** > **Secrets and variables** > **Actions**.
2. Create a new secret named `HF_TOKEN`.
3. Reference it in the workflow file using `${{ secrets.HF_TOKEN }}`.

This ensures reproducibility on fresh runners while keeping secrets secure.
