from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models import db, Pruefung, Pruefer, PruefungsFavoriten
import datetime

pruefung_bp = Blueprint('pruefung', __name__)

@pruefung_bp.route('/neu', methods=['GET', 'POST'])
def neue_pruefung():
    if request.method == 'POST':
        form = request.form
        pruefung = Pruefung(
            ausrichter=form.get('ausrichter'),
            bezirk=form.get('bezirk'),
            ort_strasse=form.get('ort_strasse'),
            ort_ort=form.get('ort_ort'),
            datum=datetime.datetime.strptime(form.get('datum'), '%Y-%m-%d').date() if form.get('datum') else None,
            uhrzeit_von=datetime.datetime.strptime(form.get('uhrzeit_von'), '%H:%M').time() if form.get('uhrzeit_von') else None,
            uhrzeit_bis=datetime.datetime.strptime(form.get('uhrzeit_bis'), '%H:%M').time() if form.get('uhrzeit_bis') else None,
            pruefer_id=form.get('pruefer_id'),
            fremdpruefer_id=form.get('fremdpruefer_id')
        )
        db.session.add(pruefung)
        db.session.commit()
        return redirect(url_for('pruefung.pruefung_detail', pruefung_id=pruefung.id))
    favoriten = PruefungsFavoriten.query.order_by(PruefungsFavoriten.name).all()
    return render_template('neue_pruefung.html', favoriten=favoriten)

@pruefung_bp.route('/bearbeiten')
def pruefung_bearbeiten():
    return "<h1>Hier kommt die Funktion zum Bearbeiten von Prüfungen.</h1><p>Wird bald ergänzt.</p>"


@pruefung_bp.route('/detail/<int:pruefung_id>')
def pruefung_detail(pruefung_id):
    pruefung = Pruefung.query.get_or_404(pruefung_id)
    return render_template('pruefung_detail.html', pruefung=pruefung)

@pruefung_bp.route('/pruefer_suche')
def pruefer_suche():
    q = request.args.get('q', '')
    pruefer = Pruefer.query.filter(Pruefer.name.ilike(f'%{q}%')).all()
    results = [{'id': p.id, 'name': p.name, 'lizenz_nr': p.lizenz_nr} for p in pruefer]
    return jsonify(results)