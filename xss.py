import flask
import os

app = flask.Flask(__name__)

@app.after_request
def after_request(response):
    response.headers.add('X-XSS-Protection', '0')
    return response

@app.route('/')
def index():
    if 'level' in flask.session:
        return flask.redirect('/level/%s' % flask.session['level'])

    return flask.render_template("xss/index.html")

@app.route('/level')
def levelbasic():
    return flask.redirect("/")

@app.route('/level/<int:level>')
def levelroute(level):

    # Check if the user has a level
    if 'level' not in flask.session:
        flask.session['level'] = 1
        return flask.redirect("/level/1")

    # Check if it's a valid level
    if level not in xrange(1, 5):
        return flask.redirect("/")

    # Has the user unlocked the level?
    if flask.session['level'] < level:
        return flask.redirect("/%s" % flask.session['level'])

    return flask.render_template("xss/level/%s.html" % level)

@app.route('/rarecandy/<level>')
def rarecandy(level):
    flask.session['level'] = int(level)
    return flask.redirect('/level/%s' % level)

@app.route('/reset')
def reset():
    try:
        del flask.session['level']
    except:
        pass
    return flask.redirect('/')

if __name__ == '__main__':
    app.secret_key = os.urandom(24)
    app.run(host='0.0.0.0', port=8080, debug=True)
