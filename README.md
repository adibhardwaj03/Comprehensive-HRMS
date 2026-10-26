<<<<<<< HEAD

# Comprehensive HR Management System

A local HR management application built with Flask, SQLAlchemy, MySQL-compatible database configuration, Bootstrap, Pandas and scikit-learn-ready analytics. It is designed for a student project and uses anonymised sample records.

## Features

- Login with password hashing and role checks for HR/Admin actions
- Employee directory, search, add/edit and active/inactive status
- Daily attendance records
- Leave request submission and HR approval/rejection
- Candidate application tracking and hiring-stage updates
- Monthly payroll records with basic gross/net calculations
- Dashboard and HR analytics
- Authenticated JSON endpoints and employee CSV export
- Dataset import command for the provided anonymised dataset
- Pytest starter tests

## Requirements

- Python 3.10 or later
- Windows 10/11 and VS Code
- SQLite (default) or MySQL 8+

## Run on Windows

Open PowerShell in this project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:HRMS_SECRET_KEY = "replace-this-with-a-long-random-secret"
$env:HRMS_ADMIN_PASSWORD = "ChangeThisBeforeUse123!"
flask --app app init-db
python app.py
```

Open http://127.0.0.1:5000. Sign in with username `admin` and the password set in `HRMS_ADMIN_PASSWORD`. If that variable was not set before initialization, the development default is `ChangeMe123!`. Change it before any real use.

The application creates its tables automatically. The `flask init-db` command also creates the initial administrator when one does not exist.

## Use MySQL

1. Install and start MySQL Server.
2. Create a database and a restricted application user:

```sql
CREATE DATABASE hrms CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'hrms_user'@'localhost' IDENTIFIED BY 'choose-a-strong-password';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX ON hrms.* TO 'hrms_user'@'localhost';
FLUSH PRIVILEGES;
```

3. Set the connection string in PowerShell:

```powershell
$env:DATABASE_URL = "mysql+pymysql://hrms_user:choose-a-strong-password@localhost/hrms"
```

Restart the app after setting the environment variable.

## Import the anonymised dataset

The sample dataset contains historical HR attributes, including an `attrition` label. The app's employee table represents current demo records, so importing the dataset creates anonymised employee names and placeholder `.invalid` email addresses. It does not treat the historical attrition label as a current employment status.

```powershell
flask --app app import-dataset
```

Set `HRMS_DATASET_PATH` if your cleaned dataset is in a different location.

## Run tests

```powershell
pytest -q
```

## Project structure

```text
Comprehensive-HRMS-Complete/
├── app.py
├── requirements.txt
├── .env.example
├── data/
│   ├── data_dictionary.csv
│   ├── dataset.csv
│   └── processed/cleaned_dataset.csv
├── notebook/employee_data_exploration.ipynb
├── reports/problem_statement.md
├── tests/test_app.py
├── templates/
└── static/css/style.css
```

## Important limitations

- This is a local academic prototype, not a production HR/payroll platform.
- Payroll is a transparent basic calculation (`base salary + bonus - deductions`); it does not implement statutory tax, PF, ESI, or legal payroll rules.
- Demo data must remain anonymised. Do not enter real employee personal or payroll data.
- Before public deployment, add CSRF protection, rate limiting, secure cookie settings, audit logging, database migrations, password reset, stronger role design and production server configuration.
- Attrition analytics should be evaluated for class imbalance, leakage, bias and calibration before use. A model score must not be used as an automatic employment decision.
=======
# Comprehensive-HRMS
>>>>>>> origin/main
git add README.mdgit status

## Employee self-service and HR workflows

The HR/Admin attendance screen is read-only. Employees can submit attendance correction requests, and HR/Admin can approve or reject them. Approving a request updates the attendance record and records the decision status.

Employees with portal accounts can submit their own leave requests and view their own request history. HR/Admin users can view all leave requests and approve or reject pending requests.

To create an employee portal account, sign in as HR/Admin, open Employees, and use the **Create employee portal account** form. Choose the employee, a unique username, and a strong temporary password of at least 12 characters. Share credentials securely. Do not use real employee data until database persistence and access controls have been verified.

The app calls `db.create_all()` on startup, so the new employee-account and attendance-correction tables are created automatically. Existing records are not intentionally deleted by this change. Back up your database before deploying changes to a production-like environment.
