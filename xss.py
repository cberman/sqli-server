#!/usr/bin/env python

from flask import Flask, redirect, render_template, session, request
import os, re

app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers.add('X-XSS-Protection', '0')
    return response

@app.route('/')
def index():
    if 'level' in session:
        return redirect('/level/%s' % session['level'])

    return render_template("xss/index.html")

@app.route('/level')
def levelbasic():
    return redirect("/")

@app.route('/level/<int:level>')
def levelroute(level):

    # Check if the user has a level
    if 'level' not in session:
        session['level'] = 1
        return redirect("/level/1")

    # Check if it's a valid level
    if level not in xrange(1, 7):
        return redirect("/")

    # Has the user unlocked the level?
    if session['level'] < level:
        return redirect("/level/%s" % session['level'])

    return render_template("xss/level/%s/index.html" % level)

@app.route('/rarecandy/<level>')
def rarecandy(level):
    session['level'] = int(level)
    return redirect("/level/%s" % level)

@app.route('/reset')
def reset():
    try:
        del session['level']
        session.clear()
    except:
        pass
    return redirect('/')

@app.route('/advance', methods=['GET'])
def advance():

    if request.headers.get("Referer"):
        current = request.headers.get("Referer")[-1]
        if int(current) == 7:
            # User completed all the levels
            return "Congratulations, you finished all the XSS challenges!"

        if int(current) in xrange(1, 7):
            try:
                session['level'] = int(current) + 1
                return redirect("/level/%s" % session['level'])
            except:
                pass

    return redirect("/")

# Challenges
@app.route('/submit/1', methods=['POST'])
def submit1():
    try:
        search_term = request.form['search']
    except:
        return redirect("/level/1")

    return render_template("xss/level/1/search.html", search_term = search_term)

# Challenges
@app.route('/submit/2', methods=['POST'])
def submit2():
    try:
        search_term = request.form['search']
        search_term = search_term.replace("<script>", "").replace("</script>", "")
    except:
        return redirect("/level/2")

    return render_template("xss/level/2/search.html", search_term = search_term)

# Challenges
@app.route('/submit/3', methods=['POST'])
def submit3():
    try:
        search_term = request.form['search']
    except:
        return redirect("/level/3")

    search_term = re.sub(pattern = "<(/)?script>", repl = " ", string = search_term, flags = re.IGNORECASE)

    return render_template("xss/level/3/search.html", search_term = search_term)

# Challenge 4 doesn't have a server handler (hash-based XSS)

@app.route('/submit/5', methods=['GET', 'POST'])
def submit5():
    if request.method == 'POST':
        try:
            newuser = request.form['username']
            session['username'] = newuser
            return render_template("xss/level/5/changeuser.html", message="Username changed successfully!")
        except:
            pass

    return render_template("xss/level/5/changeuser.html")

if __name__ == '__main__':
    app.secret_key = os.urandom(24)
    app.run(host='0.0.0.0', port=8080, debug=True)
