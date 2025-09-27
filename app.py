from flask import Flask
from models import db
import os

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pruefungsliste.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.secret_key = os.urandom(24)

    db.init_app(app)

    # Blueprints importieren und registrieren
    from blueprints.home import home_bp
    from blueprints.pruefung import pruefung_bp
    from blueprints.favorit import favorit_bp
    from blueprints.pruefer import pruefer_bp
    from blueprints.judoka import judoka_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(pruefung_bp, url_prefix='/pruefung')
    app.register_blueprint(favorit_bp, url_prefix='/favorit')
    app.register_blueprint(pruefer_bp, url_prefix='/pruefer')
    app.register_blueprint(judoka_bp, url_prefix='/judoka')

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
