# ✓ DailyDo — Smart Task Reminder System

> Add up to 50 tasks a day. Get relentless email reminders every 4 hours until they're done. Auto-archives at midnight. Respects quiet hours. Built with Django + Celery + Redis.

---

## Features

- **User Auth** — Register, login, logout with email-based accounts
- **Task Management** — Add up to 50 tasks/day, mark complete, remove, edit
- **4-Hour Reminders** — Emails sent every 4 hours if pending tasks remain
- **Quiet Hours** — No emails between 11 PM and 5 AM
- **No-Task Nudge** — Reminder sent if you haven't added any tasks yet
- **Auto-Archive** — All pending tasks archived at 11:59 PM nightly
- **Daily Records** — Track totals, completion rate, streaks per day
- **Archive View** — Browse all archived tasks with date filtering
- **History Page** — 30-day completion history with ring meters
- **Profile Page** — Lifetime stats, streak, completion rate

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Task Queue | Celery 5.3 |
| Message Broker | Redis 7 |
| Scheduling | Celery Beat |
| Frontend | Bootstrap 5.3 + custom CSS |
| Fonts | Plus Jakarta Sans, DM Mono |

---

## Project Structure

```
daily_reminder/
├── accounts/           # Custom user model, auth views
├── tasks_app/          # Tasks, reminders, Celery tasks
│   ├── models.py       # Task, DailyRecord, ReminderLog
│   ├── views.py        # Dashboard, Add, Edit, Archive, History
│   ├── tasks.py        # Celery tasks (reminders, archive)
│   └── utils.py        # Email helpers, business logic
├── templates/
│   ├── base.html
│   ├── accounts/       # login, register, profile
│   ├── tasks/          # dashboard, add, edit, archive, history
│   └── emails/         # reminder, no_tasks, day_end (HTML + text)
├── static/
│   ├── css/style.css
│   └── js/main.js
└── tests/              # model, view, celery task tests
```

---

## Local Setup

### 1. Clone & install dependencies

```bash
cd daily_reminder
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env` and fill in your values:

```bash
cp .env .env.local
```

Key variables:
```
SECRET_KEY=your-secret-key
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
REDIS_URL=redis://localhost:6379/0
```

> **Email setup**: For Gmail, enable 2FA and create an [App Password](https://myaccount.google.com/apppasswords). Set `EMAIL_BACKEND` in settings to `django.core.mail.backends.smtp.EmailBackend` for live sending.

### 3. Set up the database

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run the application

You need **three terminals**:

```bash
# Terminal 1 — Django dev server
python manage.py runserver

# Terminal 2 — Celery worker
celery -A daily_reminder worker --loglevel=info

# Terminal 3 — Celery Beat (scheduler)
celery -A daily_reminder beat --loglevel=info
```

Open http://localhost:8000 in your browser.

---

## Email Configuration

By default the project uses `console` email backend — all emails print to Terminal 1. To enable real sending:

1. Set `EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'` in `settings.py`
2. Fill in `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in `.env`
3. Restart the server

---

## Reminder Schedule

| Event | Time |
|---|---|
| Pending task reminders | Every 4 hours (5am, 9am, 1pm, 5pm, 9pm) |
| No-tasks reminder | Every 4 hours (6am, 10am, 2pm, 6pm, 8pm) |
| Auto-archive + day summary | 11:59 PM daily |
| Quiet hours (no emails) | 11 PM – 5 AM |

---

## Running Tests

```bash
python manage.py test tests
```

Or run a specific module:

```bash
python manage.py test tests.test_models
python manage.py test tests.test_views
python manage.py test tests.test_tasks
```

---

## Admin Panel

Access at http://localhost:8000/admin/ after creating a superuser.

- Manage users, tasks, daily records, reminder logs
- Manually trigger archiving or inspect reminder history

---

## Keyboard Shortcut

Press **N** anywhere on the dashboard to jump to "Add Task".

---

## Production Checklist

- [x] Set `DEBUG=False`
- [x] Set a strong `SECRET_KEY`
- [x] Switch to PostgreSQL (`DATABASE_URL`)
- [x] Set `ALLOWED_HOSTS` to your domain
- [x] Configure real SMTP email
- [x] Run `python manage.py collectstatic`
- [x] Use a process manager (gunicorn + supervisor/systemd)
- [x] Use a proper Redis instance
- [x] Enable HTTPS

---

## License

MIT — free to use, modify, and distribute.
