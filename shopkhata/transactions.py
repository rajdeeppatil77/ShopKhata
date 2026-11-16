from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from shopkhata.auth import login_required
from shopkhata import models

transactions = Blueprint('transactions', __name__, url_prefix='/transactions')
bp = transactions


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
        if not description:
            errors.append('Description is required.')
        elif len(description) > 200:
            errors.append('Description must be at most 200 characters.')
        if not amount_str:
            errors.append('Amount is required.')
        else:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    errors.append('Amount must be greater than 0.')
            except ValueError:
                errors.append('Amount must be a valid number.')
                amount = None
        if not txn_date:
            errors.append('Transaction date is required.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template(
                'transactions/add_credit.html',
                customers=customers,
                selected_customer_id=customer_id,
                form=request.form,
            )

        models.add_credit_transaction(
            customer_id=int(customer_id),
            user_id=user_id,
            description=description,
            amount=float(amount_str),
            txn_date=txn_date,
            notes=notes or None,
        )
        flash('Credit entry added successfully.', 'success')
        return redirect(url_for('customers.detail', id=int(customer_id)))

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

        if not customer_id:
            errors.append('Customer is required.')
        if not amount_str:
            errors.append('Amount is required.')
        else:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    errors.append('Amount must be greater than 0.')
            except ValueError:
                errors.append('Amount must be a valid number.')
                amount = None
        if not txn_date:
            errors.append('Transaction date is required.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template(
                'transactions/add_payment.html',
                customers=customers,
                selected_customer_id=customer_id,
                form=request.form,
            )

        # Balance check
        balance = models.get_customer_balance(int(customer_id), user_id)
        amount = float(amount_str)
        if amount > balance:
            flash(
                f'Payment amount \u20b9{amount:,.2f} exceeds outstanding balance \u20b9{balance:,.2f}.',
                'danger',
            )
            return redirect(
                url_for('transactions.add_payment', customer_id=customer_id)
            )

        models.add_payment_transaction(
            customer_id=int(customer_id),
            user_id=user_id,
            amount=amount,
            txn_date=txn_date,
            notes=notes or None,
        )
        flash('Payment recorded successfully.', 'success')
        return redirect(url_for('customers.detail', id=int(customer_id)))

    # GET
    selected_customer_id = request.args.get('customer_id', '')
    return render_template(
        'transactions/add_payment.html',
        customers=customers,
        selected_customer_id=selected_customer_id,
        form={},
    )
