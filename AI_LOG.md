AI Development Log – ShopKhata

1. Overview

ShopKhata was developed with assistance from Google Antigravity and AI coding tools.

AI was used as a development assistant for code suggestions, debugging, reviewing implementation approaches and improving documentation. The generated suggestions were reviewed, tested and modified during development.

The project was not treated as a one-click AI-generated solution. Development involved understanding requirements, checking application behaviour, resolving issues and verifying important features.

2. Areas Where AI Assistance Was Used

AI assistance was used in the following areas:

* Project Structure: Suggestions for organizing the Flask application into separate modules.
* Database: Help with SQLite queries, database relationships and transaction handling.
* Frontend: Assistance with Bootstrap layouts, templates and responsive styling.
* Features: Suggestions for customer management, credit entries, payments, ledgers and reports.
* Debugging: Help investigating Python, Flask, SQLite and JavaScript errors.
* Documentation: Assistance preparing the README and technical documentation.

3. Examples of Issues Addressed During Development

The following issues were identified and addressed with development and AI-assisted debugging:

Issue	Resolution
Duplicate transaction IDs during data seeding	Improved ID generation and added a database uniqueness constraint.
SQLite ordering issue with UNION ALL	Wrapped the combined query in a subquery before applying ordering.
Missing CSRF token in forms	Configured Flask-WTF CSRF protection.
Registration form fields missing	Updated the login template to support registration fields.
Floating-point inconsistencies	Improved rounding of financial totals.
Customer ownership validation	Added checks to ensure transactions belong to the logged-in user’s customers.
Invalid transaction amounts	Added validation for empty, non-numeric and non-finite values.
Incorrect date near midnight	Updated date handling to use local dates instead of relying on UTC conversion.
Unsafe redirect handling	Restricted redirects to safe local paths.
Development secret key configuration	Added persistent secret-key storage for local application use.

These fixes were reviewed and tested as part of development.

4. Development Decisions

Some suggestions were reviewed and not adopted.

For example, instead of storing a separately updated outstanding balance for every customer, ShopKhata calculates it from transaction records:

Outstanding Balance = Total Credit − Total Payments

This avoids maintaining a second balance value that could become inconsistent with the transaction history.

The application also uses parameterized SQL queries rather than building database queries by directly inserting user input.

5. Testing and Verification

The application was tested during development for:

* User registration and login.
* Customer creation and management.
* Credit and payment entries.
* Customer ledger and running balance.
* Dashboard and monthly reports.
* CSV export.
* User data isolation.
* Input validation and security-related cases.
* Desktop and mobile layouts.

The project includes an automated test suite. The reported test count is 18.

Run the tests using:

python -m unittest discover -s tests

6. Developer Responsibility

AI assistance helped speed up development and investigate technical problems. However, AI-generated suggestions were not accepted blindly.

Application behaviour, database operations and important changes were reviewed and tested during development. Technical decisions were made based on the project’s requirements.

The final responsibility for the code, testing, documentation and project demonstration remains with the developer.

⸻

Project: ShopKhata – Shop Credit Tracker
Developer: Rajdeep Patil
AI Development Assistant: Google Antigravity