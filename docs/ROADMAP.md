# GreenhouseIoT — Development Roadmap

## Product goal

Build a maintainable FastAPI backend for a multi-tenant greenhouse monitoring application. Each organization can manage multiple farms/greenhouses (called salons in the current product terminology), assign crops to growing areas, configure sensor thresholds, ingest measurements from IoT devices, and expose current status/history to a Persian RTL Next.js dashboard.

This roadmap is a proposed implementation plan, not a claim that the listed features already exist.

## Current baseline

The current `main` branch provides:
- FastAPI application factory and lifespan hook.
- Versioned `/api/v1` router and `/api/v1/health` endpoint.
- Pydantic Settings configuration and centralized logging.
- One async HTTP smoke test.
- Dockerfile and development quality tools (pytest, Ruff, mypy).

The database, domain APIs, authentication, device ingestion, MQTT worker, WebSockets, and operational monitoring are not implemented yet.

## Guiding architecture

Start with a **modular monolith**. Keep domain boundaries clear, but do not introduce microservices until a measured scaling or operational need justifies them.

Suggested package structure as the application grows:

```text
app/
  main.py
  api/v1/
    router.py
    health.py
    auth.py
    farms.py
    growing_areas.py
    crops.py
    devices.py
    telemetry.py
    alerts.py
  core/
    config.py
    logging.py
    security.py
    exceptions.py
  db/
    session.py
    base.py
    migrations/
  models/
  schemas/
  repositories/
  services/
  workers/
tests/
```

Avoid creating empty layers or generic abstractions before a use case needs them. Keep HTTP schemas separate from SQLAlchemy models, and keep business rules in service/domain code rather than route handlers.

## Phase 0 — Make the foundation reproducible

**Goal:** Every developer can run, test, and lint the application consistently.

- [ ] Add a clear local setup and production configuration guide.
- [ ] Validate required production settings and reject unsafe defaults in production.
- [ ] Add CI for Ruff, mypy, and pytest.
- [ ] Add structured request logging and a request/correlation ID.
- [ ] Separate liveness (`/health/live`) from readiness (`/health/ready`) once dependencies exist.
- [ ] Document supported Python version and dependency-locking policy.

**Acceptance criteria:** A clean checkout installs reproducibly; CI passes; misconfigured production settings fail at startup.

## Phase 1 — Persistence and migrations

**Goal:** Establish reliable persistence before building business endpoints.

- [ ] Choose PostgreSQL as the initial relational database.
- [ ] Add SQLAlchemy 2 async engine/session management and Alembic migrations.
- [ ] Add a local Compose setup with PostgreSQL, health checks, and a persistent volume.
- [ ] Add database lifecycle management to FastAPI lifespan.
- [ ] Add tests using an isolated test database and deterministic fixtures.
- [ ] Keep credentials in environment variables; never commit real secrets.

**Design note:** Begin with PostgreSQL. Add TimescaleDB/hypertables only when measurement volume and query patterns justify it; TimescaleDB is an extension, not a substitute for designing retention and indexes.

**Acceptance criteria:** Migrations can create a fresh database, tests do not depend on a developer's database, and shutdown disposes of the engine cleanly.

## Phase 2 — Domain model and tenant isolation

**Goal:** Represent the product's real-world hierarchy safely.

Proposed initial entities:
- **Organization/account:** tenant boundary and ownership.
- **User and membership:** identity, role, and organization membership.
- **Farm/greenhouse:** a managed site.
- **Growing area:** a greenhouse section/bed/zone; map the product's “salon” terminology to a clearly defined domain entity.
- **Crop catalog:** plant species/variety and optional growth-stage metadata.
- **Crop assignment:** crop planted in a growing area, including dates and growth stage.
- **Sensor/device:** registered hardware, status, and installation location.
- **Sensor type:** temperature, humidity, soil moisture, pH, EC, light, or other supported measurement type.
- **Threshold policy:** min/max values and units, scoped to a crop assignment and sensor type.
- **Measurement:** timestamped sensor value with source/device metadata.
- **Alert:** threshold violation, severity, lifecycle, and acknowledgement.

