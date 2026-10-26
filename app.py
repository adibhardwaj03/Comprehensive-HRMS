import os
from datetime import date, datetime
from functools import wraps

import pandas as pd
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, or_
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("HRMS_SECRET_KEY", "change-this-development-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///hrms.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="HR")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class EmployeeAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    employee = db.relationship("Employee", backref=db.backref("portal_account", uselist=False))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class AttendanceCorrectionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False)
    requested_status = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    employee = db.relationship("Employee", backref="attendance_correction_requests")


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    department = db.Column(db.String(80), nullable=False)
    grade = db.Column(db.String(20), nullable=False)
    join_date = db.Column(db.Date, nullable=False, default=date.today)
    monthly_salary_inr = db.Column(db.Float, nullable=False, default=0)
    employment_status = db.Column(db.String(20), nullable=False, default="Active")


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False, default="Present")
    employee = db.relationship("Employee", backref="attendance_records")
    __table_args__ = (db.UniqueConstraint("employee_id", "attendance_date"),)


class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    leave_type = db.Column(db.String(40), nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    employee = db.relationship("Employee", backref="leave_requests")


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    position = db.Column(db.String(120), nullable=False)
    application_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(30), nullable=False, default="Applied")


class Payroll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)
    pay_month = db.Column(db.String(7), nullable=False)
    base_salary = db.Column(db.Float, nullable=False)
    bonus = db.Column(db.Float, nullable=False, default=0)
    deductions = db.Column(db.Float, nullable=False, default=0)
    net_salary = db.Column(db.Float, nullable=False)
    generated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    employee = db.relationship("Employee", backref="payroll_records")
    __table_args__ = (db.UniqueConstraint("employee_id", "pay_month"),)



def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        is_regular_user = bool(session.get("user_id"))
        is_employee = (
            session.get("role") == "Employee"
            and bool(session.get("employee_id"))
        )

        if not is_regular_user and not is_employee:
            return redirect(url_for("login", next=request.path))

        return view(*args, **kwargs)

    return wrapped

def hr_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if session.get("role") not in {"HR", "Admin"}:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_user():
    return {"current_username": session.get("username"), "current_role": session.get("role")}


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session.clear()
            session.update(user_id=user.id, username=user.username, role=user.role)
            return redirect(request.args.get("next") or url_for("dashboard"))

        employee_account = EmployeeAccount.query.filter_by(username=username).first()
       
        if employee_account and employee_account.check_password(password):
            session.clear()
            session.update(
                username=employee_account.username,
                role="Employee",
                employee_id=employee_account.employee_id
            )
            return redirect(url_for("leave"))

        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    if session.get("role") == "Employee":
        return redirect(url_for("leave"))
    today = date.today()
    active_count = Employee.query.filter_by(employment_status="Active").count()
    pending_leaves = LeaveRequest.query.filter_by(status="Pending").count()
    open_candidates = Candidate.query.filter(Candidate.status.in_(["Applied", "Screening", "Interview"])).count()
    month_payroll = db.session.query(func.coalesce(func.sum(Payroll.net_salary), 0)).filter_by(
        pay_month=today.strftime("%Y-%m")
    ).scalar()
    department_rows = db.session.query(Employee.department, func.count(Employee.id)).group_by(Employee.department).all()
    attrition_rate = None
    return render_template(
        "dashboard.html", active_count=active_count, pending_leaves=pending_leaves,
        open_candidates=open_candidates, month_payroll=month_payroll,
        department_rows=department_rows, today=today, attrition_rate=attrition_rate
    )


@app.route("/employees")
@hr_required
def employees():
    search = request.args.get("q", "").strip()
    query = Employee.query
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(Employee.emp_id.ilike(pattern), Employee.name.ilike(pattern),
                                 Employee.department.ilike(pattern), Employee.email.ilike(pattern)))
    records = query.order_by(Employee.name).all()
    return render_template("employees.html", employees=records, search=search)


@app.route("/employees/new", methods=["GET", "POST"])
@hr_required
def employee_new():
    if request.method == "POST":
        try:
            record = Employee(
                emp_id=request.form["emp_id"].strip(),
                name=request.form["name"].strip(),
                email=request.form["email"].strip().lower(),
                department=request.form["department"].strip(),
                grade=request.form["grade"].strip(),
                join_date=date.fromisoformat(request.form["join_date"]),
                monthly_salary_inr=float(request.form["monthly_salary_inr"]),
                employment_status=request.form.get("employment_status", "Active")
            )
            if record.monthly_salary_inr < 0:
                raise ValueError("Salary cannot be negative.")
            db.session.add(record)
            db.session.commit()
            flash("Employee added successfully.", "success")
            return redirect(url_for("employees"))
        except (ValueError, KeyError) as error:
            db.session.rollback()
            flash(f"Please check the form values. {error}", "danger")
        except Exception:
            db.session.rollback()
            flash("Could not save employee. Check that employee ID and email are unique.", "danger")
    return render_template("employee_form.html", employee=None)


