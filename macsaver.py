from flask import *
from functools import *
from flask_sqlalchemy import SQLAlchemy
import os
from configparser import *
from slackclient import SlackClient
import random


client_id = '118121209712.192875325748'
client_secret = '06d8688a6fcfd4ac26bc9f5ee6e0cd10'
oauth_scope = 'bot,channels:read,chat:write:bot,commands'

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


@app.route("/begin_auth", methods=["GET"])
def pre_install():
    return '''
      <a href="https://slack.com/oauth/authorize?scope={0}&client_id={1}">
          Add to Slack
      </a>
  '''.format(oauth_scope, client_id)


@app.route("/finish_auth", methods=["GET", "POST"])
def post_install():

    # Retrieve the auth code from the request params
    auth_code = request.args['code']

    # An empty string is a valid token for this request
    sc = SlackClient("")

    # Request the auth tokens from Slack
    auth_response = sc.api_call(
    "oauth.access",
    client_id=client_id,
    client_secret=client_secret,
    code=auth_code)
    # Save the bot token to an environmental variable or to your data store
    # for later use
    os.environ["SLACK_USER_TOKEN"] = auth_response['access_token']
    os.environ["SLACK_BOT_TOKEN"] = auth_response['bot']['bot_access_token']
    sc = SlackClient(os.environ["SLACK_BOT_TOKEN"])

    sc.api_call(
      "chat.postMessage",
      channel="#macscanner",
      text="Hi, I'm the MacScanner bot! You can ask me who's at the shed by using the /shed command."
    )
    # Don't forget to let the user know that auth has succeeded!
    return "Auth complete!"


@app.route("/slack/command/shed", methods=["POST"])
def command_shed():
    names = ['James', 'Carl', 'Paul', 'Jim', 'Michael', 'Tom', 'Jack', 'Andy']
    unknown = 0
    inshed = []
    for _ in range(random.randint(1,8)):
        choice = random.choice(names)
        if choice not in inshed:
            inshed.append(choice)
    unknown = random.randint(0, 6)
    string = ''
    if len(inshed) == 2:
        string = inshed[0] + ' and ' + inshed[1] + ' are at the shed.'
        return string
    if len(inshed) > 1:
        for a in range(len(inshed)-1):
            string= string + inshed[a] + ', '
    if unknown > 1:
        string = string + inshed [-1] + ' as well as ' + str(unknown) + ' anonymous hackers are at the shed.'
    elif len(inshed) == 1:
        string = inshed[-1] + ' is at the shed.'
    elif len(inshed) > 1 and unknown == 0:
        string = string + ' and ' + inshed[-1] + 'are at the shed.'
    else:
        string = string + inshed [-1] + ' as well as one anonymous hacker are at the shed.'
    return string


@app.route("/slack/command/args", methods=["GET","POST"])
def command_args():
    token = request.form.get('token', None)
    command = request.form.get('command', None)
    args = request.form.get('text', None)
    username = request.form.get('user_name')
    channel_id = request.form.get('channel_id')
    if not token:
        abort(400)
    sc = SlackClient('xoxb-192020136560-1k2wUqp9teSYICulDFuyyJDO')

    sc.api_call(
      "chat.postMessage",
      channel='#general',
      text='@' + username + ' ased me to say: ' + args
    )
    return Response(), 200

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