Important decisions:
- Use stable IDs and foreign keys.
- Store timestamps in UTC and include explicit measurement units.
- Model crop assignments separately from the crop catalog: a species has general metadata, while an assignment represents a particular crop growing in a particular area at a particular time.
- Store threshold policies as data, not hard-coded conditionals.
- Define how thresholds vary by growth stage and sensor type before implementing alert logic.
- Enforce tenant scoping in every query and mutation; never rely only on the frontend to filter data.

**Acceptance criteria:** Tests prove that users in one organization cannot read or mutate another organization's resources.

## Phase 3 — Authentication, authorization, and CRUD APIs

**Goal:** Make the domain usable by the Next.js application.

Suggested API groups:
- `/api/v1/auth`
- `/api/v1/farms`
- `/api/v1/growing-areas`
- `/api/v1/crops`
- `/api/v1/devices`
- `/api/v1/threshold-policies`
- `/api/v1/telemetry`
- `/api/v1/alerts`

Tasks:
- [ ] Define the identity provider/session strategy before implementing login.
- [ ] Implement role-based permissions appropriate to owners, managers, and viewers.
- [ ] Add pagination, filtering, sorting, validation, and consistent error responses.
- [ ] Add crop catalog search and Persian display names, with scientific names and identifiers where available.
- [ ] Generate and review the OpenAPI contract for frontend integration.
- [ ] Add audit records for security-sensitive configuration changes.

Do not build custom password/token infrastructure unless it is a deliberate product requirement. For browser sessions, prefer secure, HttpOnly cookies when the deployment topology supports them. Device credentials should be separate from user credentials.

**Acceptance criteria:** Core CRUD workflows work through documented APIs with authorization tests and predictable validation errors.

## Phase 4 — Telemetry ingestion and storage

**Goal:** Reliably accept real measurements from devices.

- [ ] Define a versioned measurement payload: device ID, sensor ID/type, value, unit, event timestamp, and unique message/event ID.
- [ ] Authenticate devices independently of human users.
- [ ] Validate payloads and reject unknown devices, unsupported units, and invalid values.
- [ ] Make ingestion idempotent using a unique event ID or device/message key.
- [ ] Record event time separately from server receive time.
- [ ] Define behavior for offline devices, delayed delivery, retries, duplicate events, and clock drift.
- [ ] Add database indexes based on actual dashboard queries.
- [ ] Establish a retention and aggregation policy for high-volume measurements.

Start with an authenticated HTTP ingestion endpoint if it fits the hardware. Add MQTT when the device fleet and delivery requirements call for it. If MQTT is adopted, define topic conventions, broker authentication/ACLs, QoS, reconnect behavior, and message validation before connecting a worker.

**Acceptance criteria:** A simulated device can submit measurements; duplicates do not create duplicate records; invalid messages are observable and do not crash the service.

## Phase 5 — Threshold evaluation and alerts

**Goal:** Turn measurements into actionable greenhouse status.

- [ ] Evaluate measurements against the active threshold policy for the relevant crop assignment and sensor.
- [ ] Define boundary semantics explicitly: below minimum, above maximum, and exactly on a limit.
- [ ] Avoid alert flapping with configurable hysteresis and/or sustained-duration rules.
- [ ] Model alert states such as open, acknowledged, and resolved.
- [ ] Deduplicate repeated violations into a single alert episode.
- [ ] Track missing/stale sensor data separately from out-of-range measurements.
- [ ] Record which policy and measurement caused each alert.

Run evaluation in the ingestion/service flow only if it remains lightweight; otherwise use a worker/queue. Keep the rules deterministic and unit-testable.

