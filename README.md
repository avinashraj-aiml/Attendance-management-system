# Attendance Maker System

A fully offline, command-line **Attendance Management System** built in
Python. It lets you register students, mark daily attendance
(Present / Absent / Late), view records, generate percentage-based
summary reports, and export everything to CSV — all from the terminal,
with no GUI or internet connection required.

Data is stored locally in a SQLite database file, so nothing needs to
be installed or configured beyond Python itself.

---

## Features

- Register / remove students (roll number, name, class/section)
- Mark attendance per student per date (Present, Absent, or Late)
- Bulk-mark attendance for the whole class in one go
- View attendance for any specific date
- View full attendance history for any individual student
- Generate a summary report with attendance percentage per student
- Export daily attendance or the summary report to CSV
- Two ways to use it:
  - **One-shot CLI commands** — scriptable, ideal for automation/testing
  - **Interactive text menu** — run with no arguments for a guided menu

---

## Requirements

- Python 3.7 or higher (uses only the Python standard library —
  `argparse`, `sqlite3`, `csv`, `os`, `sys`, `datetime`)
- No third-party packages, no external database server, no internet
  connection needed

Check your Python version:

```bash
python3 --version
```

---

## 1. Setup

### Step 1 — Get the code

Clone the repository:

```bash
git clone https://github.com/<your-username>/attendance-maker-system.git
cd attendance-maker-system
```

(If you downloaded a ZIP instead, extract it and `cd` into the folder.)

### Step 2 — (Optional but recommended) Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

This project has no external dependencies, so this step will simply
confirm there is nothing to install — it's included so the standard
setup flow works as expected.

### Step 4 — Run it

The database and its tables are created automatically the first time
you run the program — no manual database setup is needed.

```bash
python3 main.py
```

This launches the interactive menu. To instead use one-shot commands
(better for scripting/testing), see the next section.

---

## 2. Usage — Command-Line Mode

Every feature is available as a direct subcommand. Run any command
with `-h` to see its options, e.g. `python3 main.py mark -h`.

### Add a student

```bash
python3 main.py add-student --roll 101 --name "Aarav Sharma" --class 10A
```

### List all students

```bash
python3 main.py list-students
```

### Remove a student

```bash
python3 main.py remove-student --roll 101
```

### Mark attendance

Status must be `P` (Present), `A` (Absent), or `L` (Late).
Re-running `mark` for the same student and date overwrites the
previous entry, so mistakes are easy to correct.

```bash
python3 main.py mark --roll 101 --date 2026-09-25 --status P
```

### View attendance for a date

```bash
python3 main.py view --date 2026-09-25
```

### View one student's full history

```bash
python3 main.py history --roll 101
```

### View the summary report (attendance % for every student)

```bash
python3 main.py report
```

### Export to CSV

Export one day's attendance:

```bash
python3 main.py export --date 2026-09-25
```

Export the full summary report (omit `--date`):

```bash
python3 main.py export
```

Exported files are written to the `exports/` folder.

---

## 3. Usage — Interactive Menu Mode

Simply run the program with no arguments:

```bash
python3 main.py
```

You'll see a numbered menu for every feature (add/remove students,
mark attendance individually or in bulk for the whole class, view
records, generate the report, and export CSVs). Follow the on-screen
prompts — this mode is ideal for someone unfamiliar with the CLI
flags above.

---

## 4. Example Walkthrough

```bash
python3 main.py add-student --roll 101 --name "Aarav Sharma" --class 10A
python3 main.py add-student --roll 102 --name "Diya Patel" --class 10A
python3 main.py mark --roll 101 --date 2026-09-25 --status P
python3 main.py mark --roll 102 --date 2026-09-25 --status A
python3 main.py view --date 2026-09-25
python3 main.py report
python3 main.py export --date 2026-09-25
```

---

## 5. Project Structure

```
attendance-maker-system/
├── main.py              # CLI entry point (argparse commands + interactive menu)
├── db.py                # SQLite database layer (all data access logic)
├── requirements.txt      # Dependency list (standard library only)
├── data/                 # SQLite database file lives here (auto-created)
│   └── attendance.db     # (created automatically on first run; not tracked in git)
├── exports/               # CSV exports are written here (auto-created)
└── README.md
```

---

## 6. Database Schema

**students**

| Column         | Type    | Notes                    |
|----------------|---------|---------------------------|
| id             | INTEGER | Primary key, auto-increment |
| roll_no        | TEXT    | Unique                    |
| name           | TEXT    | Required                  |
| class_section  | TEXT    | Optional                  |

**attendance**

| Column      | Type    | Notes                                      |
|-------------|---------|---------------------------------------------|
| id          | INTEGER | Primary key, auto-increment                  |
| student_id  | INTEGER | Foreign key → students.id                    |
| date        | TEXT    | Format `YYYY-MM-DD`                          |
| status      | TEXT    | One of `P`, `A`, `L`                         |

A `(student_id, date)` unique constraint ensures a student has at
most one attendance record per day; re-marking updates it in place.

---

## 7. Notes for Evaluators

- The project runs entirely from the terminal — no GUI is required at
  any step.
- On first run, `main.py` automatically initializes `data/attendance.db`
  with the required tables, so no manual database setup is needed.
- All core functionality (add/remove students, mark attendance, view,
  history, report, export) is exercised by the one-shot CLI commands
  shown in Section 2, which makes the system easy to script and test.
