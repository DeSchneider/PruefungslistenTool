from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Judoka, Pruefling
import datetime
from sqlalchemy import func

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
    sort = request.args.get('sort', 'name')

    # Unterabfragen für Kyu Grad (MIN) und letztes Prüfungsdatum (MAX) in Prüflingen des Judokas
    from sqlalchemy import func, asc, desc

    # Judoka, die bereits in dieser Prüfung sind, ausschließen
    bereits_in_pruefung = db.session.query(Pruefling.judoka_id).filter_by(pruefung_id=pruefung_id).subquery()

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

    # Hauptquery: alle Judoka mit deren min Kyu und max Datum joinen, aber nicht die bereits in der Prüfung
    query = db.session.query(
        Judoka,
        min_kyu_subq.c.min_kyu,
        max_datum_subq.c.max_datum
    ).outerjoin(
        min_kyu_subq, Judoka.id == min_kyu_subq.c.judoka_id
    ).outerjoin(
        max_datum_subq, Judoka.id == max_datum_subq.c.judoka_id
    ).outerjoin(
        bereits_in_pruefung, Judoka.id == bereits_in_pruefung.c.judoka_id
    ).filter(
        bereits_in_pruefung.c.judoka_id.is_(None)  # Nur Judoka, die NICHT bereits in der Prüfung sind
    )

    # Sortierung
    if sort == 'vorname':
        query = query.order_by(asc(Judoka.vorname))
    elif sort == 'kyu_grad':
        query = query.order_by(asc(min_kyu_subq.c.min_kyu))
    elif sort == 'datum':
        query = query.order_by(desc(max_datum_subq.c.max_datum))
    else:
        query = query.order_by(asc(Judoka.nachname))

    ergebnis = query.all()
    return render_template('judoka_fuer_pruefung.html', judokas=ergebnis, pruefung_id=pruefung_id, sort=sort)


@judoka_bp.route('/import_judoka_csv', methods=['POST'])
def import_judoka_csv():
    if 'csvfile' not in request.files:
        flash('Keine Datei ausgewählt')
        return redirect(url_for('judoka.judoka_liste'))

    file = request.files['csvfile']
    if file.filename == '':
        flash('Keine Datei ausgewählt')
        return redirect(url_for('judoka.judoka_liste'))

    import csv
    import io
    from datetime import datetime

    stream = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
    reader = csv.DictReader(stream)

    imported = 0
    errors = 0

    for row in reader:
        try:
            vorname = row.get('Vorname', '').strip()
            nachname = row.get('Nachname', '').strip()
            geburtsdatum_str = row.get('Geburtsdatum', '').strip()
            hoechster_grad = row.get('Höchster Grad', '').strip()
            letzte_graduierung_str = row.get('Letzte Graduierung', '').strip()

            # Überspringe leere Zeilen
            if not vorname or not nachname:
                continue

            # Geburtsdatum parsen
            geburtsdatum = None
            if geburtsdatum_str:
                try:
                    geburtsdatum = datetime.strptime(geburtsdatum_str, '%d.%m.%Y').date()
                except ValueError:
                    try:
                        geburtsdatum = datetime.strptime(geburtsdatum_str, '%Y-%m-%d').date()
                    except ValueError:
                        continue

            # Prüfe ob Judoka schon existiert
            judoka = Judoka.query.filter_by(vorname=vorname, nachname=nachname).first()

            if judoka:
                # Update existierenden Judoka
                if geburtsdatum:
                    judoka.geburtsdatum = geburtsdatum
            else:
                # Erstelle neuen Judoka
                if not geburtsdatum:
                    continue  # Geburtsdatum ist required

                judoka = Judoka(
                    vorname=vorname,
                    nachname=nachname,
                    geburtsdatum=geburtsdatum,
                    verein=""  # Leer lassen, da nicht in CSV
                )
                db.session.add(judoka)
                db.session.flush()  # Um judoka.id zu bekommen

            # Erstelle Pruefling-Eintrag wenn Grad vorhanden
            if hoechster_grad:
                # Parse letzte Graduierung Datum
                letzte_graduierung_datum = None
                if letzte_graduierung_str:
                    try:
                        letzte_graduierung_datum = datetime.strptime(letzte_graduierung_str, '%d.%m.%Y').date()
                    except ValueError:
                        try:
                            letzte_graduierung_datum = datetime.strptime(letzte_graduierung_str, '%Y-%m-%d').date()
                        except ValueError:
                            pass

                # Prüfe ob bereits Pruefling-Eintrag existiert
                existing_pruefling = Pruefling.query.filter_by(judoka_id=judoka.id, kyu_grad=hoechster_grad).first()

                if not existing_pruefling:
                    pruefling = Pruefling(
                        judoka_id=judoka.id,
                        kyu_grad=hoechster_grad,
                        datum_der_pruefung=letzte_graduierung_datum
                    )
                    db.session.add(pruefling)

            imported += 1

        except Exception as e:
            errors += 1
            continue

    try:
        db.session.commit()
        flash(f'{imported} Datensätze erfolgreich importiert. {errors} Fehler aufgetreten.')
    except Exception as e:
        db.session.rollback()
        flash(f'Fehler beim Speichern: {str(e)}')

    return redirect(url_for('judoka.judoka_liste'))
