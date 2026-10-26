
import pytest
from app import app, db, User, Employee


@pytest.fixture()
def client(tmp_path):
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'test_hrms.db'}",
        SECRET_KEY="test-secret"
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(username="admin", role="Admin")
        admin.set_password("TestPassword123!")
        db.session.add(admin)
        db.session.commit()
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.session.remove()
        db.drop_all()


def login(client):
    return client.post("/login", data={
        "username": "admin",
        "password": "TestPassword123!"
    }, follow_redirects=True)


def test_dashboard_requires_login(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_admin_can_login_and_view_dashboard(client):
    response = login(client)
    assert response.status_code == 200
    assert b"HR overview" in response.data


def test_admin_can_create_employee(client):
    login(client)
    response = client.post("/employees/new", data={
        "emp_id": "EMP9001",
        "name": "Sample Employee",
        "email": "sample@example.invalid",
        "department": "Engineering",
        "grade": "L2",
        "join_date": "2025-01-15",
        "monthly_salary_inr": "65000",
        "employment_status": "Active"
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        employee = Employee.query.filter_by(emp_id="EMP9001").first()
        assert employee is not None
        assert employee.monthly_salary_inr == 65000


def test_employee_api_requires_login(client):
    response = client.get("/api/employees")
    assert response.status_code == 302
