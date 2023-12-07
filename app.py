from flask import Flask, render_template, request, redirect, url_for
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
        sintomo = Sintomo(nome=sintomo_nome.strip())
        db.session.add(sintomo)
        patologia.sintomi.append(sintomo)

    for rimedio_nome in rimedi:
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



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
