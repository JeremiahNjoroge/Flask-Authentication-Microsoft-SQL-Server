from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from data import Articles
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt # encrypting passswords
from functools import wraps
import pyodbc #create sql coonection

app = Flask(__name__)

# Create  SQL connection string
conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=GRIT\SQLEXPRESS;DATABASE=myflaskapp;UID=sa;PWD=root1234')

# Index
@app.route('/')
def index():
    return render_template('home.html')

# About
@app.route('/about')
def about():
    return render_template('about.html')

# Articles
@app.route('/articles')
def articles():
    # Create cursor
    
    cursor = conn.cursor()

    # Get articles
    cursor.execute("SELECT * FROM articles")
    articles = cursor.fetchall()

    if len(articles) > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
            # Close connection
        cursor.close()
        return render_template('articles.html', msg=msg)



#Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    
    cursor = conn.cursor()

    # Get article
    cursor.execute("SELECT * FROM articles WHERE id = ?", [id])

    article = cursor.fetchone()

    return render_template('article.html', article=article)


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cursor = conn.cursor()

        # Execute query
        cursor.execute("INSERT INTO users(name, email, username, password) VALUES(?, ?, ?, ?)", (name, email, username, password))

        # Commit to DB
        conn.commit()

        # Close connection
        cursor.close()

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
        
        # Create cursor
        cursor = conn.cursor()

        # Get user by username
        cursor.execute("SELECT * FROM users WHERE username = ?", [username])

        user = cursor.fetchone()

        if user:
            # Get stored hash and user data
            stored_password = user.password

            # Compare passwords
            if sha256_crypt.verify(password_candidate, stored_password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                cursor.close()
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                cursor.close()
                return render_template('login.html', error=error)
        else:
            error = 'Username not found'
            cursor.close()
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
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
    # Create cursor
    cursor = conn.cursor()

    # Get articles 
    cursor.execute("SELECT * FROM articles WHERE author = ?", [session['username']])

    articles = cursor.fetchall()

    if len(articles) > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
           # Close connection
        cursor.close()
        return render_template('dashboard.html', msg=msg)
 

# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cursor = conn.cursor()

        # Execute
        cursor.execute("INSERT INTO articles(title, body, author) VALUES(?, ?, ?)",(title, body, session['username']))

        # Commit to DB
        conn.commit()

        #Close connection
        cursor.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cursor= conn.cursor()

    # Get article by id
    cursor.execute("SELECT * FROM articles WHERE id = ?", [id])

    article = cursor.fetchone()
    cursor.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article[1]
    form.body.data = article[3]

    if request.method == 'POST' and form.validate():
        title = request.form[1]
        body = request.form[3]

        # Create Cursor
        cursor = conn.cursor()
        app.logger.info(title)
        # Execute
        cursor.execute ("UPDATE articles SET title=?, body=? WHERE id=?",(title, body, id))
        # Commit to DB
        conn.commit()

        #Close connection
        cursor.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cursor = conn.cursor()

    # Execute
    cursor.execute("DELETE FROM articles WHERE id = ?", [id])

    # Commit to DB
    cursor.commit()

    #Close connection
    cursor.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True,port='3000')
