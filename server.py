import flask
import os
import sqlite3
import hashlib

app = flask.Flask(__name__)
html_dir = os.path.join(os.path.dirname(__file__), 'html')
index_html = open(os.path.join(html_dir, 'index.html')).read()
register_html = open(os.path.join(html_dir, 'register.html')).read()
data_dir = os.path.join(os.path.dirname(__file__), 'data')
messages = ['Thanks', 'We\'re using secure md5 password hashing now', 
    'Login is no longer vulnerable to SQLi', 'No more script execution',
    'Registration is no longer vulnerable to SQLi',
    'Go to /rarecandy/N to pick your level']

@app.before_request
def setup():
    if 'db' not in flask.session:
        flask.session['db'] = os.urandom(8).encode('hex')+'.db'
        flask.session['level'] = 0
        with sqlite3.connect(os.path.join(data_dir, flask.session['db'])) as conn:
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS passwords(
                id integer primary key autoincrement,
                username varchar(255), password varchar(255),
                hash varchar(255));""")
            cursor.execute('SELECT id FROM passwords WHERE username="admin"')
            if not cursor.fetchone():
                cursor.execute("""INSERT INTO passwords (username, password, hash)
                        VALUES ("admin", "adminpass", "2a9d119df47ff993b662a8ef36f9ea20")""")
            cursor.close()

@app.route('/')
def index():
    try:
        user_id = flask.session['user_id']
    except KeyError:
        return index_html % messages[max(0, min(flask.session['level'], len(messages)))]
    else:
        if user_id == 1:
            flask.session['level'] += 1

            with sqlite3.connect(os.path.join(data_dir, flask.session['db'])) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE passwords SET hash="2a9d119df47ff993b662a8ef36f9ea20" where username="admin"');
                cursor.close()

            return 'Congrats you are the admin<br><a href=/logout>Next level</a>'
        with sqlite3.connect(os.path.join(data_dir, flask.session['db'])) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT username FROM passwords WHERE id=?', (user_id,))
            username = cursor.fetchone()[0]
            cursor.close()
        return 'Welcome to the website, %s<br><a href=/logout>Leave</a>' % username

@app.route('/rarecandy/<level>')
def rarecandy(level):
    flask.session['level'] = int(level)
    return flask.redirect('/')

@app.route('/reset')
def reset():
    del flask.session['db']
    return flask.redirect('/')

@app.route('/logout')
def logout():
    flask.session.pop('user_id', None)
    return flask.redirect('/')

@app.route('/login', methods=['POST'])
def login():
    username = flask.request.form.get('username')
    password = flask.request.form.get('password')

    if not username:
        return 'Must provide username. <a href=/>Go back.</a>\n'
    if not password:
        return 'Must provide password. <a href=/>Go back.</a>\n'

    with sqlite3.connect(os.path.join(data_dir, flask.session['db'])) as conn:
        cursor = conn.cursor()

        if flask.session['level'] == 0:
            query = 'SELECT id FROM passwords WHERE username="%s" AND password="%s"' % (username, password)
        elif flask.session['level'] == 1:
            query = 'SELECT id, hash FROM passwords WHERE username="%s"' % (username)
        elif flask.session['level'] >= 2:
            query = 'SELECT id, hash FROM passwords WHERE username=?'

        if flask.session['level'] >= 2:
            cursor.execute(query, (username,))
        else:
            try:
                cursor.execute(query)
            except sqlite3.OperationalError:
                return 'Error in sql statement:<br>%s<br><a href=/>Go back.</a>\n' % query
            except sqlite3.Warning as e:
                return '%s <a href=/register>Go back.</a>\n' % e

        res = cursor.fetchone()
        cursor.close()
        if res and flask.session['level'] == 0:
            flask.session['user_id'] = res[0]
        elif res and flask.session['level'] and res[1] == hashlib.md5(password).hexdigest():
            flask.session['user_id'] = res[0]
        else:
            return 'Invalid password.  Click <a href=/>here</a> to return.\n'
    return flask.redirect('/')

@app.route('/register', methods=['GET'])
def register_get():
    return register_html

@app.route('/register', methods=['POST'])
def register_post():
    username = flask.request.form.get('username')
    password = flask.request.form.get('password')
    cpassword = flask.request.form.get('cpassword')

    if not username:
        return 'Must provide username\n'
    if not password:
        return 'Must provide password\n'
    if not cpassword:
        return 'Must confirm password\n'
    if password != cpassword:
        return 'Passwords must match\n'

    with sqlite3.connect(os.path.join(data_dir, flask.session['db'])) as conn:
        cursor = conn.cursor()

        query = 'SELECT id FROM passwords WHERE username=?'
        try:
            cursor.execute(query, (username,))
        except sqlite3.OperationalError:
            return 'Error in sql statement:<br>%s<br><a href=/register>Go back.</a>\n' % query
        except sqlite3.Warning as e:
            return '%s <a href=/register>Go back.</a>\n' % e

        if cursor.fetchone():
            return 'Username is already taken\n'

        if flask.session['level'] == 0:
            query = 'INSERT INTO passwords (username, password) VALUES ("%s", "%s")' % (username, password)
        else:
            hashed = hashlib.md5(password).hexdigest()
            query = 'INSERT INTO passwords (username, hash) VALUES ("%s", "%s")' % (username, hashed)
        if flask.session['level'] < 3:
            try:
                cursor.executescript(query)
            except sqlite3.OperationalError:
                return 'Error in sql statement:<br>%s<br><a href=/register>Go back.</a>\n' % query
        else:
            try:
                cursor.execute(query)
            except sqlite3.OperationalError:
                return 'Error in sql statement:<br>%s<br><a href=/register>Go back.</a>\n' % query
            except sqlite3.Warning as e:
                return '%s <a href=/register>Go back.</a>\n' % e

        cursor.execute('SELECT last_insert_rowid()')
        user_id = cursor.fetchone()[0]

        conn.commit()

    flask.session['user_id'] = user_id

    return 'Registered successfully.  Click <a href=/>here</a> to be logged in.\n'

def main():
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    if not os.path.exists(os.path.join(data_dir, 'entropy.dat')):
        with open(os.path.join(data_dir, 'entropy.dat'), 'w') as f:
            f.write(os.urandom(24))
    app.secret_key = open(os.path.join(data_dir, 'entropy.dat')).read()
    app.run(host='0.0.0.0', port=8080, debug=True)

if __name__ == '__main__': main()
