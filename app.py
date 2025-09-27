from flask import Flask
from models import db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pruefungsliste.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Blueprints importieren und registrieren
    from blueprints.home import home_bp
    from blueprints.pruefung import pruefung_bp
    from blueprints.favorit import favorit_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(pruefung_bp, url_prefix='/pruefung')
    app.register_blueprint(favorit_bp, url_prefix='/favorit')

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
