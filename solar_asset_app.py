# app.py - Main Flask Application
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pandas as pd
import io
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///solar_assets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'
    company = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)  # 'Solar Panel', 'Battery', etc.
    manufacturer = db.Column(db.String(100))
    model = db.Column(db.String(100))
    status = db.Column(db.String(50), default='In Service')  # 'In Service', 'Returned', 'Under Repair', etc.
    location = db.Column(db.String(200))  # Customer address or warehouse
    install_date = db.Column(db.Date)
    warranty_expiry = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'))
    action = db.Column(db.String(100), nullable=False)
    old_values = db.Column(db.Text)
    new_values = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs')
    asset = db.relationship('Asset', backref='audit_logs')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    # Dashboard stats
    total_assets = Asset.query.count()
    in_service = Asset.query.filter_by(status='In Service').count()
    under_repair = Asset.query.filter_by(status='Under Repair').count()
    returned = Asset.query.filter_by(status='Returned').count()
    
    recent_assets = Asset.query.order_by(Asset.updated_at.desc()).limit(10).all()
    
    return render_template('dashboard.html', 
                         total_assets=total_assets,
                         in_service=in_service,
                         under_repair=under_repair,
                         returned=returned,
                         recent_assets=recent_assets)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        company = request.form['company']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            company=company
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/assets')
@login_required
def assets():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = Asset.query
    
    if search:
        query = query.filter(Asset.serial_number.contains(search) | 
                           Asset.manufacturer.contains(search) |
                           Asset.model.contains(search))
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    assets = query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('assets.html', assets=assets, search=search, status_filter=status_filter)

@app.route('/asset/<int:id>')
@login_required
def asset_detail(id):
    asset = Asset.query.get_or_404(id)
    audit_logs = AuditLog.query.filter_by(asset_id=id).order_by(AuditLog.timestamp.desc()).limit(20).all()
    return render_template('asset_detail.html', asset=asset, audit_logs=audit_logs)

@app.route('/asset/new', methods=['GET', 'POST'])
@login_required
def new_asset():
    if request.method == 'POST':
        asset = Asset(
            serial_number=request.form['serial_number'],
            asset_type=request.form['asset_type'],
            manufacturer=request.form['manufacturer'],
            model=request.form['model'],
            status=request.form['status'],
            location=request.form['location'],
            notes=request.form['notes']
        )
        
        # Handle dates
        if request.form.get('install_date'):
            asset.install_date = datetime.strptime(request.form['install_date'], '%Y-%m-%d').date()
        if request.form.get('warranty_expiry'):
            asset.warranty_expiry = datetime.strptime(request.form['warranty_expiry'], '%Y-%m-%d').date()
        
        db.session.add(asset)
        db.session.commit()
        
        # Log the creation
        log = AuditLog(
            user_id=current_user.id,
            asset_id=asset.id,
            action='Created asset',
            new_values=f"Serial: {asset.serial_number}, Type: {asset.asset_type}, Status: {asset.status}"
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Asset created successfully')
        return redirect(url_for('assets'))
    
    return render_template('asset_form.html', asset=None)

@app.route('/asset/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_asset(id):
    asset = Asset.query.get_or_404(id)
    
    if request.method == 'POST':
        # Store old values for audit log
        old_values = f"Status: {asset.status}, Location: {asset.location}"
        
        asset.serial_number = request.form['serial_number']
        asset.asset_type = request.form['asset_type']
        asset.manufacturer = request.form['manufacturer']
        asset.model = request.form['model']
        asset.status = request.form['status']
        asset.location = request.form['location']
        asset.notes = request.form['notes']
        asset.updated_at = datetime.utcnow()
        
        # Handle dates
        if request.form.get('install_date'):
            asset.install_date = datetime.strptime(request.form['install_date'], '%Y-%m-%d').date()
        if request.form.get('warranty_expiry'):
            asset.warranty_expiry = datetime.strptime(request.form['warranty_expiry'], '%Y-%m-%d').date()
        
        new_values = f"Status: {asset.status}, Location: {asset.location}"
        
        db.session.commit()
        
        # Log the update
        log = AuditLog(
            user_id=current_user.id,
            asset_id=asset.id,
            action='Updated asset',
            old_values=old_values,
            new_values=new_values
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Asset updated successfully')
        return redirect(url_for('asset_detail', id=id))
    
    return render_template('asset_form.html', asset=asset)

@app.route('/export/excel')
@login_required
def export_excel():
    assets = Asset.query.all()
    
    # Create DataFrame
    data = []
    for asset in assets:
        data.append({
            'Serial Number': asset.serial_number,
            'Type': asset.asset_type,
            'Manufacturer': asset.manufacturer,
            'Model': asset.model,
            'Status': asset.status,
            'Location': asset.location,
            'Install Date': asset.install_date.strftime('%Y-%m-%d') if asset.install_date else '',
            'Warranty Expiry': asset.warranty_expiry.strftime('%Y-%m-%d') if asset.warranty_expiry else '',
            'Notes': asset.notes or '',
            'Created': asset.created_at.strftime('%Y-%m-%d %H:%M'),
            'Updated': asset.updated_at.strftime('%Y-%m-%d %H:%M')
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Assets')
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'solar_assets_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@app.route('/audit')
@login_required
def audit_trail():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False)
    
    return render_template('audit.html', logs=logs)

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@company.com',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                company='Solar Company'
            )
            db.session.add(admin)
            db.session.commit()
            print("Created admin user: admin/admin123")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)