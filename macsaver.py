from flask import *
from functools import *
from flask_sqlalchemy import SQLAlchemy
from config import *
app = Flask(__name__)
app.secret_key = 'SuperSecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://' + \
                                        DATABASE_USER + \
                                        ':' + \
                                        DATABASE_PASSWORD + \
                                        '@' + \
                                        DATABASE_ADDRESS + \
                                        '/' + \
                                        DATABASE_NAME
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Scanner(db.Model):
    __tablename__ = DATABASE_TABLE
    id = db.Column('id', db.INT, primary_key=True)
    mac = db.Column('mac', db.Unicode)
    name = db.Column('name', db.Unicode)

    def __init__(self, mac, name):
        self.mac = mac
        self.name = name


def login_required(f):
    # noinspection PyGlobalUndefined
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            global force_log_error
            force_log_error = True

            return redirect(url_for('login'))
    return wrap


@login_required
@app.route('/')
def home():
    data = Scanner.query.all()
    return render_template('index.html', data=data)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['user']
        password = request.form['pass']
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            pass
    return render_template('login.html')


@login_required
@app.route('/new', methods=['POST', 'GET'])
def new():
    if request.method == 'POST':
        mac = request.form['mac']
        name = request.form['name']
        data = Scanner(mac, name)
        db.session.add(data)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('new.html')


@login_required
@app.route('/_action_remove', methods=['POST', 'GET'])
def action_remove():
    entry = request.form['id']
    Scanner.query.filter_by(id=entry).delete()
    db.session.commit()

    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
