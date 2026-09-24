# 🔗 URL Shortener API

A RESTful URL shortening service built with **FastAPI**, **PostgreSQL**, and **Redis**. Supports user registration via API keys, short link creation with optional expiration, click analytics, Redis-backed rate limiting & caching, automated expired URL cleanup, and a full CI/CD pipeline deploying to Docker Hub.

---

## ✨ Features

- **Shorten URLs** — Generate unique Base62 short codes for any URL
- **Optional Expiration** — Set a TTL on short links; expired links return `410 Gone`
- **Automated Cleanup** — Background scheduler (APScheduler) purges expired URLs from the database every hour
- **Click Analytics** — Track every redirect with IP address, user-agent, and timestamp
- **API Key Authentication** — Secure all URL operations with SHA-256 hashed API keys
- **Rate Limiting** — Redis sorted-set sliding window (100 requests / 60s per key)
- **Redis Caching** — Frequently accessed short codes are cached for 1 hour, reducing database load
- **User Management** — Sign up, view profile, regenerate API key, and delete account
- **Dockerized** — Full Docker Compose setup (app + PostgreSQL + Redis) for one-command deployment
- **CI/CD** — GitHub Actions pipeline: test → build → push to Docker Hub on every push to `main`

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Database | PostgreSQL (via SQLAlchemy ORM) |
| Cache / Rate Limiter | Redis (async via `redis.asyncio`) |
| Auth | API Key (header-based, SHA-256 hashed) |
| Validation | Pydantic v2 |
| Password Hashing | bcrypt (via passlib) |
| Background Jobs | APScheduler |
| Containerization | Docker & Docker Compose |
| CI/CD | GitHub Actions → Docker Hub |
| Testing | pytest + FastAPI `TestClient` |

---

## 📁 Project Structure

```
url_shortner/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app entry point + lifespan scheduler
│   ├── database.py        # SQLAlchemy engine, session & dependency
│   ├── models.py          # ORM models (Users, URLS, Clicks)
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── utils.py           # Hashing, API key generation, short code generation
│   ├── redis_client.py    # Redis client factory
│   └── routers/
│       ├── users.py       # User signup, key regen, delete, profile
│       └── urls.py        # Shorten, redirect, stats, delete, list
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # Fixtures: test DB, client, auth header
│   ├── test_users.py      # User route tests
│   └── test_urls.py       # URL route tests
├── .github/
│   └── workflows/
│       └── ci.yml         # CI/CD pipeline (test → build → push to Docker Hub)
├── Dockerfile             # App container image
├── docker-compose.yml     # Multi-service orchestration (app + Postgres + Redis)
├── requirements.txt
├── .env                   # Environment variables (not committed)
└── .gitignore
```

---

## 🚀 Getting Started

### Option A: Docker Compose (Recommended)

The easiest way to run the entire stack — no manual setup required:

```bash
git clone <repo-url>
cd url_shortner
docker compose up --build
```

This spins up **three containers** (FastAPI app, PostgreSQL, Redis) with networking, health checks, and persistent storage pre-configured. The API will be available at `http://localhost:8000`.

### Option B: Manual Setup

#### Prerequisites

- Python 3.10+
- PostgreSQL running locally
- Redis server (defaults to `localhost:6379`; configurable via `.env`)

#### 1. Clone the repository

```bash
git clone <repo-url>
cd url_shortner
```

#### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure environment variables

Create a `.env` file in the project root:

```env
SQLALCHEMY_DATABASE_URL=postgresql://<user>:<password>@localhost/<db_name>
REDIS_HOST=localhost
REDIS_PORT=6379
```

#### 5. Create the database

Make sure a PostgreSQL database matching the URL above exists. Tables are auto-created on startup via `Base.metadata.create_all()`.

#### 6. Make sure Redis is running

```bash
docker run --name redis-cache -p 6379:6379 redis:latest
```

#### 7. Start the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Interactive docs at [`/docs`](http://127.0.0.1:8000/docs).

---

## 📡 API Endpoints

### Users (`/users`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/users/signup` | ✗ | Register a new user; returns a one-time API key |
| `POST` | `/users/regenerate-key` | ✗ | Re-authenticate with email & password to get a new API key |
| `GET` | `/users/me` | API-Key | Get current user profile |
| `DELETE` | `/users/me` | API-Key | Delete your account |

### URLs (`/urls`)

| Method | Endpoint | Auth | Rate Limited | Description |
|---|---|---|---|---|
| `POST` | `/urls/shorten` | API-Key | ✔ | Create a short URL (with optional `expires_at`) |
| `GET` | `/urls/me` | API-Key | ✔ | List all your shortened URLs |
| `GET` | `/urls/{id}/stats` | API-Key | ✔ | Get click analytics for a URL |
| `DELETE` | `/urls/{id}` | API-Key | ✔ | Delete a shortened URL (also purges Redis cache) |
| `GET` | `/urls/{short_code}` | ✗ | ✗ | Redirect to the original URL (307) |

### Authentication

All protected endpoints require an `API-Key` header:

```
API-Key: url_<your_api_key>
```

The API key is returned **once** during signup or key regeneration — store it securely.

---

## ⚡ Redis Usage

Redis is used for two purposes:

### Rate Limiting (Sliding Window)

Every rate-limited endpoint passes through a `rate_limiter` dependency that uses a **Redis sorted set** per API key:

