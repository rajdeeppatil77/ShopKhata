from flask import Blueprint, render_template, session
from shopkhata.auth import login_required
from shopkhata import models

dashboard = Blueprint('dashboard', __name__, url_prefix='/')
bp = dashboard


@dashboard.route('/')
@login_required
def index():
    user_id = session['user_id']
    stats = models.get_dashboard_stats(user_id)
    return render_template('dashboard/index.html', stats=stats)
