"""
Employee Attendance Analysis System
Entry point - a menu-driven console application.

Run with:  python main.py
"""
import os
import sys
from datetime import date, datetime

from src import attendance_manager as att_mgr
from src import employee_manager as emp_mgr
from src import reports
from src import seed_data
from src import visualizations as viz
from src.db_connection import test_connection
from src.exceptions import (
    DuplicateAttendanceError,
    EmployeeNotFoundError,
    InvalidDateError,
    InvalidStatusError,
)
from src.utils import parse_date, print_table, prompt_nonempty

OUTPUT_REPORTS_DIR = os.path.join("outputs", "reports")
OUTPUT_CHARTS_DIR = os.path.join("outputs", "charts")


def ensure_output_dirs():
    os.makedirs(OUTPUT_REPORTS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_CHARTS_DIR, exist_ok=True)


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def pause():
    input("\nPress Enter to continue...")


# ---------------------------------------------------------------------------
# Employee menu
# ---------------------------------------------------------------------------
def menu_employees():
    while True:
        print("\n--- Manage Employees ---")
        print("1. Add Employee")
        print("2. View All Employees")
        print("3. Update Employee")
        print("4. Search Employee")
        print("5. Deactivate Employee (soft delete)")
        print("6. Delete Employee (permanent)")
        print("0. Back to Main Menu")
        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                code = prompt_nonempty("Employee code (e.g. EMP011): ")
                name = prompt_nonempty("Employee name: ")
                dept = prompt_nonempty("Department: ")
                new_id = emp_mgr.add_employee(code, name, dept)
                print(f"Added employee '{name}' with employee_id={new_id}.")
            elif choice == "2":
                rows = emp_mgr.get_all_employees(active_only=False)
                print_table(rows)
            elif choice == "3":
                emp_id = int(prompt_nonempty("Employee ID to update: "))
                field = prompt_nonempty("Field to update (employee_name/department/employee_code): ")
                value = prompt_nonempty(f"New value for {field}: ")
                emp_mgr.update_employee(emp_id, **{field: value})
                print("Employee updated.")
            elif choice == "4":
                kw = prompt_nonempty("Search keyword (name/code/department): ")
                rows = emp_mgr.search_employees(kw)
                print_table(rows)
            elif choice == "5":
                emp_id = int(prompt_nonempty("Employee ID to deactivate: "))
                emp_mgr.deactivate_employee(emp_id)
                print("Employee deactivated. Attendance history is kept.")
            elif choice == "6":
                emp_id = int(prompt_nonempty("Employee ID to permanently delete: "))
                confirm = input("This also deletes their attendance history. Type YES to confirm: ")
                if confirm == "YES":
                    emp_mgr.delete_employee(emp_id)
                    print("Employee deleted.")
                else:
                    print("Cancelled.")
            elif choice == "0":
                return
            else:
                print("Invalid option.")
        except (EmployeeNotFoundError, ValueError) as exc:
            print(f"Error: {exc}")
        pause()


# ---------------------------------------------------------------------------
# Attendance menu
# ---------------------------------------------------------------------------
def menu_attendance():
    while True:
        print("\n--- Record Attendance ---")
        print("1. Mark Attendance (single employee)")
        print("2. Bulk Mark Attendance (all active employees, one date)")
        print("3. View Attendance by Date")
        print("4. View Attendance by Employee")
        print("5. Update an Attendance Record")
        print("0. Back to Main Menu")
        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                emp_id = int(prompt_nonempty("Employee ID: "))
                date_str = prompt_nonempty("Date (YYYY-MM-DD): ")
                status = prompt_nonempty("Status (Present/Absent/Leave/Holiday or P/A/L/H): ")
                remarks = input("Remarks (optional): ").strip() or None
                att_mgr.mark_attendance(emp_id, date_str, status, remarks)
                print("Attendance recorded.")
            elif choice == "2":
                date_str = prompt_nonempty("Date for bulk marking (YYYY-MM-DD): ")
                employees = emp_mgr.get_all_employees(active_only=True)
                if not employees:
                    print("No active employees found. Add employees first.")
                else:
                    print("Enter status for each employee. Press Enter to default to Present.")
                    status_map = {}
                    for e in employees:
                        raw = input(f"  [{e['employee_code']}] {e['employee_name']}: ").strip() or "P"
                        status_map[e["employee_id"]] = raw
                    inserted, skipped = att_mgr.bulk_mark_attendance(date_str, status_map)
                    print(f"\nInserted {inserted} record(s).")
                    if skipped:
                        print(f"Skipped {len(skipped)} record(s) (already existed or invalid):")
                        for emp_id, reason in skipped:
                            print(f"  - employee_id {emp_id}: {reason}")
            elif choice == "3":
                date_str = prompt_nonempty("Date (YYYY-MM-DD): ")
                rows = att_mgr.get_attendance_by_date(date_str)
                print_table(rows)
            elif choice == "4":
                emp_id = int(prompt_nonempty("Employee ID: "))
                start = input("Start date (YYYY-MM-DD, optional): ").strip() or None
                end = input("End date (YYYY-MM-DD, optional): ").strip() or None
                rows = att_mgr.get_attendance_by_employee(emp_id, start, end)
                print_table(rows)
            elif choice == "5":
                emp_id = int(prompt_nonempty("Employee ID: "))
                date_str = prompt_nonempty("Date of the record to update (YYYY-MM-DD): ")
                new_status = prompt_nonempty("New status (Present/Absent/Leave/Holiday or P/A/L/H): ")
                att_mgr.update_attendance(emp_id, date_str, new_status)
                print("Attendance record updated.")
            elif choice == "0":
                return
            else:
                print("Invalid option.")
        except DuplicateAttendanceError as exc:
            print(f"Duplicate entry blocked: {exc}")
        except (EmployeeNotFoundError, InvalidStatusError, InvalidDateError, ValueError) as exc:
            print(f"Error: {exc}")
        pause()


