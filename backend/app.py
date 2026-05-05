from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError 
from models import db, Admin, Opportunity, PasswordResetToken
from datetime import datetime, timedelta
import secrets, os

# Point Flask to serve the HTML files from the parent Qatar/ folder
app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config['SECRET_KEY']                  = 'change-this-to-a-random-string'
app.config['SQLALCHEMY_DATABASE_URI']     = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SAMESITE']    = 'Lax'

db.init_app(app)
with app.app_context():
    db.create_all()


# ── Serve the frontend ──────────────────────────────────────
@app.route('/')
def index():
    return render_template('admin.html')


# ── Helper ─────────────────────────────────────────────────
def current_admin():
    return Admin.query.get(session.get('admin_id'))


# ══════════════════════════════════════════════════════════
# TASK 1 — Auth
# ══════════════════════════════════════════════════════════

@app.route('/api/signup', methods=['POST'])
def signup():
    d    = request.get_json()
    name = d.get('full_name', '').strip()
    email = d.get('email', '').strip().lower()
    pw   = d.get('password', '')
    pw2  = d.get('confirm_password', '')

    if not all([name, email, pw, pw2]):
        return jsonify({'error': 'All fields are required'}), 400
    if len(pw) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if pw != pw2:
        return jsonify({'error': 'Passwords do not match'}), 400

    # ← This is the duplicate check — make sure this line is present
    if Admin.query.filter_by(email=email).first():
        return jsonify({'error': 'An account with this email already exists'}), 400

    admin = Admin(full_name=name, email=email, password=generate_password_hash(pw))
    db.session.add(admin)
    db.session.commit()
    return jsonify({'message': 'Account created successfully'}), 201

    


@app.route('/api/login', methods=['POST'])
def login():
    d           = request.get_json()
    email       = d.get('email', '').strip().lower()
    pw          = d.get('password', '')
    remember_me = d.get('remember_me', False)

    admin = Admin.query.filter_by(email=email).first()
    if not admin or not check_password_hash(admin.password, pw):
        return jsonify({'error': 'Invalid email or password'}), 401

    session['admin_id'] = admin.id
    if remember_me:
        session.permanent = True
        app.permanent_session_lifetime = timedelta(days=30)

    return jsonify({'message': 'Login successful',
                    'admin': {'id': admin.id, 'name': admin.full_name,
                              'email': admin.email}}), 200


@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('admin_id', None)
    return jsonify({'message': 'Logged out'}), 200


@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    email = request.get_json().get('email', '').strip().lower()
    admin = Admin.query.filter_by(email=email).first()
    if admin:
        token   = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=1)
        db.session.add(PasswordResetToken(email=email, token=token, expires_at=expires))
        db.session.commit()
        print(f"[RESET LINK] http://localhost:5000/reset-password?token={token}")
    # Always same response (privacy)
    return jsonify({'message': 'If that email exists, a reset link has been sent.'}), 200


@app.route('/reset-password')
def reset_password_page():
    token = request.args.get('token', '')
    # Check if token is valid before showing the page
    record = PasswordResetToken.query.filter_by(token=token).first()
    if not record or record.expires_at < datetime.utcnow():
        return '''
            <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
                <h2 style="color:#e74c3c;">Link Expired or Invalid</h2>
                <p>This password reset link is invalid or has expired.</p>
                <p>Please request a new one.</p>
                <a href="/">Back to Login</a>
            </body></html>
        ''', 400
    return f'''
        <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
            <h2>Reset Your Password</h2>
            <form method="POST" action="/api/reset-password-form">
                <input type="hidden" name="token" value="{token}">
                <div style="margin:16px 0;">
                    <input type="password" name="password" placeholder="New password (min 8 chars)"
                           style="padding:10px;width:280px;border:1px solid #ccc;border-radius:6px;">
                </div>
                <div style="margin:16px 0;">
                    <input type="password" name="confirm_password" placeholder="Confirm new password"
                           style="padding:10px;width:280px;border:1px solid #ccc;border-radius:6px;">
                </div>
                <button type="submit"
                        style="padding:10px 28px;background:#2c5aa0;color:white;border:none;border-radius:6px;cursor:pointer;">
                    Reset Password
                </button>
            </form>
        </body></html>
    '''
