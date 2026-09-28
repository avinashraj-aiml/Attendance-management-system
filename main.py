#!/usr/bin/env python3
"""
Attendance Maker System
========================
A fully command-line, offline attendance management system built with
Python's standard library and SQLite.

Run with a subcommand for one-shot use (scriptable / gradeable), e.g.:

    python main.py add-student --roll 101 --name "John Doe" --class 10A
    python main.py mark --date 2026-09-25 --roll 101 --status P
    python main.py view --date 2026-09-25
    python main.py report
    python main.py export --date 2026-09-25

Or run with no arguments at all to get an interactive text menu:

    python main.py

See README.md for full usage instructions.
"""

import argparse
import csv
import os
import sys
from datetime import date

import db

EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")

STATUS_LABELS = {"P": "Present", "A": "Absent", "L": "Late", None: "Not Marked"}


# ---------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------

def cmd_add_student(args):
    ok, msg = db.add_student(args.roll, args.name, args.class_section)
    print(msg)
    sys.exit(0 if ok else 1)


def cmd_remove_student(args):
    ok = db.remove_student(args.roll)
    if ok:
        print(f"Student with roll number '{args.roll}' removed.")
    else:
        print(f"No student found with roll number '{args.roll}'.")
        sys.exit(1)


def cmd_list_students(args):
    rows = db.list_students()
    if not rows:
        print("No students registered yet.")
        return
    print(f"{'Roll No':<10}{'Name':<25}{'Class/Section':<15}")
    print("-" * 50)
    for r in rows:
        print(f"{r['roll_no']:<10}{r['name']:<25}{(r['class_section'] or '-'):<15}")


def cmd_mark(args):
    status = args.status.upper()
    if status not in ("P", "A", "L"):
        print("Status must be one of: P (present), A (absent), L (late).")
        sys.exit(1)
    ok, msg = db.mark_attendance(args.roll, args.date, status)
    print(msg)
    sys.exit(0 if ok else 1)


def cmd_view(args):
    rows = db.get_attendance_by_date(args.date)
    if not rows:
        print("No students registered yet.")
        return
    print(f"Attendance for {args.date}")
    print(f"{'Roll No':<10}{'Name':<25}{'Status':<12}")
    print("-" * 47)
    for r in rows:
        print(f"{r['roll_no']:<10}{r['name']:<25}{STATUS_LABELS[r['status']]:<12}")


def cmd_history(args):
    rows = db.get_attendance_by_student(args.roll)
    student = db.get_student_by_roll(args.roll)
    if student is None:
        print(f"No student found with roll number '{args.roll}'.")
        sys.exit(1)
    print(f"Attendance history for {student['name']} ({args.roll})")
    if not rows:
        print("No attendance marked yet.")
        return
    print(f"{'Date':<15}{'Status':<12}")
    print("-" * 27)
    for r in rows:
        print(f"{r['date']:<15}{STATUS_LABELS[r['status']]:<12}")


def cmd_report(args):
    report = db.get_summary_report()
    if not report:
        print("No students registered yet.")
        return
    print(f"{'Roll No':<10}{'Name':<20}{'Present':<9}{'Absent':<9}{'Late':<7}{'%':<8}")
    print("-" * 63)
    for r in report:
        print(f"{r['roll_no']:<10}{r['name']:<20}{r['present']:<9}{r['absent']:<9}"
              f"{r['late']:<7}{r['percentage']:<8}")


def cmd_export(args):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    if args.date:
        rows = db.get_attendance_by_date(args.date)
        filename = os.path.join(EXPORT_DIR, f"attendance_{args.date}.csv")
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Roll No", "Name", "Class/Section", "Status"])
            for r in rows:
                writer.writerow([r["roll_no"], r["name"], r["class_section"] or "",
                                  STATUS_LABELS[r["status"]]])
        print(f"Exported daily attendance to {filename}")
    else:
        report = db.get_summary_report()
        filename = os.path.join(EXPORT_DIR, "attendance_summary_report.csv")
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Roll No", "Name", "Class/Section", "Total Marked",
                              "Present", "Absent", "Late", "Percentage"])
            for r in report:
                writer.writerow([r["roll_no"], r["name"], r["class_section"] or "",
                                  r["total_marked"], r["present"], r["absent"],
                                  r["late"], r["percentage"]])
        print(f"Exported summary report to {filename}")


