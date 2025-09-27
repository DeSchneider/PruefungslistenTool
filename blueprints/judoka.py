from flask import Blueprint, render_template, request, redirect, url_for
from models import db, Judoka, Pruefling
import datetime

judoka_bp = Blueprint('judoka', __name__, url_prefix='/judoka')

@judoka_bp.route('/')
def judoka_liste():
    judokas = Judoka.query.order_by(Judoka.nachname, Judoka.vorname).all()
    return render_template('judoka_verwalten.html', judokas=judokas)

@judoka_bp.route('/hinzufuegen', methods=['POST'])
def judoka_hinzufuegen():
    vorname = request.form.get('vorname')
    nachname = request.form.get('nachname')
    geburtsdatum_str = request.form.get('geburtsdatum')
    verein = request.form.get('verein')
    kyu_grad = request.form.get('kyu_grad')
    datum_der_pruefung_str = request.form.get('datum_der_pruefung')

    if not (vorname and nachname and geburtsdatum_str and verein and kyu_grad):
        return redirect(url_for('judoka.judoka_liste'))

    geburtsdatum = datetime.datetime.strptime(geburtsdatum_str, '%Y-%m-%d').date()

    datum_der_pruefung = None
    if datum_der_pruefung_str:
        datum_der_pruefung = datetime.datetime.strptime(datum_der_pruefung_str, '%Y-%m-%d').date()

    neuer_judoka = Judoka(
        vorname=vorname,
        nachname=nachname,
        geburtsdatum=geburtsdatum,
        verein=verein
    )
    db.session.add(neuer_judoka)
    db.session.commit()

    neuer_pruefling = Pruefling(
        judoka_id=neuer_judoka.id,
        pruefung_id=None,
        kyu_grad=kyu_grad,
        datum_der_pruefung=datum_der_pruefung
    )
    db.session.add(neuer_pruefling)
    db.session.commit()

    return redirect(url_for('judoka.judoka_liste'))

@judoka_bp.route('/loeschen/<int:judoka_id>', methods=['POST'])
def judoka_loeschen(judoka_id):
    judoka = Judoka.query.get_or_404(judoka_id)
    # Optional: zuerst Prüflinge löschen
    Pruefling.query.filter_by(judoka_id=judoka.id).delete()
    db.session.delete(judoka)
    db.session.commit()
    return redirect(url_for('judoka.judoka_liste'))

@judoka_bp.route('/pruefung/<int:pruefung_id>')
def judoka_fuer_pruefung(pruefung_id):
    sort = request.args.get('sort', 'name')  # Standardsortierung

    # Unterabfragen für Kyu Grad (MIN) und letztes Prüfungsdatum (MAX) in Prüflingen des Judokas
    from sqlalchemy import func, select, and_, asc, desc

    # Subquery: aktuelles Min Kyu Grad pro Judoka
    min_kyu_subq = db.session.query(
        Pruefling.judoka_id,
        func.min(Pruefling.kyu_grad).label('min_kyu')
    ).group_by(Pruefling.judoka_id).subquery()

    # Subquery: aktuelles Max Datum der Prüfung pro Judoka
    max_datum_subq = db.session.query(
        Pruefling.judoka_id,
        func.max(Pruefling.datum_der_pruefung).label('max_datum')
    ).group_by(Pruefling.judoka_id).subquery()

    # Hauptquery: alle Judoka mit deren min Kyu und max Datum joinen
    query = db.session.query(
        Judoka,
        min_kyu_subq.c.min_kyu,
        max_datum_subq.c.max_datum
    ).outerjoin(
        min_kyu_subq, Judoka.id == min_kyu_subq.c.judoka_id
    ).outerjoin(
        max_datum_subq, Judoka.id == max_datum_subq.c.judoka_id
    )

    # Sortierung
    if sort == 'vorname':
        query = query.order_by(asc(Judoka.vorname))
    elif sort == 'kyu_grad':
        # Kyu Grad ggf. numerisch umwandeln, sonst string aufsteigend
        query = query.order_by(asc(min_kyu_subq.c.min_kyu))
    elif sort == 'datum':
        query = query.order_by(desc(max_datum_subq.c.max_datum))
    else:
        # Standard: Nachname
        query = query.order_by(asc(Judoka.nachname))

    ergebnis = query.all()
    return render_template('judoka_fuer_pruefung.html', judokas=ergebnis, pruefung_id=pruefung_id, sort=sort)