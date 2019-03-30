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
    """
    Displays Departments sorted alphabetically, can be filtered by letter
    :return: Main department page
    """
    cur = mysql.connection.cursor()
    # Get letter filter if it exists
    letter = request.args.get('letter')
    query = "SELECT dep_name, dep_code FROM department"

    cur.execute(query)
    dept_details = cur.fetchall()
    alphabet = set()
    # Populate a list with letters that departments start with
    for c in dept_details:
        alphabet.add(c[0][0].upper())

    # Check if there is a filter
    if letter is None:
        filter = sorted(alphabet)
    else:
        filter = [letter]

    return render_template('index.html', alphabet=sorted(alphabet), depts=dept_details, filter=filter)


def get_requisites(courses, cur):
    """
    Gets prerequisites and antirequisites for a department's courses
    :param courses: A list of courses for which to get their requisites
    :param cur: mysql session
    :return: pre_reqs and anti_reqs which are lists containing the respective requisites
    """
    pre_reqs = []
    anti_reqs = []
    # For each course
    for row in courses:
        # Grab prerequisites
        query = f'SELECT course.*, department.dep_name FROM course, prerequisite, department ' \
            f'WHERE prerequisite.crs_code = {row[0]}' \
            f' AND prerequisite.crs_requires = course.crs_code AND course.dep_code = department.dep_code'
        cur.execute(query)
        temp = cur.fetchall()
        pre_reqs.append(temp)

        # Grab antirequisites
        query = f'SELECT course.*, department.dep_name FROM course, antirequisite, department ' \
            f'WHERE antirequisite.crs_code = {row[0]}' \
            f' AND antirequisite.crs_anti = course.crs_code AND course.dep_code = department.dep_code'
        cur.execute(query)
        temp = cur.fetchall()
        anti_reqs.append(temp)

    return pre_reqs, anti_reqs


@app.route('/program')
def program():
    """
    Get the requirements for a specific program
    :return: Program requirements page for a specific program
    """
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


@app.route('/listing', methods=['GET', 'POST'])
def dep_listing():
    """
    Dual purpose page to display courses or programs for a department
    :return: A page listing courses or programs
    """
    cur = mysql.connection.cursor()

    # Handle search request
    if request.method == 'POST':
        return search_courses(request.form)

    # Get department id
    id = request.args.get('id')
    # Get which type to list
    type = request.args.get('type')
    name = ""

    # Whether to filter by department
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


def search_courses(search):
    """
    Handles searching for courses
    :param search: The form data for the search
    :return: Page with search results
    """
    cur = mysql.connection.cursor()
    search_string = search['search']

    # Get courses containing searched value and their department name
    cur.execute("SELECT c.crs_code, c.crs_title, c.crs_description, c.crs_year, d.dep_name"
                " FROM course AS c, department AS d WHERE (c.crs_title LIKE %s OR"
                " c.crs_code LIKE %s) AND c.dep_code = d.dep_code GROUP BY c.crs_year, c.crs_code, d.dep_name",
                [("%" + str(search_string) + "%"), ("%" + str(search_string) + "%")])
    courses = cur.fetchall()
    pre_reqs, anti_reqs = get_requisites(courses, cur)
    return render_template('listing.html', name="Search", courses=courses, pre_reqs=pre_reqs, anti_reqs=anti_reqs)


@app.route('/login', methods=['POST', 'GET'])
def login():
    """
    Handles login for admin
    :return: Session with admin now logged in
    """
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        cur = mysql.connection.cursor()
        # Get user
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
    """
    Handles page for inserting a new course into the database
    :return: Add course page with a success/error message
    """
    conn = mysql.connect
    cur = conn.cursor()
    cur.execute("SELECT * FROM department")
    names = cur.fetchall()
    error = None

    # Handle submit
    if request.method == 'POST':
        # Grab user info
        course_title = request.form["new_course_title"]
        course_description = request.form["new_course_description"]
        course_year = request.form["new_course_year"]
        course_department = request.form["new_course_dep"]
        try:
            # Insert new course into DB
            query = f"INSERT INTO course (`crs_title`, `crs_description`, `crs_year`, `dep_code`)" \
                f" VALUES ('{course_title}', '{course_description}', {course_year}, {course_department})"
            print(query)
            cur.execute(query)
            conn.commit()
            error = "Success!"
        # Handle error
        except Exception as e:
            error = "Problem creating course: " + str(e)
    return render_template('addcourse.html', dep_names=names, error=error)


