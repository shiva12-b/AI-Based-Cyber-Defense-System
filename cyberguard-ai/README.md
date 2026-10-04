# CyberGuard AI — GenAI Employee & Banking Transaction Protection

A demo-only synthetic banking environment protected by a live CyberGuard security layer. The project is designed around a credential-compromise scenario: an employee session may be valid while the surrounding device, session, behavioural and transaction evidence becomes abnormal. CyberGuard collects the evidence, scores risk, invokes a GenAI analyst when warranted, and allows, isolates, or blocks the operation before the synthetic bank commits the transaction.

## Important design rule
There are no preloaded threat incidents, fake SOC counters, or hard-coded incident reports. Accounts and demo balances are created by the user. Normal transactions change the synthetic bank database. Controlled attack scenarios generate real telemetry and then submit a real synthetic transaction request; the resulting evidence drives the investigation report.

The project never creates real malware, steals credentials, attacks third-party systems, or uses real money.

## Architecture

Phone/Browser → CyberGuard Gateway :8000 → Synthetic Bank Server :9000 → Synthetic Bank DB

The controlled Attack Lab generates security telemetry inside this environment. The bank server accepts application traffic only when it carries the CyberGuard shared secret.

## Windows setup

Use Python 3.13.x (64-bit).

```bat
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
```

Then either run:

```bat
run_demo.bat
```

or manually:

```bat
uvicorn bank_server.main:app --host 0.0.0.0 --port 9000
uvicorn gateway.main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000`.

## Demo flow

1. Open **Accounts** and create two or more synthetic accounts with demo balances.
2. Open **Bank** and log in using one account and a device ID such as `BANK-PC-001`.
3. Perform a normal transfer. The source and destination balances actually change.
4. Open **Attack Lab** and run a controlled credential-compromise/account-takeover/transaction-fraud/session-anomaly scenario using the active session ID.
5. CyberGuard creates actual events, calculates risk, invokes GenAI when configured, creates an incident report, and blocks or isolates the transaction.
6. Open **Incidents** to inspect the evidence, AI interpretation and audit timeline.
7. Confirm the bank balance did not change for a blocked/isolated transfer.

## GenAI

Set `GENAI_API_KEY` in `.env` to enable the configured Gemini-compatible analyst. The application sends only structured observed evidence. If the key is missing or the model call fails, the deterministic evidence-backed fallback analyst is used and the fallback is recorded; the application does not invent missing evidence.

## Deployment

All service URLs and secrets are environment variables. For a deployed demo, expose the gateway/bank application through HTTPS and configure `BANK_SERVER_URL`, `CORS_ORIGINS`, database settings and GenAI credentials in the deployment environment. Do not commit `.env` or API keys.

## Tests

```bat
pytest -q
```
