# Project Overview (Flask Sample API)

---

## 1) What this project does

This is a Flask REST API with:

- User auth (register, login, current-user profile)
- Product management (create, list, get, update, delete)
- JWT-based protection for private endpoints
- Idempotency support for safe retry on POST requests
- ETag + `If-Match` for safe updates 
- Cursor-based pagination for product listing

---

## 2) Entry point and startup flow

### Entry point

- The application starts from [`run.py`]
- `run.py` creates the app by calling `create_app()` and runs it on port `8000`.

### App factory flow

The core app setup happens in [`app/__init__.py`]

1. Create Flask app instance
2. Load config using [`app/core/config.py`]
3. Configure logging via [`app/utils/logger.py`]
4. Initialize extensions in [`app/core/extensions.py`]
   - SQLAlchemy (`db`)
   - Flask-Migrate (`migrate`)
   - JWT manager (`jwt`)
5. Import models with [`app/db/base.py`]
6. Register:
   - request hooks (trace id)
   - global error handlers
   - JWT error handlers
   - route blueprints

---

## 3) How files are connected 

Main flow:

`Route -> Schema Validation -> Service Logic -> Model/DB -> Response Helpers`

### API routes

- [`app/api/routes/auth.py`]
- [`app/api/routes/products.py`]
- [`app/api/routes/health.py`]

Routes receive request data, call schemas/services, and return formatted responses.

### Schemas (input validation)

- [`app/schemas/auth.py`]
- [`app/schemas/product.py`]

Schemas ensure incoming payloads are valid before business logic runs.

### Services (business logic)

- [`app/services/auth_service.py`]
- [`app/services/product_service.py`]
- [`app/services/idempotency_service.py`]

Services handle core logic and database writes/reads through models.

### Models (database tables)

- [`app/models/user.py`]

- [`app/models/product.py`]
- [`app/models/idempotency_key.py`]

These define SQLAlchemy models and table structure.

### Shared helpers and constants

- Auth dependency: [`app/dependencies/auth.py`]

- Password hashing: [`app/core/security.py`]
- Error response format: [`app/utils/problem.py`]
- Response helpers: [`app/utils/responses.py`]
- ETag helper: [`app/utils/etag.py`]
- Cursor helper: [`app/utils/cursor.py`]
- API constants: [`app/constants/`]

---

## 4) Request lifecycle examples

### A) Register user (`POST /v1/auth/register`)

1. Route in [`auth.py`] checks `Idempotency-Key`
2. Request body validated by `RegisterRequestSchema`
3. Request hash is generated and checked in idempotency table
4. If already processed, saved response is replayed
5. Otherwise `AuthService.register_user()` creates user in DB
6. Response is returned and stored for future idempotent replay

### B) Create product (`POST /v1/products`)

1. JWT auth required via `@require_auth`
2. Route checks `Idempotency-Key`
3. Body validated by `ProductCreateSchema`
4. `ProductService.create_product()` writes to DB
5. Response includes an `ETag`
6. Result stored in idempotency table

### C) Update product (`PATCH /v1/products/<id>`)

1. JWT auth required
2. Client must send `If-Match`
3. Server compares header against current product ETag
4. If matched, patch is applied using `ProductService.patch_product()`
5. Updated response is returned with a new `ETag`

---

## 5) Local run, tests, logs

- Start app: `python run.py`
- Run tests: `pytest -q`
- App logs:
  - terminal output
  - [`logs/app.log`]

---