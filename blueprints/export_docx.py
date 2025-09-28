from docx import Document
import os
import random
import re
from models import Pruefling


def ersetze_platzhalter_sicher(paragraph, ersetzungen):
    runs = paragraph.runs
    if not runs:
        return
    full_text = ''.join(run.text for run in runs)
    changed = False
    for key, wert in ersetzungen.items():
        placeholders = [
            f'{{{{ {key} }}}}',
            f'{{{{{key}}}}}',
        ]
        for placeholder in placeholders:
            if placeholder in full_text:
                full_text = full_text.replace(placeholder, wert or '')
                changed = True
    if changed:
        runs[0].text = full_text
        for i in range(1, len(runs)):
            runs[i].text = ''


def erstelle_judoka_text_block(prueflinge_sortiert, pruefung):
    judoka_text_blocks = []
    for pruefling in prueflinge_sortiert:
        letzte_pruefung = None
        if pruefung.datum:
            letzte_pruefung = Pruefling.query.filter(
                Pruefling.judoka_id == pruefling.judoka_id,
                Pruefling.pruefung_id != pruefung.id,
                Pruefling.datum_der_pruefung.isnot(None),
                Pruefling.datum_der_pruefung < pruefung.datum
            ).order_by(Pruefling.datum_der_pruefung.desc()).first()

        bewertungen = [random.choice(['+', '++']) for _ in range(4)]
        bewertung_5 = random.choice(['+', '++']) if pruefling.kyu_grad == '1' else ''

        judoka_info = {
            'judoka_name_vorname': f"{pruefling.judoka.nachname}, {pruefling.judoka.vorname}",
            'gebdat': pruefling.judoka.geburtsdatum.strftime('%d.%m.%Y') if pruefling.judoka.geburtsdatum else '',
            'judoka_verein': pruefling.judoka.verein or '',
            'dlp': letzte_pruefung.datum_der_pruefung.strftime(
                '%d.%m.%Y') if letzte_pruefung and letzte_pruefung.datum_der_pruefung else '',
            'lg': f"{letzte_pruefung.kyu_grad}. Kyu" if letzte_pruefung and letzte_pruefung.kyu_grad else '',
            'b1': bewertungen[0],
            'b2': bewertungen[1],
            'b3': bewertungen[2],
            'b4': bewertungen[3],
            'b5': bewertung_5,
            'gn': ''
        }
        judoka_text_blocks.append(judoka_info)
    return judoka_text_blocks


def generiere_und_exportiere_bericht(datei_vorlage, datei_ausgabe, pruefung, prueflinge):
    doc = Document(datei_vorlage)
    prueflinge_sortiert = sorted(prueflinge, key=lambda p: int(p.kyu_grad) if p.kyu_grad.isdigit() else 999,
                                 reverse=True)
    basis_daten = {
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

    for paragraph in doc.paragraphs:
        paragraph_text = paragraph.text
        if paragraph_text and ('{{' in paragraph_text):
            judoka_keys = ['judoka_name_vorname', 'gebdat', 'judoka_verein', 'dlp', 'lg', 'b1', 'b2', 'b3', 'b4', 'b5',
                           'gn']
            has_judoka_placeholder = any(
                any(f"{key}{i + 1}" in paragraph_text for i in range(len(prueflinge_sortiert))) for key in judoka_keys)
            if not has_judoka_placeholder:
                ersetze_platzhalter_sicher(paragraph, basis_daten)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph_text = paragraph.text
                    if paragraph_text and ('{{' in paragraph_text):
                        judoka_keys = ['judoka_name_vorname', 'gebdat', 'judoka_verein', 'dlp', 'lg', 'b1', 'b2', 'b3',
                                       'b4', 'b5', 'gn']
                        has_judoka_placeholder = any(
                            any(f"{key}{i + 1}" in paragraph_text for i in range(len(prueflinge_sortiert))) for key in
                            judoka_keys)
                        if not has_judoka_placeholder:
                            ersetze_platzhalter_sicher(paragraph, basis_daten)

    judoka_text_blocks = erstelle_judoka_text_block(prueflinge_sortiert, pruefung)
    max_anzahl = min(20, len(judoka_text_blocks))

    for i in range(max_anzahl):
        ersetzungen = {}
        for key in ['judoka_name_vorname', 'gebdat', 'judoka_verein', 'dlp', 'lg', 'b1', 'b2', 'b3', 'b4', 'b5', 'gn']:
            ersetzungen[f"{key}{i + 1}"] = judoka_text_blocks[i].get(key, '')
        for paragraph in doc.paragraphs:
            ersetze_platzhalter_sicher(paragraph, ersetzungen)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        ersetze_platzhalter_sicher(paragraph, ersetzungen)

    placeholder_pattern = re.compile(r'\{\{\s*[\w]+\s*\}\}')

    def ersetze_uebrige_platzhalter(paragraph):
        runs = paragraph.runs
        if not runs:
            return
        full_text = ''.join(run.text for run in runs)
        if placeholder_pattern.search(full_text):
            full_text = placeholder_pattern.sub('', full_text)
            runs[0].text = full_text
            for i in range(1, len(runs)):
                runs[i].text = ''

    for paragraph in doc.paragraphs:
        ersetze_uebrige_platzhalter(paragraph)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    ersetze_uebrige_platzhalter(paragraph)

    ordner = os.path.dirname(datei_ausgabe)
    if ordner and not os.path.exists(ordner):
        os.makedirs(ordner)

    doc.save(datei_ausgabe)
