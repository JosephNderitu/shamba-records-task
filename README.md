# 🌱 SmartSeason Field Monitoring System

> A full-stack web application that helps coordinators and field agents track crop progress across multiple fields during a growing season.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?style=flat&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=flat&logo=docker&logoColor=white)
![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?style=flat&logo=render&logoColor=white)

---

## 🔗 Live Demo

**[https://shamba-records-task.onrender.com](https://shamba-records-task.onrender.com)**

---

## 🔐 Demo Credentials

| Role | Username | Email | Password |
|------|----------|-------|----------|
| Admin (Coordinator) | `Admin` | `test.admin@gmail.com` | `Admin@2026` |
| Field Agent | `agent01` | `agent@gmail.com` | `agent@2026` |

---

## ✅ Features

- **Role-based access control** — Admin and Field Agent roles with separate views
- **Field management** — Create, edit, delete and assign fields (Admin only)
- **Field updates** — Agents post stage updates with notes and observations
- **Field lifecycle** — Planted → Growing → Ready → Harvested
- **Computed status** — Active, At Risk, Completed (auto-calculated)
- **Dashboards** — Separate views for Admin and Agent with Chart.js insights
- **Activity timeline** — Full audit trail of every field update
- **Search & filters** — Filter fields by stage, status, or keyword
- **Jazzmin admin panel** — Enhanced Django admin interface

---

## 🚀 Local Setup

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/JosephNderitu/shamba-records-task.git
cd shamba-records-task

# 2. Create environment file
copy .env.example .env
# Edit .env with your values

# 3. Build and start
docker compose up --build

# 4. Visit the app
# http://localhost
```

### Environment Variables

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-here
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=smartseason_db
POSTGRES_USER=smartseason_user
POSTGRES_PASSWORD=your-password
DB_HOST=db
DB_PORT=5432
```

---

## 🔄 Field Status Logic

Status is computed dynamically as a model property — no extra database column needed:

| Status | Condition |
|--------|-----------|
| ✅ **Active** | Updated within the last 7 days and progressing normally |
| ⚠️ **At Risk** | No update in 7+ days OR planted 90+ days without reaching Ready |
| 🏁 **Completed** | Current stage is Harvested |

---

## ⚙️ CI/CD Pipeline

Every push to `master` triggers GitHub Actions:

1. **Test** — runs Django system checks, migrations and test suite against PostgreSQL
2. **Deploy** — triggers automatic deployment on Render if all tests pass

---

## 💡 Design Decisions

- **Server-side rendering** over REST + SPA — keeps the stack simple and ships faster for this scope
- **Computed status** as a model `@property` — avoids stale data and removes need for scheduled jobs
- **Single Django app** (`fields`) — flat structure, easy to navigate, no premature abstraction
- **Docker** for dev/prod parity — same environment locally and in production
- **WhiteNoise** for static files — simplifies Nginx config while staying performant

---

## 📌 Assumptions

- Fields without an assigned agent are visible to admins only
- Field agents cannot create, edit, or delete fields
- Every stage change goes through the Post Update form ensuring a full audit trail
- A field with no update history is immediately flagged **At Risk** for safety
- The 7-day and 90-day thresholds are adjustable per crop type in future iterations

---

## 📁 Project Structure
shamba-records-task/
├── app/
│   ├── fields/          # Main Django app
│   │   ├── models.py    # Field, FieldUpdate, UserProfile
│   │   ├── views.py     # All view logic
│   │   ├── admin.py     # Jazzmin-enhanced admin
│   │   └── tests.py     # Test suite
│   ├── smartseason/     # Django project config
│   ├── templates/       # HTML templates
│   └── requirements.txt
├── nginx/               # Nginx config
├── .github/workflows/   # CI/CD pipeline
├── docker-compose.yml
├── Dockerfile
├── render.yaml
└── .env.example

---

## 👨‍💻 Author

**Joseph Nderitu**
GitHub: [@JosephNderitu](https://github.com/JosephNderitu)

---

*SmartSeason — Technical Assessment Submission — 2026*