@app.route('/admin/programs', methods=['POST', 'GET'])
def admin_program():
    """
    Handles admin program page's functionality
    :return: Admin program page
    """
    conn = mysql.connect
    cur = conn.cursor()
    if request.method == 'POST':
        # User adds a new program
        if request.args.get("add"):
            cur.execute("SELECT * FROM department")
            program_title = request.form["new_program_title"]
            program_options = request.form["new_program_options"]
            program_length = request.form["new_program_length"]
            program_dep = request.form["new_program_dep"]
            default_type = "BSc"
            try:
                # Insert a new record into program table
                query = f"INSERT INTO program" \
                    f" (`program_name`, `program_dep`, `program_type`, `program_length`, `num_options`)" \
                    f" VALUES ('{program_title}', {program_dep}, '{default_type}', {program_length}, {program_options})"
                print(query)
                cur.execute(query)
                conn.commit()
            except Exception as e:
                # Handle exception
                pass
        # User deletes the program
        elif request.args.get("delete"):
            data = None
            jsonData = request.get_json()
            program_id = jsonData["id"]
            try:
                # Delete program's id from requirements table and program table
                delete_course_query(conn, cur, "program_requirements", "program_code", program_id)
                delete_course_query(conn, cur, "program", "program_code", program_id)
                data = {"success": "true"}
            except Exception as e:
                # Handle exception
                traceback.print_exc()
                data = {"error": "Please try again."}
            finally:
                return json.dumps(data)
                # User updates the program
        elif request.args.get("update"):
            data = None
            jsonData = request.get_json()
            program_code = jsonData["code"]
            program_name = jsonData["name"]
            program_length = jsonData["length"]
            dep_code = jsonData["dep_code"]
            num_options = jsonData["num_options"]
            courses = jsonData["courses"]

            try:
                # Update program's info
                query = f"UPDATE program " \
                    f"SET program_name= '{program_name}', program_dep='{dep_code}', program_length={program_length}, " \
                    f"num_options={num_options} " \
                    f"WHERE program_code={program_code}"
                cur.execute(query)
                conn.commit()
                # Update its courses
                update_req(cur, conn, "program_requirements", program_code, courses)
                data = {"status": "success"}
            except Exception as e:
                # Handle exception
                traceback.print_exc()
                data = {"error": 404}
            finally:
                # Return json data
                return json.dumps(data)

    cur.execute("SELECT * FROM department")
    deps = cur.fetchall()
    cur.execute("SELECT * FROM course")
    courses = cur.fetchall()
    cur.execute("SELECT * FROM program")
    courses = cur.fetchall()
    data = []
    # Retrieve program's info and it to data array
    for row in courses:
        program = {}
        program["code"] = row[0]
        program["name"] = row[1]
        program["dep_code"] = row[2]
        program["type"] = row[3]
        program["length"] = row[4]
        program["num_options"] = row[5]

        query = f'SELECT dep_name FROM department WHERE dep_code={row[2]}'
        cur.execute(query)
        temp = cur.fetchone()[0]
        program["dep_name"] = temp

        query = f'SELECT course.*, department.dep_name FROM course, program_requirements, department ' \
            f'WHERE program_requirements.program_code = {row[0]}' \
            f' AND program_requirements.program_crs = course.crs_code AND course.dep_code = department.dep_code'
        cur.execute(query)
        temp = cur.fetchall()
        courses = get_codes(temp)
        program["courses"] = courses
        data.append(program)

    return render_template('admin-program.html', data=data, deps=deps, courses=courses)


