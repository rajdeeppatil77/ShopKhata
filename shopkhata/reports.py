import csv
import io

from flask import Blueprint, render_template, session, make_response
from shopkhata.auth import login_required
from shopkhata import models

reports = Blueprint('reports', __name__, url_prefix='/reports')
bp = reports


@reports.route('/')
@login_required
def index():
    user_id = session['user_id']
    report_data = models.get_report_data(user_id)
    return render_template('reports/index.html', report_data=report_data)


@reports.route('/csv')
@login_required
def download_csv():
    user_id = session['user_id']
    report_data = models.get_report_data(user_id)
    customers = report_data.get('customer_balances', [])

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'Customer Name',
        'Phone',
        'Address',
        'Total Credit (INR)',
        'Total Paid (INR)',
        'Outstanding Balance (INR)',
    ])

    for c in customers:
        writer.writerow([
            c.get('full_name') or c.get('customer_name', ''),
            c.get('phone', '') or '',
            c.get('address', '') or '',
            f"{c.get('total_credit', 0):.2f}",
            f"{c.get('total_paid', 0):.2f}",
            f"{c.get('balance', 0):.2f}",
        ])

    totals = report_data.get('totals', {})
    writer.writerow([])
    writer.writerow([
        'TOTALS',
        '',
        '',
        f"{totals.get('total_credit', 0):.2f}",
        f"{totals.get('total_paid', 0):.2f}",
        f"{totals.get('total_outstanding', 0):.2f}",
    ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=shopkhata_credit_report.csv'
    return response
