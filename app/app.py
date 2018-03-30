# from data import articles
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

# Matthew 7:7,8

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'us-cdbr-iron-east-05.cleardb.net'
app.config['MYSQL_USER'] = 'bae5ca553420bb'
app.config['MYSQL_PASSWORD'] = '54a73eae'
app.config['MYSQL_DB'] = 'heroku_9aeb6a61a4ea7d7'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

# Articles = articles()


# Home
@app.route('/')
def index():
    """entry point"""
    return render_template('home.html')


# About
@app.route('/about')
def home():
    return render_template('about.html')


# Articles
@app.route('/articles')
def articles():
    return show_articles('articles')


# Single Articles
@app.route('/article/<string:id>/')
def article(id):
    # Create Cursor
    cur = mysql.connection.cursor()

    # Execute query
    cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    # Get article
    article = cur.fetchone()

    # Close connection
    cur.close()
    return render_template('article.html', article=article)


# Registration Form Class (WTFORMS)
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES (%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create Cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        # Username matched
        if result > 0:
            # Get Stored hash
            data = cur.fetchone()
            password = data['password']
            cur.close()
            # Compare passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid password'
                return render_template('login.html', error=error)

        else:
            # Username did not match
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))
    return wrap


# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return show_articles('dashboard')


def show_articles(template):
    # Create Cursor
    cur = mysql.connection.cursor()

    # Execute query
    results = cur.execute("SELECT * FROM articles")

    # Get articles
    articles = cur.fetchall()

    # Close connection
    cur.close()

    if results > 0:
        return render_template('{}.html'.format(template), articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('{}.html'.format(template), msg=msg)


# Article Form Class (WTFORMS)
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])


# Add article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create a Cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        # Close Connection
        cur.close()

        flash('Article {} Create'.format(title), 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)


# Edit article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create a Cursor
    cur = mysql.connection.cursor()

    # Get user by ID
    result = cur.execute("SELECT * FROM articles where id = %s", [id])

    article = cur.fetchone()

    # Close Connection
    cur.close()

    # Get Form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create a Cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", [title, body, id])

        # Commit to DB
        mysql.connection.commit()

        # Close Connection
        cur.close()

        flash('Article {} Updated'.format(title), 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form)


@app.route('/delete_article/<string:id>/', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create a Cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles where id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    # Close Connection
    cur.close()

    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.secret_key = 'secret12345'
    app.run(debug=True)