- **Key**: `ratelimit:<api_key>`
- **Window**: 60 seconds
- **Limit**: 100 requests per window
- Old entries outside the window are pruned with `ZREMRANGEBYSCORE`, and new request timestamps are added with `ZADD`

Exceeding the limit returns `429 Too Many Requests`.

### Caching (Short Code → Original URL)

On redirect (`GET /urls/{short_code}`):

1. Redis is checked first for a cached mapping
2. On a **cache miss**, the database is queried and the result is cached with a **1-hour TTL** (`ex=3600`)
3. On a **cache hit**, the redirect is served directly from Redis — no database query needed
4. When a URL is **deleted**, its cache entry is also purged

---

## 🧹 Expired URL Cleanup

Expired URLs are handled at two levels:

1. **At redirect time** — If a user hits an expired short code, the API returns `410 Gone` immediately
2. **Background cleanup** — An APScheduler job runs **every hour** during the app's lifespan, deleting all URLs whose `expires_at` has passed. This prevents expired data from accumulating in the database

---

## 🔄 CI/CD Pipeline

The project uses **GitHub Actions** for continuous integration and deployment:

```
Push to main → Run Tests (pytest) → Build Docker Image → Push to Docker Hub
              └─ PR to main → Run Tests only (no deploy)
```

- **CI (test)**: Spins up PostgreSQL and Redis service containers, installs dependencies, runs `pytest`
- **CD (deploy)**: On push to `main` only — builds the Docker image and pushes to Docker Hub with two tags:
  - `latest` — always points to the most recent build
  - `<commit-sha>` — for version traceability

---

## 🐳 Docker

### Dockerfile

The app image is built from a Python base, installs dependencies, copies the application code, and runs Uvicorn on port 8000.

### Docker Compose

`docker-compose.yml` orchestrates three services:

| Service | Image | Purpose |
|---|---|---|
| `db` | `postgres:16-alpine` | PostgreSQL database with persistent volume and health checks |
| `redis` | `redis:alpine` | Redis for caching and rate limiting |
| `web` | Built from `Dockerfile` | FastAPI application, waits for `db` and `redis` before starting |

```bash
docker compose up --build    # Start all services
docker compose down          # Stop all services
docker compose down -v       # Stop and delete database volume
```

---

## 🎯 Design Decisions

- **Cascade deletes** — Deleting a user cascades to their URLs and clicks (`ondelete="CASCADE"`), chosen for schema simplicity over retaining orphaned analytics data.
- **Sync DB + async Redis** — SQLAlchemy sessions are synchronous while Redis calls are async, since FastAPI safely runs sync routes in a thread pool. Fully async DB access (via `asyncpg`) is a natural next optimization.
- **Sliding window over fixed window** — Chosen to avoid the boundary-burst problem of fixed-window rate limiting, at the cost of slightly more Redis operations per request.
- **SHA-256 for API keys (not bcrypt)** — API key lookups must be fast and deterministic for every authenticated request. Unlike passwords, where slow hashing deters brute-force attacks on leaked hashes, API keys are high-entropy secrets (32 bytes of randomness), making SHA-256 a safe and practical choice.
- **APScheduler for cleanup** — Lightweight, in-process scheduler avoids the operational overhead of an external task queue (Celery) for a single periodic job.

---

## ⚠️ Known Limitations & Scaling Notes

- **Cache staleness on update** — Cached redirects may serve briefly-stale data for up to the 1-hour TTL if the underlying URL is deleted and the delete-invalidation call to Redis fails or races.
- **Rate limiter race condition** — The `zremrangebyscore` → `zcard` → `zadd` pattern is not atomic; concurrent requests near the limit could both pass. A Redis pipeline or Lua script would close this gap.
- **Horizontal scaling** — Rate-limit keys (`ratelimit:{api_key}`) are fully independent per user, making this design naturally shardable across a Redis Cluster if traffic grows beyond a single instance.
- **Scheduler in multi-instance deployments** — APScheduler runs per process, so running multiple app instances would create duplicate cleanup jobs. A distributed lock (e.g., Redis-based) or an external scheduler would be needed at scale.

---

## 🧪 Testing

Tests use a **separate PostgreSQL database** (`url_shortner_testing_db`) and pytest fixtures that drop & recreate all tables for each test session.

### Setup

1. Create the test database in PostgreSQL:

   ```sql
   CREATE DATABASE url_shortner_testing_db;
   ```

2. Run the tests:

   ```bash
   pytest tests/ -v
   ```

### Test Coverage

**User tests** (`test_users.py`):
- Signup, duplicate email conflict (409)
- API key regeneration (success, invalid email, wrong password)
- Delete account (success, invalid key, empty key, missing header)
- Get profile (success, invalid key)

**URL tests** (`test_urls.py`):
- Create short URL with expiration
- List all user URLs
- Redirect (307) and verify click stats
- Delete URL and verify 404 on stats
- Redirect to expired URL returns 410 Gone

---

## 📌 Notes

- **Short code collisions** — The `generate_short_code()` function produces 6-character Base62 codes (~56 billion combinations). A retry loop ensures uniqueness against the database.
- **API key security** — Raw API keys are never stored. Only SHA-256 hashes are persisted, making database leaks non-exploitable.

---

## 📜 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
