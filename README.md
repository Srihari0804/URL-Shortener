# 🔗 URL Shortener API

A RESTful URL shortening service built with **FastAPI**, **PostgreSQL**, and **Redis**. Supports user registration via API keys, short link creation with optional expiration, click analytics, and Redis-backed rate limiting & caching.

---

## ✨ Features

- **Shorten URLs** — Generate unique Base62 short codes for any URL
- **Optional Expiration** — Set a TTL on short links; expired links return `410 Gone`
- **Click Analytics** — Track every redirect with IP address, user-agent, and timestamp
- **API Key Authentication** — Secure all URL operations with SHA-256 hashed API keys
- **Rate Limiting** — Redis sorted-set sliding window (100 requests / 60s per key)
- **Redis Caching** — Frequently accessed short codes are cached for 1 hour, reducing database load
- **User Management** — Sign up, view profile, regenerate API key, and delete account

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
| Testing | pytest + FastAPI `TestClient` |

---

## 📁 Project Structure

```
url_shortner/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app entry point
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
├── requirements.txt
├── .env                   # Environment variables (not committed)
└── .gitignore
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL running locally
- Redis server running on `localhost:6379`

### 1. Clone the repository

```bash
git clone <repo-url>
cd url_shortner
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
SQLALCHEMY_DATABASE_URL=postgresql://<user>:<password>@localhost/<db_name>
```

### 5. Create the database

Make sure a PostgreSQL database matching the URL above exists. Tables are auto-created on startup via `Base.metadata.create_all()`.

### 6. Start the server

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

- **Expired URL cleanup** — URLs with a past `expires_at` are rejected at redirect time (`410 Gone`) but are not yet periodically purged from the database. This is a planned enhancement (see `main.py` TODO).
- **Short code collisions** — The `generate_short_code()` function produces 6-character Base62 codes (~56 billion combinations). A retry loop ensures uniqueness against the database.
- **API key security** — Raw API keys are never stored. Only SHA-256 hashes are persisted, making database leaks non-exploitable.

---

## 📜 License

This project is open-source. Add a license of your choice.
