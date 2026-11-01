# Employee Attendance Analysis System

A beginner-friendly, menu-driven Python + MySQL application for maintaining
employee attendance records and summarizing attendance percentage and
absenteeism patterns.

## Features

- Manage employee records (add, view, update, search, deactivate, delete)
- Record daily attendance with statuses: `Present`, `Absent`, `Leave`, `Holiday`
- **Duplicate attendance prevention** - enforced at both the application
  layer and the database layer (`UNIQUE (employee_id, attendance_date)`)
- Attendance percentage calculations based on defined working days
  (NumPy-powered)
- Employee-wise, monthly, and department-wise summaries (Pandas-powered)
- Absenteeism and monthly-trend charts (Matplotlib-powered), saved as PNGs
- Sample data generator (10 employees, ~2 months of realistic attendance)
- Built-in reconciliation check confirming reports match source records

## Tech Stack

| Layer          | Technology                     |
|----------------|---------------------------------|
| Language       | Python 3.9+                     |
| Database       | MySQL 8.0+                      |
| DB Driver      | mysql-connector-python          |
| Analysis       | pandas, numpy                   |
| Visualization  | matplotlib                      |
| Config         | python-dotenv                   |
| CLI formatting | tabulate                        |

## Folder Structure

```
employee-attendance-analysis-system/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── .env.example
├── main.py                        # Menu-driven CLI entry point
├── config/
│   ├── __init__.py
│   └── db_config.py                # Reads DB credentials from .env
├── database/
│   ├── schema.sql                  # CREATE DATABASE / CREATE TABLE statements
│   └── sample_queries.sql          # Handy ad-hoc SQL for direct inspection
├── src/
│   ├── __init__.py
│   ├── db_connection.py            # Central MySQL connection handler
│   ├── exceptions.py               # Custom exceptions
│   ├── utils.py                    # Validation + console table helpers
│   ├── employee_manager.py         # Employee CRUD
│   ├── attendance_manager.py       # Attendance CRUD + duplicate prevention
│   ├── seed_data.py                # Sample employee/attendance generator
│   ├── reports.py                  # Pandas/NumPy analysis & report builders
│   └── visualizations.py           # Matplotlib chart generation
├── tests/
│   ├── __init__.py
│   ├── test_duplicate_prevention.py   # Needs a live DB
│   └── test_attendance_percentage.py  # Pure logic, no DB needed
├── docs/
│   ├── attendance_policy.md        # Status definitions, leave/holiday treatment
│   └── er_diagram.md               # Mermaid ER diagram
└── outputs/
    ├── reports/                    # Generated CSV reports land here
    └── charts/                     # Generated PNG charts land here
```

## Database Schema

**employees**(employee_id, employee_code, employee_name, department, is_active, created_at)
**attendance**(attendance_id, employee_id, attendance_date, status, remarks, created_at)

Full DDL with the duplicate-prevention `UNIQUE` constraint is in
[`database/schema.sql`](database/schema.sql). See
[`docs/er_diagram.md`](docs/er_diagram.md) for the relationship diagram and
[`docs/attendance_policy.md`](docs/attendance_policy.md) for exactly how
Leave and Holiday are treated in every calculation.

## Prerequisites

- Python 3.9 or later
- MySQL Server 8.0 or later, running and reachable
- `pip` for installing Python packages

## Setup & Run

### 1. Get the code onto your machine

If you already have this folder, just `cd` into it. Otherwise clone it once
it's on GitHub (see the Git section below).

```bash
cd employee-attendance-analysis-system
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your database credentials

```bash
cp .env.example .env
```

Then edit `.env` and set your real MySQL `DB_USER` / `DB_PASSWORD` (and
`DB_HOST` / `DB_PORT` if not running locally on the default port).

### 5. Create the database and tables

```bash
mysql -u root -p < database/schema.sql
```

This creates the `employee_attendance_db` database plus the `employees` and
`attendance` tables with the duplicate-prevention constraint already in
place.

### 6. Run the application

```bash
python main.py
```

On startup the app verifies it can reach MySQL, then shows the main menu.

### 7. Load sample data (recommended for a first run)

From the main menu choose **4. Load Sample Data** - this inserts 10 sample
employees across 5 departments and ~2 months of realistic attendance
history, so the Reports menu has something meaningful to show immediately.

(You can also run it directly: `python -m src.seed_data`)

## Using the App

```
1. Manage Employees        -> add/view/update/search/deactivate/delete
2. Record Attendance       -> mark single or bulk attendance, view, update
3. Reports & Analysis      -> the 4 reports/charts below + reconciliation check
4. Load Sample Data
0. Exit
```

### Reports & Analysis menu

| Option | Output                                                        |
|--------|-----------------------------------------------------------------|
| 1      | Employee attendance % report (CSV in `outputs/reports/`)        |
| 2      | Monthly summary report, per employee per month (CSV)            |
| 3      | Department summary report (CSV)                                 |
| 4      | Absenteeism chart (PNG in `outputs/charts/`)                    |
| 5      | Department summary chart (PNG)                                  |
| 6      | Monthly attendance trend chart (PNG)                             |
| 7      | Reconciliation check - confirms report totals match source rows |

Each report/chart prompts for a date range (defaults are provided) before
generating.

## Running the Tests

```bash
# Pure calculation logic - no database needed:
python -m tests.test_attendance_percentage

# End-to-end duplicate-prevention check - needs the DB set up (steps 4-5 above):
python -m tests.test_duplicate_prevention
```

Both are also pytest-compatible if you have pytest installed:

```bash
pip install pytest
pytest tests/
```

## Acceptance Criteria Mapping

| Criterion                                              | Where it's satisfied                                                        |
|----------------------------------------------------------|-------------------------------------------------------------------------------|
| Duplicate employee-date records are prevented            | `UNIQUE (employee_id, attendance_date)` in schema.sql + app-level check in `attendance_manager.mark_attendance()`; verified by `tests/test_duplicate_prevention.py` |
| Leave/Holiday treatment is documented                    | `docs/attendance_policy.md`                                                   |
| Reports reconcile with source records                    | `reports.reconcile_with_source()`, exposed as menu option 7                   |

## Troubleshooting

- **"Could not connect to MySQL database"** - confirm MySQL is running,
  `.env` has the correct credentials, and you ran `database/schema.sql`.
- **Charts look empty / "No data available to chart"** - load sample data
  (main menu option 4) or widen the date range you're prompted for.
- **`ModuleNotFoundError`** - make sure your virtual environment is
  activated and `pip install -r requirements.txt` completed successfully.

## Pushing This Project to Git

See the step-by-step instructions provided alongside this project for
initializing the repository and pushing it to GitHub (or any other remote).

## License

MIT - see [LICENSE](LICENSE).
