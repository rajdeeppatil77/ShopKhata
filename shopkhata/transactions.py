import math
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from shopkhata.auth import login_required
from shopkhata import models
from shopkhata.utils import today_str

transactions = Blueprint('transactions', __name__, url_prefix='/transactions')
bp = transactions


MAX_AMOUNT = 10_000_000  # sanity cap (₹1 crore) to catch typos


def _parse_amount(amount_str, label):
    """Return (amount, error). Rejects blank, non-numeric, nan/inf, <=0 and absurd values."""
    if not amount_str:
        return None, f'{label} is required.'
    try:
        amount = float(amount_str)
    except ValueError:
        return None, 'Amount must be a valid number.'
    if not math.isfinite(amount):
        return None, 'Amount must be a valid number.'
    if amount <= 0:
        return None, f'{label} must be greater than 0.'
    if amount > MAX_AMOUNT:
        return None, 'Amount is too large. Please check the number.'
    return round(amount, 2), None


def _check_date(txn_date):
    """Return an error string if txn_date is not a valid YYYY-MM-DD date."""
    try:
        datetime.strptime(txn_date, '%Y-%m-%d')
    except ValueError:
        return 'Date is not valid.'
    return None


def _get_customers_with_balance(user_id):
    """Return list of customer dicts enriched with their current balance."""
    customers = models.get_customers(user_id)
    result = []
    for c in customers:
        balance = models.get_customer_balance(c['id'], user_id)
        result.append({**dict(c), 'balance': balance})
    return result


@transactions.route('/credit/add', methods=['GET', 'POST'])
@transactions.route('/add_credit', methods=['GET', 'POST'])
@login_required
def add_credit():
    user_id = session['user_id']
    customers = _get_customers_with_balance(user_id)

    if request.method == 'POST':
        customer_id = request.form.get('customer_id', '').strip()
        description = request.form.get('description', '').strip()
        amount_str = request.form.get('amount', '').strip()
        txn_date = request.form.get('txn_date', '').strip()
        notes = request.form.get('notes', '').strip()

        errors = []

        if not customer_id:
            errors.append('Customer is required.')
        else:
            try:
                cid = int(customer_id)
                customer = models.get_customer(cid, user_id)
                if customer is None:
                    errors.append('Selected customer not found in your shop account.')
            except ValueError:
                errors.append('Invalid customer ID.')

        if not description:
            description = 'Goods on credit'  # optional: Ravi should not have to type at the counter
        if len(description) > 200:
            errors.append('Description must be at most 200 characters.')

        amount, amt_err = _parse_amount(amount_str, 'Credit amount')
        if amt_err:
            errors.append(amt_err)

        if not txn_date:
            txn_date = today_str()
        date_err = _check_date(txn_date)
        if date_err:
            errors.append(date_err)

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template(
                'transactions/add_credit.html',
                customers=customers,
                selected_customer_id=customer_id,
                form=request.form,
            )

        try:
            models.add_credit_transaction(
                customer_id=int(customer_id),
                user_id=user_id,
                description=description,
                amount=amount,
                txn_date=txn_date,
                notes=notes or None,
            )
            flash('Credit entry recorded successfully.', 'success')
            return redirect(url_for('customers.detail', id=int(customer_id)))
        except ValueError as ex:
            flash(str(ex), 'danger')
            return render_template(
                'transactions/add_credit.html',
                customers=customers,
                selected_customer_id=customer_id,
                form=request.form,
            )

    # GET
    selected_customer_id = request.args.get('customer_id', '')
    return render_template(
        'transactions/add_credit.html',
        customers=customers,
        selected_customer_id=selected_customer_id,
        form={},
    )


@transactions.route('/payment/add', methods=['GET', 'POST'])
@transactions.route('/add_payment', methods=['GET', 'POST'])
@login_required
def add_payment():
    user_id = session['user_id']
    customers = _get_customers_with_balance(user_id)

    if request.method == 'POST':
        customer_id = request.form.get('customer_id', '').strip()
        amount_str = request.form.get('amount', '').strip()
        txn_date = request.form.get('txn_date', '').strip()
        notes = request.form.get('notes', '').strip()

        errors = []
        customer = None

        if not customer_id:
            errors.append('Customer is required.')
        else:
            try:
                cid = int(customer_id)
                customer = models.get_customer(cid, user_id)
                if customer is None:
                    errors.append('Selected customer not found in your shop account.')
            except ValueError:
                errors.append('Invalid customer ID.')

        amount, amt_err = _parse_amount(amount_str, 'Payment amount')
        if amt_err:
            errors.append(amt_err)

        if not txn_date:
            txn_date = today_str()
        date_err = _check_date(txn_date)
        if date_err:
            errors.append(date_err)

        if customer and amount is not None:
            balance = models.get_customer_balance(customer['id'], user_id)
            if balance <= 0.001:
                errors.append(f"Customer '{customer['full_name']}' currently has no outstanding balance (₹0.00).")
            elif amount > round(balance, 2) + 0.01:
                errors.append(f"Payment amount ₹{amount:,.2f} exceeds outstanding balance ₹{balance:,.2f}.")

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template(
                'transactions/add_payment.html',
                customers=customers,
                selected_customer_id=customer_id,
                form=request.form,
            )

        try:
            models.add_payment_transaction(
                customer_id=int(customer_id),
                user_id=user_id,
                amount=amount,
                txn_date=txn_date,
                notes=notes or None,
            )
            flash('Payment recorded successfully.', 'success')
            return redirect(url_for('customers.detail', id=int(customer_id)))
        except ValueError as ex:
            flash(str(ex), 'danger')
            return render_template(
                'transactions/add_payment.html',
                customers=customers,
                selected_customer_id=customer_id,
                form=request.form,
            )

    # GET
    selected_customer_id = request.args.get('customer_id', '')
    return render_template(
        'transactions/add_payment.html',
        customers=customers,
        selected_customer_id=selected_customer_id,
        form={},
    )
