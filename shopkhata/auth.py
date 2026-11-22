import functools
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    session,
    flash,
    g
)
from werkzeug.security import generate_password_hash, check_password_hash
from shopkhata import models

bp = Blueprint('auth', __name__, url_prefix='/auth')


def login_required(view):
    """View decorator to ensure a user is logged in."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('user_id') is None:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.path if request.method == 'GET' else None))
        return view(**kwargs)
    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """Load logged-in user into flask.g on each request."""
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = models.get_user_by_id(user_id)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        error = None

        if not username:
            error = 'Please enter your username.'
        elif not password:
            error = 'Please enter your password.'
        else:
            user = models.get_user_by_username(username)
            if user is None or not check_password_hash(user['password_hash'], password):
                error = 'Invalid username or password.'

        if error is None:
            session.clear()
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['shop_name'] = user['shop_name']
            flash(f"Welcome back, {user['shop_name']}!", 'success')

            next_page = request.args.get('next') or ''
            # Only allow same-site relative paths ("//evil.com" and "/\\evil.com" are not).
            if next_page.startswith('/') and not next_page.startswith(('//', '/\\')):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))

        flash(error, 'danger')

    return render_template('auth/login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        shop_name = request.form.get('shop_name', '').strip()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif not shop_name:
            error = 'Shop name is required.'
        elif models.get_user_by_username(username) is not None:
            error = f"Username '{username}' is already taken."

        if error is None:
            password_hash = generate_password_hash(password)
            models.create_user(username, password_hash, shop_name)
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))

        flash(error, 'danger')

    return render_template('auth/login.html', register_mode=True)


@bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.login'))
