from flask import Blueprint, render_template
from models import Pruefung

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    alle_pruefungen = Pruefung.query.order_by(Pruefung.datum.desc()).all()
    return render_template('index.html', pruefungen=alle_pruefungen)
