# 🔬 QualityForge — UC-07 Auto-Regression Triage Agent

> An intelligent AI agent that intercepts CI/CD failure events in real time, classifies the root cause automatically, and posts a structured triage report directly to the relevant Jira ticket — with zero manual intervention.

---

## 🧩 The Problem

After every CI/CD run, QA engineers must:
- Manually open failure logs
- Determine whether the failure is a real bug, a flaky test, or an environment issue
- Update the corresponding Jira ticket with findings

This is repetitive, slow, and inconsistent across team members. It consumes QA bandwidth that should be spent on prevention, not investigation.

---

## ✅ The Solution

The Auto-Regression Triage Agent automates the entire triage pipeline:

```
GitHub Actions Failure
        ↓
Webhook received by FastAPI agent
        ↓
Failure logs fetched from GitHub API
        ↓
Root cause classified by AI (Heuristic + LLM)
        ↓
Structured report posted to Jira ticket
```

---

## 🗂️ Project Structure

```
UC-07_Auto_Regression_Triage/
├── triage_agent/
│   ├── __init__.py          # Package entry point
│   ├── main.py              # FastAPI webhook server
│   ├── config.py            # Environment-based configuration
│   ├── models.py            # Pydantic data models
│   ├── github_client.py     # GitHub Actions API client
│   ├── classifier.py        # Two-stage failure classifier
│   ├── jira_client.py       # Jira REST API v3 client
│   └── reporter.py          # Structured report builder
├── tests/
│   ├── test_genuine_failure.py    # Simulates a real code defect
│   ├── test_flaky.py              # Simulates a timing/timeout failure
│   ├── test_environment.py        # Simulates a missing env variable
│   └── test_dependency.py         # Simulates a missing package
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI workflow
├── requirements.txt
├── requirements-test.txt
├── .env.example
└── README.md
```

---

## 🧠 How the Classifier Works

Classification runs in two stages:

### Stage 1 — Heuristic Signal Matcher *(always runs)*
Scores 16 weighted regex patterns against the raw failure log. Fast, deterministic, requires no API call. Returns a category and a confidence score (0–100%).

### Stage 2 — Anthropic Claude LLM *(fallback only)*
Triggered only when heuristic confidence falls below 70%. Sends the log excerpt to Claude for nuanced engineering reasoning. Returns a structured JSON response with category, confidence, and explanation.

### The 4 Classification Categories

| Category | Icon | What it means |
|---|---|---|
| `genuine_failure` | 🐛 | A real code defect exposed by the test |
| `flaky_test` | ⚡ | Intermittent failure from timing or race conditions |
| `environment_issue` | 🌐 | Infrastructure problem — OOM, disk, missing secrets |
| `dependency_failure` | 📦 | Broken package, version conflict, or service outage |

---

## 🗃️ What Each File Does

### `main.py` — The Webhook Server
The entry point of the agent. Built with FastAPI, it:
- Listens for `workflow_run` events from GitHub on `/webhook/github`
- Verifies the HMAC signature to ensure the request is genuinely from GitHub
- Extracts the Jira ticket ID from the commit message automatically
- Dispatches the triage pipeline as a background task so GitHub gets a response within 1 second
- Exposes a `/triage/manual` endpoint for testing without a real CI failure
- Exposes a `/health` endpoint for monitoring

### `config.py` — Configuration
Uses `pydantic-settings` to load all configuration from environment variables. Supports `.env` files for local development. Every setting has a sensible default so the agent works out of the box.

### `models.py` — Data Models
Pydantic v2 models for:
- `WebhookPayload` — the raw GitHub webhook JSON
- `TriageRequest` — the internal triage job (includes extracted Jira ticket ID)
- `ClassificationResult` — the output of the classifier (category, confidence, signals, reasoning)
- `TriageResult` — the full result passed to the report builder

### `github_client.py` — GitHub API Client
Fetches failure logs for a given workflow run:
1. Lists all jobs in the run
2. Filters to failed jobs only
3. Downloads logs for each failed job (GitHub redirects to a signed Azure Blob URL)
4. Falls back to the full run log ZIP archive if individual job logs are unavailable

### `classifier.py` — The AI Classifier
The core intelligence of the agent. Contains:
- `Signal` — a named regex pattern with a target category and weight
- `HeuristicClassifier` — scores all signals and returns the highest-scoring category
- `LLMClassifier` — sends the log to Anthropic Claude for a structured JSON classification
- `FailureClassifier` — orchestrates both stages and decides which result to use

### `jira_client.py` — Jira REST API Client
Posts comments to Jira tickets using the v3 REST API with Basic Auth (email + API token). Converts the plain-text report into Atlassian Document Format (ADF) so headings, bullet points, and code blocks render natively in Jira.

### `reporter.py` — Report Builder
Builds the structured Jira comment from a `TriageResult`. Includes:
- Classification category with confidence badge (🟢 High / 🟡 Medium / 🔴 Low)
- Failure context (workflow, branch, commit, run URL, timestamp)
- Matched signals that drove the classification
- Recommended actions tailored to each failure category
- Sanitised log excerpt (ANSI codes stripped)

---

## ⚙️ Test Files Explained

Each test file is designed to produce a specific failure category so you can demo and verify the classifier.