@app.route('/admin/courses', methods=['POST', 'GET'])
def admin_course():
    """
    Handles admin dashboard functionality
    :return: Admin page
    """
    conn = mysql.connect
    cur = conn.cursor()
    error = None
    if request.method == 'POST':
        # User adds a new course
        if request.args.get("add"):
            cur.execute("SELECT * FROM department")
            course_title = request.form["new_course_title"]
            course_description = request.form["new_course_description"]
            course_year = request.form["new_course_year"]
            course_department = request.form["new_course_dep"]
            try:
                # Insert new record into table course
                query = f"INSERT INTO course (`crs_title`, `crs_description`, `crs_year`, `dep_code`)" \
                    f" VALUES ('{course_title}', '{course_description}', {course_year}, {course_department})"
                print(query)
                cur.execute(query)
                conn.commit()
                error = "Success!"
            except Exception as e:
                # Handle exception
                error = "Problem creating course: " + str(e)
        # User deletes the course
        elif request.args.get("delete"):
            data = None
            jsonData = request.get_json()
            course_id = jsonData["id"]
            try:
                # Delete id along with its reference in other tables
                delete_course_query(conn, cur, "antirequisite", "crs_code", course_id)
                delete_course_query(conn, cur, "prerequisite", "crs_code", course_id)
                delete_course_query(conn, cur, "program_requirements", "program_crs", course_id)
                delete_course_query(conn, cur, "course", "crs_code", course_id)
                data = {"success": "true"}
            except Exception as e:
                # Handle exception
                traceback.print_exc()
                data = {"error": "Please try again."}
            finally:
                # Return json data
                return json.dumps(data)

        # User updates the course
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
                # Update the record
                query = f"UPDATE course " \
                    f"SET crs_title= '{title}', crs_description='{description}', crs_year={year}, dep_code={dep_code} " \
                    f"WHERE crs_code={course_id}"
                cur.execute(query)
                conn.commit()
                update_req(conn, cur, "prerequisite", course_id, pre_reqs)
                update_req(conn, cur, "antirequisite", course_id, anti_reqs)
                data = {"status": "success"}

            except Exception as e:
                # Handle exception
                traceback.print_exc()
                data = {"error": 404}
            finally:
                # Return json
                return json.dumps(data)

    cur.execute("SELECT * FROM department")
    deps = cur.fetchall()

    cur.execute("SELECT * FROM course")
    courses = cur.fetchall()
    data = []
    # Retrieve course's info and add it to data array
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

    return render_template('admin-course.html', data=data, deps=deps, error=error)


@app.route("/allcourses", methods=['GET'])
def get_courses():
    """
    Get all record from the courses
    :return: JSON array containing all courses
    """
    conn = mysql.connect
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM course")
    courses = cur.fetchall()
    data = []
    for c in courses:
        course = {}
        course["crs_code"] = c[0]
        course["crs_title"] = c[1]
        course["crs_description"] = c[2]
        course["crs_year"] = c[3]
        course["dep_code"] = c[4]
        course["ex_code"] = str(c[3]) + "%02d" % c[0]
        query = f'SELECT dep_name FROM department WHERE dep_code={c[4]}'
        cur.execute(query)
        temp = cur.fetchone()[0]
        course["dep_name"] = temp
        data.append(course)
    return json.dumps(data)


@app.route("/logout")
def logout():
    """
    Logout page
    :return: Logout page
    """
    return render_template("logout.html")


def delete_course_query(conn, cur, table, para, id):
    """
    Delete a given element from a table in DB
    :param conn: MySQL connection
    :param cur: cursor for MySQL connection
    :param table: Which table to delete from
    :param para: parameter for identification
    :param id: Id for element to delete
    :return:
    """
    query = f"DELETE FROM {table} " \
        f"WHERE `{para}` = {id}"
    cur.execute(query)
    conn.commit()


def update_req(cur, conn, table, record_id, req_ids):
    """
    Delete a given element from a table in DB
    :param conn: MySQL connection
    :param cur: cursor for MySQL connection
    :param table: Which table to update
    :param record_id: parameter for identification
    :param req_ids: Ids to delete
    :return:
    """
    col_name = None
    record_name = None

    if table == "prerequisite":
        col_name = "crs_requires"
        record_name = "crs_code"
    elif table == "antirequisite":
        col_name = "crs_anti"
        record_name = "crs_code"
    else:
        col_name = "program_crs"
        record_name = "program_code"

    delete_course_query(conn, cur, table, record_name, record_id)

    for req_id in req_ids:
        query = f"INSERT INTO {table} " \
            f"(`{record_name}`, `{col_name}`) " \
            f"VALUES ({record_id}, {req_id})"
        cur.execute(query)
        conn.commit()


def get_codes(courses):
    """
    Get the course code along with its id in JSON format
    :param courses:
    :return: the codes
    """
    codes = []
    for c in courses:
        data = {"id": c[0], "course_code": f"{c[5]} {c[3]}{'%02d' % c[0]}"}
        codes.append(data)
    return codes


# Main entry point
if __name__ == '__main__':
    app.run(debug=True, port=8080)