@app.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
@hr_required
def employee_edit(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    if request.method == "POST":
        try:
            employee.name = request.form["name"].strip()
            employee.email = request.form["email"].strip().lower()
            employee.department = request.form["department"].strip()
            employee.grade = request.form["grade"].strip()
            employee.join_date = date.fromisoformat(request.form["join_date"])
            employee.monthly_salary_inr = float(request.form["monthly_salary_inr"])
            employee.employment_status = request.form.get("employment_status", "Active")
            if employee.monthly_salary_inr < 0:
                raise ValueError("Salary cannot be negative.")
            db.session.commit()
            flash("Employee details updated.", "success")
            return redirect(url_for("employees"))
        except Exception:
            db.session.rollback()
            flash("Could not update employee. Check the entered values and email uniqueness.", "danger")
    return render_template("employee_form.html", employee=employee)


@app.route("/employees/<int:employee_id>/account", methods=["POST"])
@hr_required
def employee_account_create(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if len(username) < 3 or len(password) < 12:
        flash("Choose a username with at least 3 characters and a password with at least 12 characters.", "danger")
        return redirect(url_for("employees"))

    if EmployeeAccount.query.filter_by(employee_id=employee.id).first():
        flash("This employee already has a portal account.", "warning")
        return redirect(url_for("employees"))

    if User.query.filter_by(username=username).first() or EmployeeAccount.query.filter_by(username=username).first():
        flash("That username is already in use.", "danger")
        return redirect(url_for("employees"))

    account = EmployeeAccount(employee_id=employee.id, username=username)
    account.set_password(password)
    db.session.add(account)
    db.session.commit()
    flash("Employee portal account created. Share the login details with the employee securely.", "success")
    return redirect(url_for("employees"))


@app.route("/employees/<int:employee_id>/status", methods=["POST"])
@hr_required
def employee_status(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    employee.employment_status = "Inactive" if employee.employment_status == "Active" else "Active"
    db.session.commit()
    flash("Employment status updated.", "success")
    return redirect(url_for("employees"))


@app.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    role = session.get("role")

    if role == "Employee":
        employee_id = session.get("employee_id")
        if not employee_id:
            abort(403)

        if request.method == "POST":
            try:
                attendance_date = date.fromisoformat(request.form["attendance_date"])
                requested_status = request.form["requested_status"]
                reason = request.form["reason"].strip()
                if requested_status not in {"Present", "Absent", "Work From Home"}:
                    raise ValueError("Invalid requested status.")
                if not reason:
                    raise ValueError("Please explain the attendance correction.")
                correction = AttendanceCorrectionRequest(
                    employee_id=employee_id,
                    attendance_date=attendance_date,
                    requested_status=requested_status,
                    reason=reason
                )
                db.session.add(correction)
                db.session.commit()
                flash("Attendance correction request submitted to HR.", "success")
                return redirect(url_for("attendance"))
            except (ValueError, KeyError):
                db.session.rollback()
                flash("Please check the date, requested status and reason.", "danger")

        corrections = AttendanceCorrectionRequest.query.filter_by(
            employee_id=employee_id
        ).order_by(AttendanceCorrectionRequest.created_at.desc()).all()
        records = Attendance.query.filter_by(employee_id=employee_id).order_by(
            Attendance.attendance_date.desc()
        ).all()
        return render_template(
            "attendance.html", employee_view=True, records=records,
            correction_requests=corrections, selected_date=date.today(),
            employees=[], pending_corrections=[]
        )

    if role not in {"HR", "Admin"}:
        abort(403)

    selected_date = request.args.get("date", date.today().isoformat())
    try:
        parsed_date = date.fromisoformat(selected_date)
    except ValueError:
        parsed_date = date.today()

    records = Attendance.query.filter_by(attendance_date=parsed_date).join(Employee).order_by(Employee.name).all()
    pending_corrections = AttendanceCorrectionRequest.query.filter_by(status="Pending").join(
        Employee
    ).order_by(AttendanceCorrectionRequest.created_at.asc()).all()
    return render_template(
        "attendance.html", employee_view=False, employees=[],
        records=records, selected_date=parsed_date,
        correction_requests=[], pending_corrections=pending_corrections
    )


@app.route("/attendance/corrections/<int:request_id>/decision", methods=["POST"])
@hr_required
def attendance_correction_decision(request_id):
    correction = AttendanceCorrectionRequest.query.get_or_404(request_id)
    decision = request.form.get("decision")

    if correction.status != "Pending" or decision not in {"Approved", "Rejected"}:
        flash("This correction request can no longer be changed.", "warning")
        return redirect(url_for("attendance"))

    if decision == "Approved":
        record = Attendance.query.filter_by(
            employee_id=correction.employee_id,
            attendance_date=correction.attendance_date
        ).first()
        if record:
            record.status = correction.requested_status
        else:
            record = Attendance(
                employee_id=correction.employee_id,
                attendance_date=correction.attendance_date,
                status=correction.requested_status
            )
            db.session.add(record)

    correction.status = decision
    correction.reviewed_at = datetime.utcnow()
    db.session.commit()
    flash(f"Attendance correction {decision.lower()}.", "success")
    return redirect(url_for("attendance"))


@app.route("/leave", methods=["GET", "POST"])
@login_required
def leave():
    role = session.get("role")

    if role == "Employee":
        employee_id = session.get("employee_id")
        if not employee_id:
            abort(403)

        if request.method == "POST":
            try:
                start_date = date.fromisoformat(request.form["start_date"])
                end_date = date.fromisoformat(request.form["end_date"])
                leave_type = request.form["leave_type"]
                reason = request.form["reason"].strip()
                if end_date < start_date:
                    raise ValueError("End date cannot be earlier than start date.")
                if leave_type not in {"Annual", "Sick", "Personal", "Unpaid"}:
                    raise ValueError("Invalid leave type.")
                if not reason:
                    raise ValueError("Please provide a reason.")
                request_record = LeaveRequest(
                    employee_id=employee_id,
                    start_date=start_date,
                    end_date=end_date,
                    leave_type=leave_type,
                    reason=reason
                )
                db.session.add(request_record)
                db.session.commit()
                flash("Leave request submitted to HR for review.", "success")
                return redirect(url_for("leave"))
            except (ValueError, KeyError):
                db.session.rollback()
                flash("Could not submit leave request. Check the dates and details.", "danger")

        requests = LeaveRequest.query.filter_by(employee_id=employee_id).order_by(
            LeaveRequest.created_at.desc()
        ).all()
        return render_template("leave.html", employee_view=True, leave_requests=requests)

    if role not in {"HR", "Admin"}:
        abort(403)

    if request.method == "POST":
        abort(403)

    requests = LeaveRequest.query.join(Employee).order_by(LeaveRequest.created_at.desc()).all()
    return render_template("leave.html", employee_view=False, leave_requests=requests)


@app.route("/leave/<int:request_id>/decision", methods=["POST"])
@hr_required
def leave_decision(request_id):
    leave_request = LeaveRequest.query.get_or_404(request_id)
    decision = request.form.get("decision")
    if leave_request.status != "Pending" or decision not in {"Approved", "Rejected"}:
        flash("This leave request cannot be changed.", "warning")
    else:
        leave_request.status = decision
        db.session.commit()
        flash(f"Leave request {decision.lower()}.", "success")
    return redirect(url_for("leave"))

@app.route("/recruitment", methods=["GET", "POST"])
@hr_required
def recruitment():
    if request.method == "POST":
        candidate = Candidate(
            full_name=request.form["full_name"].strip(),
            email=request.form["email"].strip().lower(),
            position=request.form["position"].strip(),
            status="Applied"
        )
        db.session.add(candidate)
        db.session.commit()
        flash("Candidate application added.", "success")
        return redirect(url_for("recruitment"))
    candidates = Candidate.query.order_by(Candidate.application_date.desc()).all()
    return render_template("recruitment.html", candidates=candidates)


@app.route("/recruitment/<int:candidate_id>/status", methods=["POST"])
@hr_required
def candidate_status(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    status = request.form.get("status")
    if status not in {"Applied", "Screening", "Interview", "Offered", "Hired", "Rejected"}:
        abort(400)
    candidate.status = status
    db.session.commit()
    flash("Candidate status updated.", "success")
    return redirect(url_for("recruitment"))


@app.route("/payroll", methods=["GET", "POST"])
@hr_required
def payroll():
    if request.method == "POST":
        try:
            employee_id = int(request.form["employee_id"])
            pay_month = request.form["pay_month"]
            base_salary = float(request.form["base_salary"])
            bonus = float(request.form.get("bonus") or 0)
            deductions = float(request.form.get("deductions") or 0)
            if min(base_salary, bonus, deductions) < 0 or deductions > base_salary + bonus:
                raise ValueError("Salary values are invalid.")
            existing = Payroll.query.filter_by(employee_id=employee_id, pay_month=pay_month).first()
            if existing:
                raise ValueError("Payroll already exists for this employee and month.")
            record = Payroll(employee_id=employee_id, pay_month=pay_month, base_salary=base_salary,
                             bonus=bonus, deductions=deductions, net_salary=base_salary + bonus - deductions)
            db.session.add(record)
            db.session.commit()
            flash("Payroll record generated.", "success")
            return redirect(url_for("payroll"))
        except Exception as error:
            db.session.rollback()
            flash(f"Could not generate payroll. {error}", "danger")
    records = Payroll.query.join(Employee).order_by(Payroll.pay_month.desc(), Employee.name).all()
    return render_template("payroll.html", employees=Employee.query.filter_by(employment_status="Active").order_by(Employee.name).all(),
                           payroll_records=records, current_month=date.today().strftime("%Y-%m"))


@app.route("/analytics")
@hr_required
def analytics():
    department_rows = db.session.query(Employee.department, func.count(Employee.id), func.avg(Employee.monthly_salary_inr)).group_by(Employee.department).all()
    grade_rows = db.session.query(Employee.grade, func.avg(Employee.monthly_salary_inr), func.count(Employee.id)).group_by(Employee.grade).order_by(Employee.grade).all()
    attendance_rows = db.session.query(Attendance.status, func.count(Attendance.id)).group_by(Attendance.status).all()
    leave_rows = db.session.query(LeaveRequest.status, func.count(LeaveRequest.id)).group_by(LeaveRequest.status).all()
    candidate_rows = db.session.query(Candidate.status, func.count(Candidate.id)).group_by(Candidate.status).all()
    return render_template("analytics.html", department_rows=department_rows, grade_rows=grade_rows,
                           attendance_rows=attendance_rows, leave_rows=leave_rows, candidate_rows=candidate_rows)


@app.route("/api/summary")
@hr_required
def api_summary():
    return jsonify({
        "active_employees": Employee.query.filter_by(employment_status="Active").count(),
        "pending_leave_requests": LeaveRequest.query.filter_by(status="Pending").count(),
        "candidates": Candidate.query.count(),
        "payroll_total_current_month": float(db.session.query(func.coalesce(func.sum(Payroll.net_salary), 0)).filter_by(
            pay_month=date.today().strftime("%Y-%m")).scalar())
    })


@app.route("/api/employees")
@hr_required
def api_employees():
    records = Employee.query.order_by(Employee.name).all()
    return jsonify([{
        "emp_id": record.emp_id, "name": record.name, "email": record.email,
        "department": record.department, "grade": record.grade,
        "monthly_salary_inr": record.monthly_salary_inr, "status": record.employment_status
    } for record in records])


@app.route("/export/employees.csv")
@hr_required
def export_employees():
    records = Employee.query.order_by(Employee.name).all()
    import csv
    from io import StringIO
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Employee ID", "Name", "Email", "Department", "Grade", "Join Date", "Monthly Salary INR", "Status"])
    for employee in records:
        writer.writerow([employee.emp_id, employee.name, employee.email, employee.department, employee.grade,
                         employee.join_date.isoformat(), employee.monthly_salary_inr, employee.employment_status])
    from flask import Response
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=employees.csv"})


@app.cli.command("init-db")
def init_db():
    db.create_all()

    user = User.query.filter_by(username="admin").first()

    if not user:
        user = User(username="admin", role="Admin")
        db.session.add(user)

    password = os.environ.get("HRMS_ADMIN_PASSWORD")

    if not password:
        raise ValueError("HRMS_ADMIN_PASSWORD is not configured.")

    user.set_password(password)
    db.session.commit()

    print("Admin password updated successfully.")


@app.cli.command("import-dataset")
def import_dataset():
    path = os.environ.get("HRMS_DATASET_PATH", "data/processed/cleaned_dataset.csv")
    if not os.path.exists(path):
        raise SystemExit(f"Dataset not found: {path}")
    data = pd.read_csv(path)
    added = 0
    for _, row in data.iterrows():
        if Employee.query.filter_by(emp_id=str(row["emp_id"])).first():
            continue
        employee = Employee(
            emp_id=str(row["emp_id"]),
            name=f"Employee {str(row['emp_id'])[-4:]}",
            email=f"{str(row['emp_id']).lower()}@example.invalid",
            department=str(row["department"]),
            grade=str(row["grade"]),
            join_date=pd.to_datetime(row["join_date"]).date(),
            monthly_salary_inr=float(row["monthly_salary_inr"]),
            employment_status="Active"
        )
        db.session.add(employee)
        added += 1
    db.session.commit()
    print(f"Imported {added} employee records. Attrition is retained in the analysis dataset, not treated as live employment status.")


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "1") == "1")
