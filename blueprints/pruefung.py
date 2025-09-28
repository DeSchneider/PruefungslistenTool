from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, make_response, send_file
from models import db, Pruefung, Pruefer, PruefungsFavoriten, Pruefling, Judoka
import datetime
from blueprints.export_docx import generiere_graduierungsbericht
from sqlalchemy import func

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
            # Aktuellen Kyu-Grad des Judokas ermitteln (niedrigster Grad = aktueller)
            aktueller_kyu = db.session.query(func.min(Pruefling.kyu_grad)).filter_by(judoka_id=judoka_id).scalar()

            # Falls noch kein Kyu-Grad vorhanden, Standardwert setzen
            if not aktueller_kyu:
                aktueller_kyu = '8'  # Startwert für neue Judoka
            else:
                # Nächsten Kyu-Grad berechnen (ein Grad niedriger)
                try:
                    naechster_kyu = int(aktueller_kyu) - 1
                    if naechster_kyu < 1:
                        naechster_kyu = 1  # Minimum ist 1. Kyu
                    aktueller_kyu = str(naechster_kyu)
                except (ValueError, TypeError):
                    aktueller_kyu = '8'  # Fallback

            neuer_pruefling = Pruefling(
                judoka_id=judoka_id,
                pruefung_id=pruefung_id,
                kyu_grad=aktueller_kyu,
                datum_der_pruefung=pruefung.datum
            )
            db.session.add(neuer_pruefling)

    db.session.commit()
    flash(f"{len(judoka_ids)} Judoka wurden hinzugefügt.", "success")
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


@pruefung_bp.route('/export_docx/<int:pruefung_id>')
def export_docx(pruefung_id):
    pruefung = Pruefung.query.get_or_404(pruefung_id)
    pruefer = pruefung.pruefer

    daten = {
        'ausrichter': pruefung.ausrichter or '',
        'bezirk': pruefung.bezirk or '',
        'datum': pruefung.datum.strftime('%d.%m.%Y') if pruefung.datum else '',
        'pruefer_name': pruefer.name if pruefer else '',
        'pruefer_lizenz': pruefer.lizenz_nr if pruefer else '',
        # weitere Felder...
    }

    vorlage_pfad = 'static/edoc/Kyu_Graduierungsbericht_Vorlage.docx'
    ausgabe_pfad = f'out/Kyu_Graduierungsbericht_{pruefung_id}.docx'

    pruefung = Pruefung.query.get(pruefung_id)
    prueflinge = Pruefling.query.filter_by(pruefung_id=pruefung_id).all()

    generiere_graduierungsbericht(vorlage_pfad, ausgabe_pfad, pruefung, prueflinge)

    return send_file(ausgabe_pfad, as_attachment=True, download_name=f'Graduierungsbericht_Pruefung_{pruefung_id}.docx')