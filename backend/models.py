from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Admin(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password      = db.Column(db.String(200), nullable=False)
    opportunities = db.relationship('Opportunity', backref='admin', lazy=True)

class Opportunity(db.Model):
    id                   = db.Column(db.Integer, primary_key=True)
    name                 = db.Column(db.String(200), nullable=False)
    category             = db.Column(db.String(100), nullable=False)
    duration             = db.Column(db.String(100), nullable=False)
    start_date           = db.Column(db.String(50),  nullable=False)
    description          = db.Column(db.Text,        nullable=False)
    skills               = db.Column(db.String(500), nullable=False)   # stored as "skill1,skill2"
    future_opportunities = db.Column(db.Text,        nullable=False)
    max_applicants       = db.Column(db.Integer,     nullable=True)    # optional
    admin_id             = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)

class PasswordResetToken(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(120), nullable=False)
    token      = db.Column(db.String(200), nullable=False)
    expires_at = db.Column(db.DateTime,   nullable=False)