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


def generiere_graduierungsbericht(datei_vorlage, datei_ausgabe, daten):
    doc = Document(datei_vorlage)

    # Absätze bearbeiten
    for paragraph in doc.paragraphs:
        ersetze_platzhalter_sicher(paragraph, daten)

    # Tabellenzellen bearbeiten
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    ersetze_platzhalter_sicher(paragraph, daten)

    # Ordner erstellen falls nötig
    ordner = os.path.dirname(datei_ausgabe)
    if ordner and not os.path.exists(ordner):
        os.makedirs(ordner)

    doc.save(datei_ausgabe)
