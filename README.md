# aws_chatbot

AWS chatbot API backed by FastAPI, LangChain, and LocalStack.

## Required `.env` Variables

Create a `.env` file in the project root.

| Variable | Required | Example | Notes |
|---|---|---|---|
| `MODEL` | Yes | `gpt-5-nano-2025-08-07` | Model name used by LangChain. If no provider prefix is included, code defaults to `openai:`. |
| `OPENAI_API_KEY` | Yes* | `sk-...` | OpenAI API key. Required when using an OpenAI model. |
| `OPEN_API_KEY` | Yes* | `sk-...` | Backward-compatible alias for `OPENAI_API_KEY`. If set and `OPENAI_API_KEY` is missing, it is copied at runtime. |
| `MODEL_TEMP` | No | `0` | Model temperature. Defaults to `0`. |
| `LOG_LEVEL` | No | `INFO` | App log level. Defaults to `INFO`. |
| `USE_LOCALSTACK` | No | `true` | Set to `true` to use LocalStack endpoints. Defaults to `false`. |
| `LOCALSTACK_URL` | No | `http://localstack:4566` | LocalStack endpoint used when `USE_LOCALSTACK=true`. Defaults to `http://localhost:4566` if unset. |
| `AWS_REGION` | No | `us-east-1` | AWS region. Defaults to `us-east-1` if unset. |
| `AWS_PROFILE` | No | `default` | Optional profile for real AWS usage (not LocalStack). |
| `AWS_ACCESS_KEY_ID` | No | `test` | Used for LocalStack clients when `USE_LOCALSTACK=true`. |
| `AWS_SECRET_ACCESS_KEY` | No | `test` | Used for LocalStack clients when `USE_LOCALSTACK=true`. |

\* Provide at least one of `OPENAI_API_KEY` or `OPEN_API_KEY` for OpenAI models.

## Start with Docker Compose

```bash
docker compose up --build -d
```

Check status:

```bash
docker compose ps
```

Follow logs:

```bash
docker compose logs -f chatbot
```

## Test with `curl`

### 1) New conversation (payload `user_id`)

```bash
curl -sS http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user-1",
    "query": "What buckets exist?"
  }'
```

### 2) Follow-up in same conversation (same payload `user_id`)

```bash
curl -sS http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user-1",
    "query": "Which of those are public?"
  }'
```

### 3) Header-based conversation tracking (`x-user-id`)

```bash
curl -sS http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-user-id: demo-user-2" \
  -d '{
    "query": "List IAM users."
  }'
```

Important: for follow-up context to work, every request in the same thread must include the same identifier, either:
- `user_id` in the JSON payload, or
- `x-user-id` header.

If neither is provided, the backend generates a random ID and the next request will not have prior context unless you send a stable `user_id` or `x-user-id`.
