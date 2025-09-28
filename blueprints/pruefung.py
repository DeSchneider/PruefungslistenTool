from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from models import db, Pruefung, Pruefer, PruefungsFavoriten, Pruefling, Judoka
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


@pruefung_bp.route('/bearbeiten/<int:pruefung_id>', methods=['GET', 'POST'])
def pruefung_bearbeiten(pruefung_id):
    pruefung = Pruefung.query.get_or_404(pruefung_id)
    prueflinge = Pruefling.query.filter_by(pruefung_id=pruefung_id).join(Judoka).all()
    prueferanzahl = 1 if not pruefung.fremdpruefer_id else 2
    return render_template('pruefung_detail.html', pruefung=pruefung, prueflinge=prueflinge, prueferanzahl=prueferanzahl)


@pruefung_bp.route('/detail/<int:pruefung_id>')
def pruefung_detail(pruefung_id):
    pruefung = Pruefung.query.get_or_404(pruefung_id)
    prueflinge = Pruefling.query.filter_by(pruefung_id=pruefung_id).join(Judoka).all()
    prueferanzahl = 1 if not pruefung.fremdpruefer_id else 2
    return render_template('pruefung_detail.html', pruefung=pruefung, prueflinge=prueflinge, prueferanzahl=prueferanzahl)


@pruefung_bp.route('/pruefer_suche')
def pruefer_suche():
    q = request.args.get('q', '')
    pruefer = Pruefer.query.filter(Pruefer.name.ilike(f'%{q}%')).all()
    results = [{'id': p.id, 'name': p.name, 'lizenz_nr': p.lizenz_nr} for p in pruefer]
    return jsonify(results)

@pruefung_bp.route('/<int:pruefung_id>/prueflinge_hinzufuegen', methods=['POST'])
def prueflinge_hinzufuegen(pruefung_id):
    pruefung = Pruefung.query.get_or_404(pruefung_id)
    judoka_ids = request.form.getlist('judoka_ids')

    if not judoka_ids:
        flash("Keine Judoka ausgewählt.", "warning")
        return redirect(url_for('judoka.judoka_fuer_pruefung', pruefung_id=pruefung_id))

    for judoka_id in judoka_ids:
        # Prüfling nur anlegen, falls noch nicht existiert
        exists = Pruefling.query.filter_by(pruefung_id=pruefung_id, judoka_id=judoka_id).first()
        if not exists:
            neuer_pruefling = Pruefling(
                judoka_id=judoka_id,
                pruefung_id=pruefung_id,
                kyu_grad='',  # Optional: Standardwert oder erweitertes Handling
                datum_der_pruefung=pruefung.datum
            )
            db.session.add(neuer_pruefling)
    db.session.commit()

    flash(f"{len(judoka_ids)} Judoka wurden hinzugefügt.", "success")
    # Bleibe auf dieser Seite, aktualisiert die Liste
    return redirect(url_for('judoka.judoka_fuer_pruefung', pruefung_id=pruefung_id))


@pruefung_bp.route('/<int:pruefung_id>/pruefling_entfernen/<int:pruefling_id>', methods=['POST'])
def pruefling_entfernen(pruefung_id, pruefling_id):
    pruefling = Pruefling.query.get_or_404(pruefling_id)
    db.session.delete(pruefling)
    db.session.commit()
    return redirect(url_for('pruefung.pruefung_detail', pruefung_id=pruefung_id))


@pruefung_bp.route('/angaben_bearbeiten/<int:pruefung_id>', methods=['GET', 'POST'])
def angaben_bearbeiten(pruefung_id):
    pruefung = Pruefung.query.get_or_404(pruefung_id)
    pruefer_liste = Pruefer.query.order_by(Pruefer.name).all()
    if request.method == 'POST':
        pruefung.ausrichter = request.form.get('ausrichter') or None
        pruefung.bezirk = request.form.get('bezirk') or None

        datum_str = request.form.get('datum')
        if datum_str:
            pruefung.datum = datetime.datetime.strptime(datum_str, '%Y-%m-%d').date()
        else:
            pruefung.datum = None

        pruefung.prueferanzahl = request.form.get('prueferanzahl') or None
        pruefung.ort_strasse = request.form.get('ort_strasse') or None
        pruefung.ort_ort = request.form.get('ort_ort') or None

        uhrzeit_von = request.form.get('uhrzeit_von')
        pruefung.uhrzeit_von = datetime.datetime.strptime(uhrzeit_von, '%H:%M').time() if uhrzeit_von else None
        uhrzeit_bis = request.form.get('uhrzeit_bis')
        pruefung.uhrzeit_bis = datetime.datetime.strptime(uhrzeit_bis, '%H:%M').time() if uhrzeit_bis else None

        pruefer_id = request.form.get('pruefer_id')
        pruefung.pruefer_id = int(pruefer_id) if pruefer_id else None

        fremdpruefer_id = request.form.get('fremdpruefer_id')
        pruefung.fremdpruefer_id = int(fremdpruefer_id) if fremdpruefer_id else None

        db.session.commit()
        return redirect(url_for('pruefung.pruefung_detail', pruefung_id=pruefung_id))
    return render_template(
        'pruefung_angaben_bearbeiten.html',
        pruefung=pruefung,
        pruefer_liste=pruefer_liste
    )