# ---------------------------------------------------------------------
# Interactive menu (used when no subcommand is given)
# ---------------------------------------------------------------------

def interactive_menu():
    menu = """
========================================
   ATTENDANCE MAKER SYSTEM
========================================
1. Add student
2. Remove student
3. List students
4. Mark attendance for a student
5. Mark attendance for the whole class (bulk, by date)
6. View attendance for a date
7. View attendance history for a student
8. View summary report
9. Export data to CSV
0. Exit
----------------------------------------
"""
    while True:
        print(menu)
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            roll = input("Roll number: ").strip()
            name = input("Name: ").strip()
            cls = input("Class/Section (optional): ").strip() or None
            ok, msg = db.add_student(roll, name, cls)
            print(msg)

        elif choice == "2":
            roll = input("Roll number to remove: ").strip()
            ok = db.remove_student(roll)
            print("Removed." if ok else "Student not found.")

        elif choice == "3":
            cmd_list_students(None)

        elif choice == "4":
            roll = input("Roll number: ").strip()
            d = input(f"Date [YYYY-MM-DD] (blank = today, {date.today()}): ").strip() or str(date.today())
            status = input("Status (P/A/L): ").strip().upper()
            ok, msg = db.mark_attendance(roll, d, status)
            print(msg)

        elif choice == "5":
            d = input(f"Date [YYYY-MM-DD] (blank = today, {date.today()}): ").strip() or str(date.today())
            students = db.list_students()
            if not students:
                print("No students registered yet.")
                continue
            for s in students:
                status = input(f"  {s['roll_no']} - {s['name']} (P/A/L): ").strip().upper()
                if status in ("P", "A", "L"):
                    db.mark_attendance(s["roll_no"], d, status)
                else:
                    print("  Skipped (invalid status).")
            print("Bulk attendance marking complete.")

        elif choice == "6":
            d = input(f"Date [YYYY-MM-DD] (blank = today, {date.today()}): ").strip() or str(date.today())
            args = argparse.Namespace(date=d)
            cmd_view(args)

        elif choice == "7":
            roll = input("Roll number: ").strip()
            args = argparse.Namespace(roll=roll)
            cmd_history(args)

        elif choice == "8":
            cmd_report(None)

        elif choice == "9":
            sub = input("Export (D)aily attendance or (S)ummary report? ").strip().upper()
            if sub == "D":
                d = input("Date [YYYY-MM-DD]: ").strip()
                args = argparse.Namespace(date=d)
            else:
                args = argparse.Namespace(date=None)
            cmd_export(args)

        elif choice == "0":
            print("Goodbye!")
            break

        else:
            print("Invalid choice, please try again.")


# ---------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Attendance Maker System — a CLI attendance management tool."
    )
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("add-student", help="Register a new student")
    p.add_argument("--roll", required=True, help="Unique roll number")
    p.add_argument("--name", required=True, help="Student name")
    p.add_argument("--class", dest="class_section", default=None, help="Class or section")
    p.set_defaults(func=cmd_add_student)

    p = sub.add_parser("remove-student", help="Remove a student")
    p.add_argument("--roll", required=True)
    p.set_defaults(func=cmd_remove_student)

    p = sub.add_parser("list-students", help="List all registered students")
    p.set_defaults(func=cmd_list_students)

    p = sub.add_parser("mark", help="Mark attendance for one student on one date")
    p.add_argument("--roll", required=True)
    p.add_argument("--date", required=True, help="Format YYYY-MM-DD")
    p.add_argument("--status", required=True, help="P (present) / A (absent) / L (late)")
    p.set_defaults(func=cmd_mark)

    p = sub.add_parser("view", help="View attendance for all students on a given date")
    p.add_argument("--date", required=True, help="Format YYYY-MM-DD")
    p.set_defaults(func=cmd_view)

    p = sub.add_parser("history", help="View attendance history for one student")
    p.add_argument("--roll", required=True)
    p.set_defaults(func=cmd_history)

    p = sub.add_parser("report", help="View attendance summary/percentage report for all students")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("export", help="Export attendance data to CSV")
    p.add_argument("--date", default=None,
                    help="Export a specific date's attendance. Omit to export the full summary report.")
    p.set_defaults(func=cmd_export)

    return parser


def main():
    db.init_db()
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        interactive_menu()
        return

    args.func(args)


if __name__ == "__main__":
    main()