**Acceptance criteria:** Tests cover low/high readings, threshold changes, stale sensors, duplicates, recovery, and alert deduplication.

## Phase 6 — Live updates and dashboard queries

**Goal:** Support the Next.js dashboard without excessive polling.

- [ ] Add efficient endpoints for latest readings, time ranges, device status, and alert summaries.
- [ ] Add WebSocket events for new measurements, alert state changes, and device connectivity.
- [ ] Authenticate WebSocket connections and enforce the same tenant permissions as HTTP.
- [ ] Send only the fields the dashboard needs; include event IDs/timestamps and a documented event schema.
- [ ] Treat WebSockets as a live-update channel, not the source of truth. Clients should reconnect and refetch REST snapshots after disconnection.
- [ ] Define heartbeat, reconnect/backoff, and stale-connection behavior.
- [ ] If multiple API instances are deployed, use a shared pub/sub or broker-backed fan-out; an in-process connection manager alone will not broadcast across instances.

**Acceptance criteria:** A new reading appears in the dashboard promptly, reconnects recover missed state through HTTP, and one tenant never receives another tenant's events.

## Phase 7 — Production readiness

**Goal:** Operate the service safely and diagnose failures.

- [ ] Add dependency-aware readiness checks without exposing secrets.
- [ ] Add metrics for request latency/errors, ingestion throughput, rejected messages, worker health, database pool usage, and WebSocket connections.
- [ ] Add error reporting and operational alerts.
- [ ] Set database backup/restore procedures and test restoration.
- [ ] Define retention, deletion, and access policies for telemetry and audit data.
- [ ] Run dependency and container security scans.
- [ ] Use non-root containers, pinned/reproducible dependencies, and least-privilege database credentials.
- [ ] Document migrations and rollback/forward-fix procedures.
- [ ] Load-test realistic ingestion and dashboard queries before optimizing.

**Acceptance criteria:** Operators can identify API/database/worker failures, restore data from backup, and deploy migrations through a documented procedure.

## Suggested priority order

| Priority | Deliverable | Why now |
|---|---|---|
| P0 | CI, configuration validation, tests | Prevent regressions early |
| P0 | PostgreSQL, SQLAlchemy, Alembic | Required for all persistent features |
| P0 | Tenant/domain model | Determines ownership and access boundaries |
| P1 | Auth and core CRUD | Enables the dashboard's basic workflows |
| P1 | Device registration and HTTP ingestion | Proves the end-to-end IoT path |
| P1 | Latest readings and history | Provides immediate product value |
| P2 | Thresholds and alert lifecycle | Converts data into useful status |
| P2 | WebSocket live updates | Improves dashboard responsiveness |
| P2 | MQTT and background workers | Add when device/protocol requirements are confirmed |
| P3 | Aggregation, advanced analytics, scaling | Add based on real usage and measured bottlenecks |

## First vertical slice

Build this end-to-end before expanding the scope:

1. Start PostgreSQL locally and run an Alembic migration.
2. Create an organization, greenhouse, growing area, and registered device.
3. Accept one authenticated temperature or humidity measurement.
4. Persist it with event and receive timestamps.
5. Expose the latest measurement through a tenant-scoped API.
6. Test successful ingestion, invalid payloads, duplicate events, and cross-tenant access.
7. Connect a simple Next.js screen to the endpoint.

This slice tests the database, domain boundaries, API design, and device data path together. It is more valuable than implementing many disconnected endpoints.

## Decisions to confirm before deeper implementation

- Is “salon” a greenhouse, a room/zone inside a greenhouse, or another business entity?
- What device protocol and hardware are planned: HTTP, MQTT, or both?
- Which sensors and units are actually supported?
- Will the application support multiple organizations and users from the first release?
- What are the expected device count, measurement frequency, and history-retention period?
- What authentication system will the existing product use?

These decisions affect the schema and ingestion design; avoid premature complexity until they are known.
