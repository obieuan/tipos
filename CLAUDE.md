# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tipos Beach House is a family beach house reservation system (simplified Calendly). Target users are elderly family members — UX must be extremely simple with large fonts, high contrast, and minimal flows. The app is in Spanish.

## Tech Stack

- **Backend:** Python Flask (REST API + Jinja2 server-rendered templates)
- **Database:** PostgreSQL 16 (Docker)
- **Frontend:** Vanilla HTML/CSS/JS — no JS frameworks. Mobile-first responsive.
- **Auth:** Username + numeric PIN (4-6 digits, bcrypt-hashed), Flask-Login sessions (30-day timeout)
- **Infrastructure:** Docker Compose (Flask/Gunicorn + PostgreSQL + Nginx reverse proxy)
- **Migrations:** Flask-Migrate (Alembic)

## Commands

```bash
# Build and run (production)
docker-compose build
docker-compose up -d

# Seed initial data (admin user + default settings)
docker-compose exec app python seed.py

# Database migrations
flask db migrate -m "Description"
flask db upgrade

# Local development (without Docker)
pip install -r requirements.txt
export DATABASE_URL=postgresql://beach:password@localhost/beachhouse
export SECRET_KEY=dev-secret-key
export FLASK_ENV=development
flask run
```

## Architecture

```
docker-compose.yml
├── nginx        → reverse proxy, SSL termination
├── flask-app    → API + server-rendered frontend (Gunicorn in prod)
└── postgres     → database
```

**Layered structure inside `app/`:**

- `models/` — SQLAlchemy ORM models (user, reservation, blocked_day, activity_log, app_setting)
- `services/` — Business logic layer (reservation_service, user_service, log_service). All validation and rules live here.
- `api/` — Flask blueprints exposing REST endpoints (auth, reservations, calendar, history, admin)
- `views.py` — Page-serving blueprint (renders templates, redirects unauthenticated users)
- `templates/` — Jinja2 server-rendered pages. NOT an SPA.
- `static/` — Single CSS file (mobile-first), vanilla JS modules (calendar, modals, pin-pad, admin)

**App factory pattern:** `app/__init__.py` creates the Flask app. Extensions (db, migrate, login_manager) are initialized in `app/extensions.py`.

## Key Data Model Relationships

- `reservations` has `owner_id` FK to `users`, with UNIQUE(date, block) constraint
- `reservation_guests` is a many-to-many join between reservations and users
- `activity_log` records every action with user_id, action type, and optional reservation_id/target_user_id
- `blocked_days` stores admin-blocked dates
- `app_settings` is a key-value config table (disclaimer_text, booking_mode, min/max days ahead, site_name)

## Business Rules

- No public registration — admin creates all users
- Reservations require: future date, not blocked, no conflict, within min/max days ahead, disclaimer accepted
- Owners can cancel, reassign, and manage guests. Guests can only self-remove.
- No hard deletes — users are deactivated, logs are permanent
- All actions logged to `activity_log` with human-readable text generated server-side
- The `block` field on reservations supports future "morning/afternoon" mode but currently only "full_day" is used

## UX Constraints (Elderly Users)

- Minimum 18px font (14px only for secondary metadata), 24px+ for titles/buttons
- Tap targets: minimum 48x48px, buttons 48-56px+ height
- Dark text (#1A1A1A) on light backgrounds (#FAFAFA)
- Modals must be fullscreen on mobile
- Custom on-screen PIN pad (not OS keyboard) for consistent large buttons
- Fixed bottom nav: Calendario | Historial | Perfil | (Admin)
- Font: Inter (Google Fonts), fallback: Segoe UI, system-ui, sans-serif
- All dates in America/Merida timezone (CST UTC-6)

## Design Tokens

- Primary: `#2E7D6F` (teal), Secondary: `#F5A623` (warm orange)
- Error: `#D32F2F`, Success: `#388E3C`
- User color pool: `#4A90D9`, `#E07B4C`, `#7BC47F`, `#D4A843`, `#9B6BB0`, `#D96B7A`, `#5BBCBF`, `#8B8B5E`

## Reference

Full specification with data model schemas, API endpoints, and detailed UI requirements: `TIPOS_BEACH_HOUSE_INSTRUCTIONS.md`