@app.route('/api/reset-password-form', methods=['POST'])
def reset_password_form():
    token            = request.form.get('token', '')
    new_password     = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    record = PasswordResetToken.query.filter_by(token=token).first()
    if not record or record.expires_at < datetime.utcnow():
        return '''
            <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
                <h2 style="color:#e74c3c;">Link Expired or Invalid</h2>
                <p>This reset link is invalid or has already been used.</p>
                <a href="/">Back to Login</a>
            </body></html>
        ''', 400

    if len(new_password) < 8:
        return f'''
            <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
                <h2 style="color:#e74c3c;">Password Too Short</h2>
                <p>Password must be at least 8 characters.</p>
                <a href="/reset-password?token={token}">Try again</a>
            </body></html>
        ''', 400

    if new_password != confirm_password:
        return f'''
            <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
                <h2 style="color:#e74c3c;">Passwords Do Not Match</h2>
                <a href="/reset-password?token={token}">Try again</a>
            </body></html>
        ''', 400

    admin          = Admin.query.filter_by(email=record.email).first()
    admin.password = generate_password_hash(new_password)
    db.session.delete(record)  # token used, delete it so it can't be reused
    db.session.commit()

    return '''
        <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
            <h2 style="color:green;">Password Reset Successful!</h2>
            <p>Your password has been updated. You can now log in.</p>
            <a href="/">Back to Login</a>
        </body></html>
    '''


# ══════════════════════════════════════════════════════════
# TASK 2 — Opportunities
# ══════════════════════════════════════════════════════════

def opp_to_dict(o):
    return {
        'id':                   o.id,
        'name':                 o.name,
        'category':             o.category,
        'duration':             o.duration,
        'start_date':           o.start_date,
        'description':          o.description,
        'skills':               o.skills,           # "skill1,skill2"
        'future_opportunities': o.future_opportunities,
        'max_applicants':       o.max_applicants
    }


@app.route('/api/opportunities', methods=['GET'])
def get_opportunities():
    admin = current_admin()
    if not admin:
        return jsonify({'error': 'Unauthorized'}), 401
    opps = Opportunity.query.filter_by(admin_id=admin.id).all()
    return jsonify([opp_to_dict(o) for o in opps]), 200


@app.route('/api/opportunities', methods=['POST'])
def create_opportunity():
    admin = current_admin()
    if not admin:
        return jsonify({'error': 'Unauthorized'}), 401

    d        = request.get_json()
    required = ['name','duration','start_date','description','skills','category','future_opportunities']
    for f in required:
        if not str(d.get(f, '')).strip():
            return jsonify({'error': f'{f} is required'}), 400

    opp = Opportunity(
        name=d['name'], category=d['category'], duration=d['duration'],
        start_date=d['start_date'], description=d['description'],
        skills=d['skills'], future_opportunities=d['future_opportunities'],
        max_applicants=d.get('max_applicants') or None,
        admin_id=admin.id
    )
    db.session.add(opp)
    db.session.commit()
    return jsonify({'message': 'Created', 'opportunity': opp_to_dict(opp)}), 201


@app.route('/api/opportunities/<int:opp_id>', methods=['PUT'])
def update_opportunity(opp_id):
    admin = current_admin()
    if not admin:
        return jsonify({'error': 'Unauthorized'}), 401

    opp = Opportunity.query.filter_by(id=opp_id, admin_id=admin.id).first()
    if not opp:
        return jsonify({'error': 'Not found'}), 404

    d = request.get_json()
    opp.name                 = d.get('name',                 opp.name)
    opp.category             = d.get('category',             opp.category)
    opp.duration             = d.get('duration',             opp.duration)
    opp.start_date           = d.get('start_date',           opp.start_date)
    opp.description          = d.get('description',          opp.description)
    opp.skills               = d.get('skills',               opp.skills)
    opp.future_opportunities = d.get('future_opportunities', opp.future_opportunities)
    opp.max_applicants       = d.get('max_applicants')       or None
    db.session.commit()
    return jsonify({'message': 'Updated', 'opportunity': opp_to_dict(opp)}), 200


@app.route('/api/opportunities/<int:opp_id>', methods=['DELETE'])
def delete_opportunity(opp_id):
    admin = current_admin()
    if not admin:
        return jsonify({'error': 'Unauthorized'}), 401

    opp = Opportunity.query.filter_by(id=opp_id, admin_id=admin.id).first()
    if not opp:
        return jsonify({'error': 'Not found'}), 404

    db.session.delete(opp)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)