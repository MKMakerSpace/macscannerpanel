from flask import *
from functools import *
from flask_sqlalchemy import SQLAlchemy
import os
from configparser import *

config = ConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__)) + '/config.ini')
try:
    config.add_section('database')
except:
    pass
try:
    config.add_section('user')
except:
    pass


app = Flask(__name__)
app.secret_key = 'SuperSecret'
try:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://' + \
                                            config.get('database', 'user') + \
                                            ':' + \
                                            config.get('database', 'pass') + \
                                            '@' + \
                                            config.get('database', 'host') + \
                                            '/' + \
                                            config.get('database', 'id')
except NoOptionError:
    pass

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

dir_path = os.path.dirname(os.path.realpath(__file__))
installed = dir_path + '/config.ini'


class Scanner(db.Model):
    __tablename__ = 'scanner'
    id = db.Column('id', db.INT, primary_key=True)
    mac = db.Column('mac', db.Unicode(20))
    name = db.Column('name', db.Unicode(80))

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


def install_check(f):
    # noinspection PyGlobalUndefined
    @wraps(f)
    def wrap(*args, **kwargs):
        if os.path.exists(installed):
            return f(*args, **kwargs)
        else:
            global not_installed
            not_installed = True

            return redirect(url_for('setup'))
    return wrap


@app.route('/')
@install_check
@login_required
def home():
    try:
        data = Scanner.query.all()
    except:
        return 'Error establishing database connection'

    return render_template('index.html', data=data)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['user']
        password = request.form['pass']
        if username == config.get('user', 'username') and password == config.get('user', 'password'):
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            return render_template('login.html')
    return render_template('login.html')


@app.route('/new', methods=['POST', 'GET'])
@login_required
def new():
    if request.method == 'POST':
        mac = request.form['mac']
        name = request.form['name']
        data = Scanner(mac, name)
        db.session.add(data)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('new.html')


@app.route('/_action_remove', methods=['POST', 'GET'])
@login_required
def action_remove():
    entry = request.form['id']
    Scanner.query.filter_by(id=entry).delete()
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/test')
def test():
    return 'test'


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if os.path.exists(installed):
        return abort(404)
    if request.method == 'POST':
        database_id = request.form['database_id']
        database_user = request.form['database_user']
        database_pass = request.form['database_pass']
        database_host = request.form['database_host']
        user_user = request.form['user_user']
        user_pass = request.form['user_pass']
        print(database_id)
        print(database_user)
        print(database_pass)
        print(database_host)
        config.set('database', 'id', database_id)
        config.set('database', 'user', database_user)
        config.set('database', 'pass', database_pass)
        config.set('database', 'host', database_host)
        config.set('user', 'username', user_user)
        config.set('user', 'password', user_pass)
        with open(os.path.dirname(os.path.realpath(__file__)) + '/config.ini', 'w') as f:
            config.write(f)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://' + \
                                                config.get('database', 'user') + \
                                                ':' + \
                                                config.get('database', 'pass') + \
                                                '@' + \
                                                config.get('database', 'host') + \
                                                '/' + \
                                                config.get('database', 'id')
        db.create_all()
        return redirect(url_for('home'))
    return render_template('setup.html')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