### `test_genuine_failure.py`
```python
def test_discount_calculation():
    result = calculate_discount(100, 10)
    assert result == 80  # wrong — correct answer is 90
```
Produces an `AssertionError` — classified as 🐛 Genuine Failure.

### `test_flaky.py`
```python
def test_api_response_time():
    time.sleep(6)
    assert elapsed < 5  # always times out
```
Produces a timeout — classified as ⚡ Flaky Test.

### `test_environment.py`
```python
def test_required_config_present():
    api_key = os.environ.get("MISSING_SECRET_KEY")
    assert api_key is not None  # env var is not set
```
Produces a missing environment variable error — classified as 🌐 Environment Issue.

### `test_dependency.py`
```python
import nonexistent_analytics_sdk  # package does not exist
```
Produces a `ModuleNotFoundError` — classified as 📦 Dependency Failure.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
copy .env.example .env
notepad .env
```
Fill in your GitHub token, Jira credentials, and webhook secret.

### 3. Run the agent
```bash
python -m uvicorn triage_agent.main:app --host 0.0.0.0 --port 8080
```

### 4. Expose to the internet (local development)
```bash
ngrok http 8080
```

### 5. Register the webhook in GitHub
Go to your repository → Settings → Webhooks → Add webhook:

| Field | Value |
|---|---|
| Payload URL | `https://your-ngrok-url.ngrok-free.app/webhook/github` |
| Content type | `application/json` |
| Secret | Your `GITHUB_WEBHOOK_SECRET` value |
| Events | Workflow runs |

### 6. Trigger a failure
Make a commit to your repo with a Jira ticket ID in the message:
```
fix: PROJ-123 correct login null check
```
When GitHub Actions fails, the agent automatically classifies and posts to PROJ-123.

### 7. Test manually (without a real failure)
Visit `http://localhost:8080/docs` and use the `POST /triage/manual` endpoint.

---

## 🔐 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GITHUB_TOKEN` | Yes | Personal Access Token with `repo` and `workflow` scopes |
| `GITHUB_WEBHOOK_SECRET` | Yes | Shared secret for HMAC signature verification |
| `JIRA_BASE_URL` | Yes | e.g. `https://yourcompany.atlassian.net` |
| `JIRA_EMAIL` | Yes | Email address of your Jira account |
| `JIRA_API_TOKEN` | Yes | Token from id.atlassian.com/manage-profile/security/api-tokens |
| `ANTHROPIC_API_KEY` | Optional | Required only if `USE_LLM_CLASSIFIER=true` |
| `USE_LLM_CLASSIFIER` | No | Set to `false` to use heuristics only (default: `true`) |
| `LLM_CONFIDENCE_THRESHOLD` | No | Confidence cutoff for LLM fallback (default: `0.70`) |
| `LOG_EXCERPT_MAX_CHARS` | No | Max log characters in Jira comment (default: `4000`) |
| `JIRA_COMMENT_TAG` | No | Comment prefix tag (default: `[AutoTriageAgent]`) |

---

## 🌐 API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/webhook/github` | GitHub Actions webhook receiver |
| `POST` | `/triage/manual` | Manually trigger triage for any run |
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |
| `GET` | `/docs` | Interactive OpenAPI documentation |

---

## 📋 Example Jira Comment Output

```
[AutoTriageAgent] 🤖 Auto-Regression Triage Report

Classification
  Category:   🐛 Genuine Failure (Code Bug)
  Confidence: 🟢 87% (High)
  Classifier: HEURISTIC

Failure Context
  Workflow:  CI / Run Tests
  Branch:    feature/login-fix
  Commit:    a3f9c2d — fix: PROJ-123 correct null check
  Run URL:   https://github.com/org/repo/actions/runs/12345678
  Detected:  2026-04-26 14:22 UTC

Matched Signals
  - Assertion Error
  - Null Pointer

Recommended Actions
  - Review the assertion/exception trace and identify the regression.
  - Check recent commits on this branch that touch the failing code path.
  - Assign the ticket to the owning team for a fix in the current sprint.
  - Block the PR/merge until the defect is resolved.

Log Excerpt
  AssertionError: expected 90 but got 80
    File tests/test_genuine_failure.py, line 8
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Core language |
| FastAPI | Webhook server and REST API |
| httpx | Async HTTP client |
| Pydantic v2 | Data validation and configuration |
| Anthropic Claude | LLM-assisted classification |
| GitHub Actions API | Fetching failure logs |
| Jira REST API v3 | Posting triage comments |
| ngrok | Exposing local server for webhook testing |

---

## 💡 Key Design Decisions

**Why two-stage classification?**
Heuristics are fast and free — they handle the majority of cases correctly. The LLM fallback handles ambiguous edge cases without burning API tokens on clear-cut failures.

**Why extract the Jira ticket from the commit message?**
This requires zero additional configuration per repository. Developers already reference ticket IDs in commit messages — the agent piggybacks on that existing convention.

**Why FastAPI with background tasks?**
GitHub requires a webhook response within 10 seconds or it marks the delivery as failed. By returning `202 Accepted` immediately and running triage in the background, the agent never times out regardless of how long log fetching or LLM classification takes.

---

## 📦 Part of QualityForge

This agent is UC-07 in the QualityForge GenAI QA platform — a suite of intelligent tools built to automate the repetitive, low-value tasks that consume QA engineering time.

Built with Claude Cowork and n8n in 3 weeks.

---

*For questions or contributions, open an issue in this repository.*
