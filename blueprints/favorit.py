from flask import Blueprint, request, redirect, url_for, jsonify, render_template
from models import db, PruefungsFavoriten
import datetime

favorit_bp = Blueprint('favorit', __name__)

@favorit_bp.route('/speichern', methods=['POST'])
def favorit_speichern():
    form = request.form
    name = form.get('favorit_name')
    if not name:
        return "Favoritenname benötigt", 400
    favorit = PruefungsFavoriten(
        name=name,
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
    db.session.add(favorit)
    db.session.commit()
    return redirect(url_for('pruefung.neue_pruefung'))

@favorit_bp.route('/laden/<int:favorit_id>')
def favorit_laden(favorit_id):
    favorit = PruefungsFavoriten.query.get_or_404(favorit_id)
    data = {
        "ausrichter": favorit.ausrichter,
        "bezirk": favorit.bezirk,
        "ort_strasse": favorit.ort_strasse,
        "ort_ort": favorit.ort_ort,
        "datum": favorit.datum.isoformat() if favorit.datum else "",
        "uhrzeit_von": favorit.uhrzeit_von.strftime("%H:%M") if favorit.uhrzeit_von else "",
        "uhrzeit_bis": favorit.uhrzeit_bis.strftime("%H:%M") if favorit.uhrzeit_bis else "",
        "pruefer_id": favorit.pruefer_id or "",
        "fremdpruefer_id": favorit.fremdpruefer_id or "",
        "favorit_name": favorit.name
    }
    return jsonify(data)
