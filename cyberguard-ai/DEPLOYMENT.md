# Deployment Notes

Recommended shape: one web service running `python start.py`.

- Public CyberGuard gateway listens on the platform-provided `PORT`.
- Synthetic bank server listens only on `127.0.0.1:9000`.
- `BANK_SERVER_URL` is set automatically unless overridden.
- Set `GENAI_API_KEY`, `GENAI_MODEL`, `GENAI_BASE_URL`, `PROTECTED_SHARED_SECRET`, and `CORS_ORIGINS` in deployment settings.
- SQLite persistence requires a persistent disk/volume on platforms with ephemeral filesystems, or a database-layer migration before production use.
- This is a synthetic banking/security demonstration, not a real banking system.
