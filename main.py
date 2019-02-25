from flask import Flask, render_template, request
from flask_mysqldb import MySQL
from string import ascii_uppercase
import yaml

app = Flask(__name__)

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
        query = "SELECT dep_name FROM department"
    else:
        query = "SELECT dep_name FROM department WHERE dep_name LIKE '{0}%'".format(letter)

    cur.execute(query)
    dept_details = cur.fetchall()
    alphabet = set()
    for c in dept_details:
        alphabet.add(c[0][0].upper())
    return render_template('index.html', alphabet=sorted(alphabet), depts=dept_details)


if __name__ == '__main__':
    app.run(debug=True)