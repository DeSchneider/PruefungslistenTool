from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Judoka(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vorname = db.Column(db.String(100), nullable=False)
    nachname = db.Column(db.String(100), nullable=False)
    geburtsdatum = db.Column(db.Date, nullable=False)
    verein = db.Column(db.String(150), nullable=False)
    prueflinge = db.relationship('Pruefling', backref='judoka', lazy=True)

class Pruefling(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judoka_id = db.Column(db.Integer, db.ForeignKey('judoka.id'), nullable=False)
    pruefung_id = db.Column(db.Integer, db.ForeignKey('pruefung.id'), nullable=False)
    kyu_grad = db.Column(db.String(50), nullable=False)

class Pruefer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    lizenz_nr = db.Column(db.String(50), nullable=False)
    pruefungen = db.relationship('Pruefung', backref='pruefer', foreign_keys='Pruefung.pruefer_id')
    fremdpruefungen = db.relationship('Pruefung', backref='fremdpruefer', foreign_keys='Pruefung.fremdpruefer_id')

class Pruefung(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ausrichter = db.Column(db.String(150))
    bezirk = db.Column(db.String(100))
    ort_strasse = db.Column(db.String(150))
    ort_ort = db.Column(db.String(100))
    datum = db.Column(db.Date, nullable=False)
    uhrzeit_von = db.Column(db.Time)
    uhrzeit_bis = db.Column(db.Time)
    prueferanzahl = db.Column(db.Integer)
    pruefer_id = db.Column(db.Integer, db.ForeignKey('pruefer.id'))  # Prüfer FK
    fremdpruefer_id = db.Column(db.Integer, db.ForeignKey('pruefer.id'))  # Fremdprüfer FK

class PruefungsFavoriten(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False) # Favoritenname für Identifikation
    ausrichter = db.Column(db.String(150))
    bezirk = db.Column(db.String(100))
    ort_strasse = db.Column(db.String(150))
    ort_ort = db.Column(db.String(100))
    datum = db.Column(db.Date)
    uhrzeit_von = db.Column(db.Time)
    uhrzeit_bis = db.Column(db.Time)
    pruefer_id = db.Column(db.Integer, db.ForeignKey('pruefer.id'))
    fremdpruefer_id = db.Column(db.Integer, db.ForeignKey('pruefer.id'))


