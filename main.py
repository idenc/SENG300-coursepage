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


def get_requisites(courses, cur):
    pre_reqs = []
    anti_reqs = []
    for row in courses:
        query = f'SELECT course.*, department.dep_name FROM course, prerequisite, department ' \
            f'WHERE prerequisite.crs_code = {row[0]}' \
            f' AND prerequisite.crs_requires = course.crs_code AND course.dep_code = department.dep_code'
        cur.execute(query)
        temp = cur.fetchall()
        pre_reqs.append(temp)

        query = f'SELECT course.*, department.dep_name FROM course, antirequisite, department ' \
            f'WHERE antirequisite.crs_code = {row[0]}' \
            f' AND antirequisite.crs_anti = course.crs_code AND course.dep_code = department.dep_code'
        cur.execute(query)
        temp = cur.fetchall()
        anti_reqs.append(temp)
    return pre_reqs, anti_reqs


@app.route('/courses')
def courses():
    cur = mysql.connection.cursor()
    id = request.args.get('id')
    cur.execute("SELECT dep_name FROM department WHERE dep_code = %s", id)
    name = cur.fetchone()[0]

    cur.execute("SELECT * FROM course WHERE dep_code = %s GROUP BY crs_year, crs_code", id)
    courses = cur.fetchall()
    pre_reqs, anti_reqs = get_requisites(courses, cur)

    return render_template('courses.html', name=name, courses=courses, pre_reqs=pre_reqs, anti_reqs=anti_reqs)


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


@app.route('/addcourse', methods=['POST', 'GET'])
def add_course():
    conn = mysql.connect
    cur = conn.cursor()
    cur.execute("SELECT * FROM department")
    names = cur.fetchall()
    error = None
    if request.method == 'POST':
        course_title = request.form["new_course_title"]
        course_description = request.form["new_course_description"]
        course_year = request.form["new_course_year"]
        course_department = request.form["new_course_dep"]
        try:
            query = f"INSERT INTO course (`crs_title`, `crs_description`, `crs_year`, `dep_code`)" \
                f" VALUES ('{course_title}', '{course_description}', {course_year}, {course_department})"
            print(query)
            cur.execute(query)
            conn.commit()
            error = "Success!"
        except Exception as e:
            error = "Problem creating course: " + str(e)
    return render_template('addcourse.html', dep_names=names, error=error)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=80)
