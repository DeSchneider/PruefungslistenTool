from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from models import db, Pruefer

pruefer_bp = Blueprint('pruefer', __name__, url_prefix='/pruefer')

@pruefer_bp.route('/liste')
def liste_json():
    pruefer = Pruefer.query.order_by(Pruefer.name).all()
    return jsonify([{"id": p.id, "name": p.name, "lizenz_nr": p.lizenz_nr} for p in pruefer])

@pruefer_bp.route('/')
def pruefer_verwalten():
    pruefer = Pruefer.query.order_by(Pruefer.name).all()
    return render_template('pruefer_verwalten.html', prueferliste=pruefer)

@pruefer_bp.route('/hinzufuegen', methods=['POST'])
def hinzufuegen():
    name = request.form.get('name')
    lizenz_nr = request.form.get('lizenz_nr')
    if not name or not lizenz_nr:
        # Einfach zurück zur Verwaltungsseite mit Fehler im Flash (optional)
        return redirect(url_for('pruefer.pruefer_verwalten'))
    neuer_pruefer = Pruefer(name=name, lizenz_nr=lizenz_nr)
    db.session.add(neuer_pruefer)
    db.session.commit()
    return redirect(url_for('pruefer.pruefer_verwalten'))

@pruefer_bp.route('/loeschen/<int:pruefer_id>', methods=['POST'])
def loeschen(pruefer_id):
    pruefer = Pruefer.query.get_or_404(pruefer_id)
    db.session.delete(pruefer)
    db.session.commit()
    return redirect(url_for('pruefer.pruefer_verwalten'))
