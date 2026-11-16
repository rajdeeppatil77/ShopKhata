"""
shopkhata/customers.py
Customer Management Blueprint for ShopKhata.

Routes (all protected with @login_required):
  GET  /customers/              — list customers (supports ?search=)
  GET  /customers/add           — add-customer form
  POST /customers/add           — create customer
  GET  /customers/<id>          — customer detail + ledger
  GET  /customers/<id>/edit     — edit form
  POST /customers/<id>/edit     — update customer
  GET  /customers/<id>/delete   — delete confirmation page
  POST /customers/<id>/delete   — delete customer (only if balance == 0)
"""

import re
from urllib.parse import quote

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from shopkhata import models
from shopkhata.auth import login_required
from shopkhata.utils import get_whatsapp_link

customers_bp = Blueprint("customers", __name__, url_prefix="/customers")
bp = customers_bp


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

PHONE_RE = re.compile(r"^\d{10}$")


def _validate_customer_form(full_name: str, phone: str, address: str) -> list:
    """Return a list of error strings; empty list means valid."""
    errors = []

    if not full_name:
        errors.append("Customer full name is required.")
    elif len(full_name) > 100:
        errors.append("Customer name must be 100 characters or fewer.")

    if phone and not PHONE_RE.match(phone):
        errors.append("Phone number must be exactly 10 digits (numbers only).")

    if address and len(address) > 200:
        errors.append("Address must be 200 characters or fewer.")

    return errors


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@customers_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]
    search = request.args.get("search", "").strip()

    if search:
        customers = models.search_customers(user_id, search)
    else:
        customers = models.get_customers_with_balance(user_id)

    return render_template("customers/index.html", customers=customers, search=search)


@customers_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    user_id = session["user_id"]
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone     = request.form.get("phone", "").strip()
        address   = request.form.get("address", "").strip()

        errors = _validate_customer_form(full_name, phone, address)

        # Check for duplicate customer under this shop owner
        if not errors and models.customer_exists(user_id, full_name, phone or None):
            errors.append(f"A customer named '{full_name}'" + (f" with phone {phone}" if phone else "") + " already exists in your records.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "customers/add.html",
                form_data={"full_name": full_name, "phone": phone, "address": address},
            )

        models.create_customer(user_id, full_name, phone or None, address or None)
        flash(f"Customer '{full_name}' added successfully.", "success")
        return redirect(url_for("customers.index"))

    return render_template("customers/add.html", form_data={})


@customers_bp.route("/<int:id>")
@login_required
def detail(id):
    user_id = session["user_id"]
    customer = models.get_customer(id, user_id)
    if customer is None:
        abort(404)

    ledger_data = models.get_ledger(id, user_id)
    balance = ledger_data["balance"]
    wa_link = get_whatsapp_link(
        customer["phone"] or "",
        customer["full_name"],
        balance,
        session.get("shop_name", "Our Shop")
    )

    return render_template(
        "customers/detail.html",
        customer=customer,
        ledger=ledger_data["entries"],
        balance=balance,
        whatsapp_link=wa_link,
    )


@customers_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    user_id = session["user_id"]
    customer = models.get_customer(id, user_id)
    if customer is None:
        abort(404)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone     = request.form.get("phone", "").strip()
        address   = request.form.get("address", "").strip()

        errors = _validate_customer_form(full_name, phone, address)

        # Check duplicate excluding current customer
        if not errors and models.customer_exists(user_id, full_name, phone or None, exclude_id=id):
            errors.append(f"Another customer with name '{full_name}'" + (f" or phone {phone}" if phone else "") + " already exists.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "customers/edit.html",
                customer=customer,
                form_data={"full_name": full_name, "phone": phone, "address": address},
            )

        models.update_customer(id, user_id, full_name, phone or None, address or None)
        flash("Customer details updated successfully.", "success")
        return redirect(url_for("customers.detail", id=id))

    form_data = {
        "full_name": customer["full_name"],
        "phone":     customer["phone"] or "",
        "address":   customer["address"] or "",
    }
    return render_template("customers/edit.html", customer=customer, form_data=form_data)


@customers_bp.route("/<int:id>/delete", methods=["GET", "POST"])
@login_required
def delete(id):
    user_id = session["user_id"]
    customer = models.get_customer(id, user_id)
    if customer is None:
        abort(404)

    balance = models.get_customer_balance(id, user_id)

    if request.method == "POST":
        if abs(balance) > 0.001:
            flash(f"Cannot delete customer '{customer['full_name']}': outstanding balance of ₹{balance:,.2f} must be settled first.", "danger")
            return redirect(url_for("customers.detail", id=id))

        models.delete_customer(id, user_id)
        flash(f"Customer '{customer['full_name']}' deleted safely.", "success")
        return redirect(url_for("customers.index"))

    return render_template("customers/delete.html", customer=customer, balance=balance)
