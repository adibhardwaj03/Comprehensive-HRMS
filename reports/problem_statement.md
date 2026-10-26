
# Problem Statement: Comprehensive HR Management System

## Background
Human resource teams maintain employee records and coordinate attendance, leave, recruitment, payroll and workforce reporting. When these activities are spread across disconnected spreadsheets, it becomes harder to keep records consistent and produce timely summaries.

## Problem
The project aims to build a local web application that brings core HR workflows into one place. It should provide structured employee records, track candidate applications, record attendance, manage leave decisions, calculate simple monthly payroll figures and summarize workforce information.

## Objectives
1. Maintain searchable employee records.
2. Record attendance by employee and date.
3. Submit leave requests and allow HR users to approve or reject pending requests.
4. Track candidates through recruitment stages.
5. Store monthly payroll calculations with a clear breakdown.
6. Provide department, grade, attendance, leave and recruitment summaries.
7. Use anonymised historical data for exploratory analysis and, if validated, attrition modelling.
8. Test core workflows and document limitations and ethical safeguards.

## Scope
The prototype is intended for local demonstration and educational evaluation. It does not replace a production HR information system or provide legally compliant payroll processing. Access to HR actions is restricted to authenticated HR/Admin users. Demo data must be anonymised.

## Success criteria
- Application starts using documented Windows instructions.
- User can sign in and reach the dashboard.
- HR/Admin can create and update employee records.
- Attendance, leave, recruitment and payroll records persist in the configured database.
- Dashboard and analytics pages display database-backed summaries.
- JSON API endpoints return valid responses for authenticated users.
- Automated tests cover authentication and key data flows.
- Deliverables include the cleaned dataset, data dictionary, EDA notebook, report, and demo instructions.
