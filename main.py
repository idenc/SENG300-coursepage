from flask import Flask, render_template, request
from flask_mysqldb import MySQL
import yaml
import json
import time

app = Flask(__name__)

# Config environment
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True


@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


# Config DB
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)


@app.route('/')
def home():
    cur = mysql.connection.cursor()
    letter = request.args.get('letter')
    if letter is None:
        query = "SELECT dep_name, dep_code FROM department"
    else:
        query = "SELECT dep_name, dep_code FROM department WHERE dep_name LIKE '{0}%'".format(letter)

    cur.execute(query)
    dept_details = cur.fetchall()
    alphabet = set()
    for c in dept_details:
        alphabet.add(c[0][0].upper())
    return render_template('index.html', alphabet=sorted(alphabet), depts=dept_details)


@app.route('/courses')
def courses():
    cur = mysql.connection.cursor()
    id = request.args.get('id')
    cur.execute("SELECT dep_name FROM department WHERE dep_code = %s", id)
    name = cur.fetchone()[0]

    query = f"""SELECT c1.crs_code, c1.crs_title, c1.crs_description, c1.crs_year, c2.crs_code, c2.crs_year, c3.crs_code, c3.crs_year, d1.dep_name, d2.dep_name
                FROM course AS c1
                LEFT JOIN prerequisite AS p ON c1.crs_code = p.crs_code
                LEFT JOIN course AS c2 ON p.crs_requires = c2.crs_code
                LEFT JOIN antirequisite AS a ON c1.crs_code = a.crs_code
                LEFT JOIN course AS c3 ON a.crs_anti = c3.crs_code
                LEFT JOIN department AS d1 ON c2.dep_code = d1.dep_code
                LEFT JOIN department AS d2 ON c3.dep_code = d2.dep_code
                WHERE c1.dep_code = {1}"""

    cur.execute(query)
    courses = cur.fetchall()

    return render_template('courses.html', name=name, courses=courses)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) FROM user WHERE username = '{0}' AND password = '{1}'".format(username, password))
        if cur.fetchone()[0] != 0:
            data = {
                "username": username,
                "token": int(round(time.time() * 1000)),
            }
            return json.dumps(data)
        else:
            data = {
                "error": 404,
            }
            return json.dumps(data)
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=80)
