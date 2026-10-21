import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "salon_michel_clave_segura_2026")

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///salon_michel.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), default="cajero")

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(100), nullable=True)
    total = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.datetime.utcnow)

def init_db():
    with app.app_context():
        db.create_all()
        if not Usuario.query.filter_by(username="admin").first():
            hashed_pw = generate_password_hash("admin123")
            admin = Usuario(username="admin", password_hash=hashed_pw, rol="admin")
            db.session.add(admin)
            db.session.commit()

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        init_db()
    except Exception as e:
        print("Error al conectar DB:", e)
        
    if request.method == 'POST':
        user = request.form.get('username')
        password = request.form.get('password')
        usuario = Usuario.query.filter_by(username=user).first()
        
        if usuario and check_password_hash(usuario.password_hash, password):
            session['user'] = usuario.username
            session['rol'] = usuario.rol
            return redirect(url_for('pos'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
            
    return render_template('login.html')

@app.route('/pos')
def pos():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('pos.html', usuario=session['user'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/ventas', methods=['POST'])
def registrar_venta():
    if 'user' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    nueva_venta = Venta(cliente=data.get('cliente', 'General'), total=data.get('total', 0.0))
    db.session.add(nueva_venta)
    db.session.commit()
    return jsonify({"success": True, "venta_id": nueva_venta.id})

if __name__ == '__main__':
    app.run(debug=True)