# ---------------------------------------------------------------------------
# Reports menu
# ---------------------------------------------------------------------------
def _get_date_range(default_days: int = 60):
    start_str = input(f"Start date (YYYY-MM-DD) [default: {default_days} days ago]: ").strip()
    end_str = input("End date (YYYY-MM-DD) [default: today]: ").strip()
    end_date = parse_date(end_str) if end_str else date.today()
    if start_str:
        start_date = parse_date(start_str)
    else:
        start_date = date.fromordinal(end_date.toordinal() - default_days)
    return start_date, end_date


def menu_reports():
    while True:
        print("\n--- Reports & Analysis ---")
        print("1. Employee Attendance % Report")
        print("2. Monthly Summary Report")
        print("3. Department Summary Report")
        print("4. Absenteeism Chart")
        print("5. Department Summary Chart")
        print("6. Monthly Attendance Trend Chart")
        print("7. Reconciliation Check")
        print("0. Back to Main Menu")
        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                start_date, end_date = _get_date_range()
                df = reports.employee_attendance_percentage(start_date, end_date)
                print_table(df.to_dict("records"))
                path = os.path.join(OUTPUT_REPORTS_DIR, f"employee_attendance_pct_{timestamp()}.csv")
                df.to_csv(path, index=False)
                print(f"\nSaved to {path}")
            elif choice == "2":
                start_date, end_date = _get_date_range(default_days=90)
                df = reports.monthly_summary(start_date, end_date)
                print_table(df.to_dict("records"))
                path = os.path.join(OUTPUT_REPORTS_DIR, f"monthly_summary_{timestamp()}.csv")
                df.to_csv(path, index=False)
                print(f"\nSaved to {path}")
            elif choice == "3":
                start_date, end_date = _get_date_range()
                df = reports.department_summary(start_date, end_date)
                print_table(df.to_dict("records"))
                path = os.path.join(OUTPUT_REPORTS_DIR, f"department_summary_{timestamp()}.csv")
                df.to_csv(path, index=False)
                print(f"\nSaved to {path}")
            elif choice == "4":
                start_date, end_date = _get_date_range()
                df = reports.employee_attendance_percentage(start_date, end_date)
                path = os.path.join(OUTPUT_CHARTS_DIR, f"absenteeism_chart_{timestamp()}.png")
                viz.plot_absenteeism_chart(df, path)
                print(f"Chart saved to {path}")
            elif choice == "5":
                start_date, end_date = _get_date_range()
                df = reports.department_summary(start_date, end_date)
                path = os.path.join(OUTPUT_CHARTS_DIR, f"department_summary_chart_{timestamp()}.png")
                viz.plot_department_summary_chart(df, path)
                print(f"Chart saved to {path}")
            elif choice == "6":
                start_date, end_date = _get_date_range(default_days=90)
                df = reports.monthly_company_trend(start_date, end_date)
                path = os.path.join(OUTPUT_CHARTS_DIR, f"monthly_trend_chart_{timestamp()}.png")
                viz.plot_monthly_trend_chart(df, path)
                print(f"Chart saved to {path}")
            elif choice == "7":
                start_date, end_date = _get_date_range()
                result = reports.reconcile_with_source(start_date, end_date)
                status = "PASS" if result["reconciled"] else "FAIL"
                print(f"Reconciliation: {status}")
                print(f"  Raw attendance records : {result['raw_record_count']}")
                print(f"  Report record count     : {result['report_record_count']}")
            elif choice == "0":
                return
            else:
                print("Invalid option.")
        except (InvalidDateError, ValueError) as exc:
            print(f"Error: {exc}")
        pause()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main_menu():
    while True:
        print("\n==========================================")
        print(" Employee Attendance Analysis System")
        print("==========================================")
        print("1. Manage Employees")
        print("2. Record Attendance")
        print("3. Reports & Analysis")
        print("4. Load Sample Data")
        print("0. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            menu_employees()
        elif choice == "2":
            menu_attendance()
        elif choice == "3":
            menu_reports()
        elif choice == "4":
            confirm = input("Load sample employees + ~2 months of attendance? (y/n): ").strip().lower()
            if confirm == "y":
                e, a, s, en = seed_data.seed_all()
                print(f"Inserted {e} new employee(s) and {a} attendance record(s) ({s} to {en}).")
            pause()
        elif choice == "0":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid option.")


if __name__ == "__main__":
    ensure_output_dirs()
    print("Connecting to database...")
    try:
        test_connection()
    except RuntimeError as exc:
        print(str(exc))
        sys.exit(1)
    print("Connected.")
    main_menu()
