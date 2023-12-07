from flask import Flask, render_template, request, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diario_naturopatico.db'
db = SQLAlchemy(app)

class Patologia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), unique=True, nullable=False)
    descrizione = db.Column(db.Text)

    # Aggiungi la relazione con Sintomo
    sintomi = db.relationship('Sintomo', secondary='patologia_sintomo', back_populates='patologie')

    # Aggiungi la relazione con Rimedio
    rimedi = db.relationship('Rimedio', secondary='patologia_rimedio', back_populates='patologie')

class Sintomo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), unique=True, nullable=False)

    # Aggiungi la relazione con Patologia
    patologie = db.relationship('Patologia', secondary='patologia_sintomo', back_populates='sintomi')


class Rimedio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), unique=True, nullable=False)

    # Aggiungi la relazione con Patologia
    patologie = db.relationship('Patologia', secondary='patologia_rimedio', back_populates='rimedi')


patologia_sintomo = db.Table('patologia_sintomo',
    db.Column('patologia_id', db.Integer, db.ForeignKey('patologia.id')),
    db.Column('sintomo_id', db.Integer, db.ForeignKey('sintomo.id'))
)

patologia_rimedio = db.Table('patologia_rimedio',
    db.Column('patologia_id', db.Integer, db.ForeignKey('patologia.id')),
    db.Column('rimedio_id', db.Integer, db.ForeignKey('rimedio.id'))
)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inserisci_dati', methods=['POST'])
def inserisci_dati():
    patologia_nome = request.form['patologia']
    sintomi = request.form['sintomi'].split(',')
    rimedi = request.form['rimedi'].split(',')
    descrizione = request.form['descrizione']

    # Salva i dati nel database
    patologia = Patologia(nome=patologia_nome, descrizione=descrizione)
    db.session.add(patologia)

    for sintomo_nome in sintomi:
        sintomo = Sintomo.query.filter_by(nome=sintomo_nome.strip()).first()

        if not sintomo:
            sintomo = Sintomo(nome=sintomo_nome.strip())
            db.session.add(sintomo)

        patologia.sintomi.append(sintomo)

    for rimedio_nome in rimedi:
        rimedio = Rimedio.query.filter_by(nome=rimedio_nome.strip()).first()

        if not rimedio:
            rimedio = Rimedio(nome=rimedio_nome.strip())
            db.session.add(rimedio)

        patologia.rimedi.append(rimedio)

    db.session.commit()

    return redirect(url_for('index'))

@app.route('/cerca', methods=['GET'])
def cerca():
    query = request.args.get('query', '').lower()

    # Esempi di ricerche nel database
    patologie_trovate = Patologia.query.filter(Patologia.nome.ilike(f'%{query}%')).all()
    sintomi_trovati = Sintomo.query.filter(Sintomo.nome.ilike(f'%{query}%')).all()
    rimedi_trovati = Rimedio.query.filter(Rimedio.nome.ilike(f'%{query}%')).all()

    return render_template('risultati.html', patologie=patologie_trovate, sintomi=sintomi_trovati, rimedi=rimedi_trovati)

@app.route('/cerca_sintomo', methods=['GET'])
def cerca_sintomo():
    sintomo_query = request.args.get('sintomo', '').lower()

    if sintomo_query:
        patologie_trovate = Patologia.query.filter(Patologia.sintomi.any(Sintomo.nome.ilike(f'%{sintomo_query}%'))).all()
    else:
        patologie_trovate = []

    return render_template('risultati_sintomo.html', sintomo_query=sintomo_query, patologie=patologie_trovate)

@app.route('/dettagli_patologia/<int:patologia_id>', methods=['GET'])
def dettagli_patologia(patologia_id):
    patologia = Patologia.query.get_or_404(patologia_id)
    return render_template('risultati.html', patologie=[patologia], sintomi=patologia.sintomi, rimedi=patologia.rimedi)

from flask import redirect, url_for

@app.route('/pulisci_database', methods=['POST'])
def pulisci_database():
    # Implementa la logica per pulire il database
    # Ad esempio, elimina tutti i record nelle tue tabelle
    db.session.query(Patologia).delete()
    db.session.query(Sintomo).delete()
    db.session.query(Rimedio).delete()
    db.session.commit()

    # Reindirizza alla pagina principale dopo la pulizia del database
    return redirect(url_for('index'))


@app.route('/modifica_patologia/<int:patologia_id>', methods=['GET'])
def modifica_patologia(patologia_id):
    patologia = Patologia.query.get_or_404(patologia_id)

    # Creiamo una lista di nomi di sintomi separati da virgola
    sintomi_nomi = ','.join([sintomo.nome for sintomo in patologia.sintomi])

    # Creiamo una lista di nomi di rimedi separati da virgola
    rimedi_nomi = ','.join([rimedio.nome for rimedio in patologia.rimedi])

    return render_template('modifica_patologia.html', patologia=patologia, sintomi_nomi=sintomi_nomi, rimedi_nomi=rimedi_nomi)

@app.route('/salva_modifiche_patologia/<int:patologia_id>', methods=['POST'])
def salva_modifiche_patologia(patologia_id):
    patologia = Patologia.query.get_or_404(patologia_id)

    # Ottieni i dati dalla form e aggiorna la patologia
    patologia.nome = request.form['patologia']
    patologia.descrizione = request.form['descrizione']

    # Aggiorna i sintomi e i rimedi associati
    sintomi_nomi = request.form['sintomi'].split(',')
    rimedi_nomi = request.form['rimedi'].split(',')

    patologia.sintomi = [Sintomo.query.filter_by(nome=sintomo_nome.strip()).first() or Sintomo(nome=sintomo_nome.strip()) for sintomo_nome in sintomi_nomi]
    patologia.rimedi = [Rimedio.query.filter_by(nome=rimedio_nome.strip()).first() or Rimedio(nome=rimedio_nome.strip()) for rimedio_nome in rimedi_nomi]

    # Salva le modifiche nel database
    db.session.commit()

    # Reindirizza alla pagina dei risultati
    return redirect(url_for('cerca'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)