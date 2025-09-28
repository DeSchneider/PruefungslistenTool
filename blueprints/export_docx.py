from docx import Document
import re
import os


def ersetze_platzhalter_sicher(paragraph, ersetzungen):
    # Sammle den kompletten Text und die Run-Informationen
    runs = paragraph.runs
    if not runs:
        return

    # Gesamten Text zusammenfügen
    full_text = ''.join(run.text for run in runs)

    # Prüfe, ob Platzhalter vorhanden sind
    changed = False
    for key, wert in ersetzungen.items():
        placeholder = f'{{{{ {key} }}}}'
        if placeholder in full_text:
            full_text = full_text.replace(placeholder, wert or '')
            changed = True

    if not changed:
        return

    # Erste Run behält ihre Formatierung und bekommt den neuen Text
    runs[0].text = full_text

    # Alle anderen Runs leeren (aber nicht löschen, um Formatierung zu erhalten)
    for i in range(1, len(runs)):
        runs[i].text = ''


def generiere_graduierungsbericht(datei_vorlage, datei_ausgabe, pruefung, prueflinge):
    doc = Document(datei_vorlage)

    # Sortiere Prüflinge nach Kyu-Grad (numerisch)
    prueflinge_sortiert = sorted(prueflinge, key=lambda p: int(p.kyu_grad) if p.kyu_grad.isdigit() else 999,
                                 reverse=True)

    # Basis-Daten für Platzhalter
    daten = {
        'ausrichter': pruefung.ausrichter or '',
        'bezirk': pruefung.bezirk or '',
        'ort_strasse': pruefung.ort_strasse or '',
        'ort_ort': pruefung.ort_ort or '',
        'datum': pruefung.datum.strftime('%d.%m.%Y') if pruefung.datum else '',
        'uhrzeit_von': pruefung.uhrzeit_von.strftime('%H:%M') if pruefung.uhrzeit_von else '',
        'uhrzeit_bis': pruefung.uhrzeit_bis.strftime('%H:%M') if pruefung.uhrzeit_bis else '',
        'anzahl_pruefer': str(pruefung.prueferanzahl or 1),
        'pruefer_name': pruefung.pruefer.name if pruefung.pruefer else '',
        'pruefer_lizenz': pruefung.pruefer.lizenz_nr if pruefung.pruefer else '',
        'fremdpruefer_name': pruefung.fremdpruefer.name if pruefung.fremdpruefer else '',
        'fremdpruefer_lizenz': pruefung.fremdpruefer.lizenz_nr if pruefung.fremdpruefer else '',
        'anzahl_graduierungen': str(len(prueflinge_sortiert)),
        'antrag_nr': str(pruefung.id)
    }

    # Basis-Platzhalter ersetzen
    for paragraph in doc.paragraphs:
        ersetze_platzhalter_sicher(paragraph, daten)

    # Judoka-Tabelle befüllen (suche nach Tabelle mit Platzhalter)
    for table in doc.tables:
        # Prüfe, ob das eine Judoka-Tabelle ist (z.B. durch Suche nach bestimmtem Platzhalter)
        erste_zelle_text = table.rows[0].cells[0].text
        if '{{ judoka_' in erste_zelle_text:  # Identifiziere die richtige Tabelle
            # Erste Zeile als Template verwenden
            template_row = table.rows[0]

            # Lösche die Template-Zeile (nach dem Kopieren)
            table._element.remove(template_row._element)

            # Füge für jeden Judoka eine neue Zeile hinzu
            for i, pruefling in enumerate(prueflinge_sortiert):
                new_row = table.add_row()
                # Befülle die Zellen der neuen Zeile
                judoka_daten = {
                    'judoka_nr': str(i + 1),
                    'judoka_nachname': pruefling.judoka.nachname,
                    'judoka_vorname': pruefling.judoka.vorname,
                    'judoka_kyu': pruefling.kyu_grad,
                    'judoka_verein': pruefling.judoka.verein or '',
                    'judoka_geburtsdatum': pruefling.judoka.geburtsdatum.strftime(
                        '%d.%m.%Y') if pruefling.judoka.geburtsdatum else ''
                }

                for cell in new_row.cells:
                    for paragraph in cell.paragraphs:
                        ersetze_platzhalter_sicher(paragraph, judoka_daten)
        else:
            # Normale Tabelle: Standard-Platzhalter ersetzen
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        ersetze_platzhalter_sicher(paragraph, daten)

    # Ordner erstellen
    ordner = os.path.dirname(datei_ausgabe)
    if ordner and not os.path.exists(ordner):
        os.makedirs(ordner)

    doc.save(datei_ausgabe)

