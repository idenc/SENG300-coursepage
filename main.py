from flask import Flask, render_template, request
from flask_mysqldb import MySQL
import yaml
import json
import time
import traceback

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
    query = "SELECT dep_name, dep_code FROM department"

    cur.execute(query)
    dept_details = cur.fetchall()
    alphabet = set()
    for c in dept_details:
        alphabet.add(c[0][0].upper())

    if letter is None:
        filter = sorted(alphabet)
    else:
        filter = [letter]

    return render_template('index.html', alphabet=sorted(alphabet), depts=dept_details, filter=filter)


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


@app.route('/program')
def program():
    cur = mysql.connection.cursor()

    # Get the courses that are required by the program
    program_id = request.args.get('id')
    cur.execute(
        "SELECT c.* FROM course AS c, program_requirements AS p WHERE p.program_code = %s"
        " AND c.crs_code = p.program_crs",
        program_id)
    program_requirements = cur.fetchall()

    # Get the program info
    cur.execute("SELECT * FROM program WHERE program_code = %s", program_id)
    program_info = cur.fetchall()

    return render_template('program.html', program_requirements=program_requirements, program_info=program_info)


@app.route('/listing')
def dep_listing():
    cur = mysql.connection.cursor()
    id = request.args.get('id')
    type = request.args.get('type')
    name = ""
    if id is not None:
        cur.execute("SELECT dep_name FROM department WHERE dep_code = %s", id)
        name = cur.fetchone()[0]

    # Get department's course data or program data
    if type == "courses":
        cur.execute("SELECT * FROM course WHERE dep_code = %s GROUP BY crs_year, crs_code", id)
        courses = cur.fetchall()
        pre_reqs, anti_reqs = get_requisites(courses, cur)
        return render_template('listing.html', name=name, courses=courses, pre_reqs=pre_reqs, anti_reqs=anti_reqs)
    else:
        # Select department's programs
        if id is not None:
            cur.execute("SELECT program_name, program_code FROM program WHERE program_dep = %s", id)
        # Select all programs
        else:
            cur.execute("SELECT program_name, program_code FROM program")
        programs = cur.fetchall()
        return render_template('listing.html', name=name, programs=programs)


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


@app.route('/admin/courses', methods=['POST', 'GET'])
def admin_course():
    conn = mysql.connect
    cur = conn.cursor()
    if request.method == 'POST':

        if request.args.get("delete"):
            # This will be finished later
            date = None
        elif request.args.get("update"):
            data = None
            jsonData = request.get_json()
            course_id = jsonData["id"]
            title = jsonData["title"]
            description = jsonData["description"]
            year = jsonData["year"]
            dep_code = jsonData["dep_code"]
            pre_reqs = jsonData["pre_reqs"]  # JSON array containing ids of prerequisite
            anti_reqs = jsonData["anti_reqs"]  # JSON array containing ids of antirequisite

            try:
                query = f"UPDATE course " \
                    f"SET crs_title= '{title}', crs_description='{description}', crs_year={year}, dep_code={dep_code} " \
                    f"WHERE crs_code={course_id}"
                cur.execute(query)
                conn.commit()

                update_req(cur, conn, "prerequisite", course_id, pre_reqs)
                update_req(cur, conn, "antirequisite", course_id, anti_reqs)
                data = {"status": "success"}

            except Exception as e:
                traceback.print_exc()
                data = {"error": 404}

            finally:
                return json.dumps(data)

    cur.execute("SELECT * FROM department")
    deps = cur.fetchall()

    cur.execute("SELECT * FROM course")
    courses = cur.fetchall()
    data = []
    for row in courses:
        course = {}
        course["id"] = row[0]
        course["code"] = str(row[3]) + "%02d" % row[0]
        course["title"] = row[1]
        course["description"] = row[2]
        course["year"] = row[3]
        course["dep_code"] = row[4]

        query = f'SELECT dep_name FROM department WHERE dep_code={row[4]}'
        cur.execute(query)
        temp = cur.fetchone()[0]
        course["dep_name"] = temp

        query = f'SELECT course.*, department.dep_name FROM course, prerequisite, department ' \
            f'WHERE prerequisite.crs_code = {row[0]}' \
            f' AND prerequisite.crs_requires = course.crs_code AND course.dep_code = department.dep_code'
        cur.execute(query)
        temp = cur.fetchall()
        pres = get_codes(temp)
        course["pre_reqs"] = pres

        query = f'SELECT course.*, department.dep_name FROM course, antirequisite, department ' \
            f'WHERE antirequisite.crs_code = {row[0]}' \
            f' AND antirequisite.crs_anti = course.crs_code AND course.dep_code = department.dep_code'
        cur.execute(query)
        temp = cur.fetchall()
        antis = get_codes(temp)
        course["anti_reqs"] = antis
        data.append(course)

    return render_template('admin-course.html', data=data, deps=deps)


def update_req(cur, conn, table, course_id, req_ids):
    col_name = None
    if table == "prerequisite":
        col_name = "crs_requires"
    else:
        col_name = "crs_anti"

    query = f"DELETE FROM {table} " \
        f"WHERE crs_code = {course_id}"
    cur.execute(query)
    conn.commit()

    for req_id in req_ids:
        query = f"INSERT INTO {table} " \
            f"(`crs_code`, `{col_name}`) " \
            f"VALUES ({course_id}, {req_id})"
        cur.execute(query)
        conn.commit()


def get_codes(courses):
    codes = []
    for c in courses:
        data = {"id": c[0], "course_code": f"{c[5]} {c[3]}{'%02d' % c[0]}"}
        codes.append(data)
    return codes


if __name__ == '__main__':
    app.run(debug=True, port=8080)
