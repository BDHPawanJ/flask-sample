# Flask Sample Project 

Flask REST API with:

- JWT auth (`register`, `login`)
- Product CRUD
- Idempotency-Key support on POST endpoints
- ETag + If-Match optimistic concurrency for PATCH
- Cursor pagination on product listing
- Service-layer architecture + pytest tests

## Tech Stack

- Flask
- SQLAlchemy + Flask-SQLAlchemy
- Flask-Migrate (Alembic migrations)
- MySQL (runtime + tests, configurable via env)
- Flask-JWT-Extended
- passlib bcrypt hashing
- Marshmallow validation
- pytest

## Project Structure

- `app/api/routes/` - route handlers
- `app/core/` - config, security, extensions
- `app/constants/` - centralized status codes, API messages, and problem codes
- `app/db/` - model import wiring
- `app/dependencies/` - auth helper
- `app/models/` - SQLAlchemy models
- `app/schemas/` - Marshmallow schemas
- `app/services/` - business logic
- `app/utils/` - cursor, serialization, ETag, problem response, logging

## Setup

1. Create and activate a virtualenv
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file at project root:

```bash
cp .env.example .env
```

Then edit `.env` with your values.

4. Run migrations:

```bash
flask db upgrade
```

5. Run the app:

```bash
python run.py
```

API base URL: `http://localhost:8000`

Logs:
- Console output in the terminal where `python run.py` is started
- File output in `logs/app.log`

## Run Tests

```bash
pytest -q
```

Tests use `TEST_DATABASE_URL` from `.env` and expect a reachable MySQL test database.

## API Endpoints

### Auth

- `POST /v1/auth/register` (requires `Idempotency-Key`)
- `POST /v1/auth/login`
- `GET /v1/auth/me` (Bearer token required)

### Products

- `POST /v1/products` (Bearer + `Idempotency-Key` required)
- `GET /v1/products` (public, `limit`, `cursor`, `search`)
- `GET /v1/products/{product_id}` (public, returns `ETag`)
- `PATCH /v1/products/{product_id}` (Bearer + `If-Match` required)
- `DELETE /v1/products/{product_id}` (Bearer required, returns 204)

## Error Format (`application/problem+json`)

```json
{
  "type": "about:blank",
  "title": "Validation Error",
  "status": 422,
  "detail": "Request validation failed.",
  "instance": "/v1/products",
  "code": "validation_error",
  "trace_id": "d2e2f06f-b2d0-47a2-9d58-4ba6f4604a2b",
  "errors": {}
}
```

## Sample curl Commands

### Register

```bash
curl -X POST 'http://localhost:8000/v1/auth/register' \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: reg-001' \
  -d '{"email":"user@example.com","password":"strongpass123"}'
```

### Login

```bash
curl -X POST 'http://localhost:8000/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"strongpass123"}'
```

### Create Product

```bash
curl -X POST 'http://localhost:8000/v1/products' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  -H 'Idempotency-Key: prod-001' \
  -d '{"name":"Keyboard","description":"Mechanical keyboard","price":"129.99","stock":5}'
```

### List Products (cursor pagination)

```bash
curl 'http://localhost:8000/v1/products?limit=10'
```
