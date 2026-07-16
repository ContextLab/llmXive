# Security Policy

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** create a public GitHub issue
2. Email the maintainers directly at [security@example.com]
3. Include details about the vulnerability and potential impact
4. Allow time for a fix before public disclosure

## API Key Security

### Do NOT commit API keys
- Store API keys in `.env` file (not committed)
- Use environment variables for sensitive data
- Rotate keys if accidentally exposed

### Environment Variables
Required environment variables:
- `MP_API_KEY`: Materials Project API key
- `OPENKIM_API_KEY`: OpenKIM API key

## Data Privacy

- Raw data from external APIs is stored locally
- No personal data is collected or transmitted
- All data usage complies with source terms of service

## Dependencies

- Regularly update dependencies to patch security vulnerabilities
- Use `pip-audit` or similar tools to check for known vulnerabilities
- Review security advisories for third-party packages

## Best Practices

1. Keep `.env` file out of version control
2. Use strong, unique API keys
3. Limit API key permissions to minimum required
4. Monitor API usage for unusual activity
5. Rotate keys periodically
