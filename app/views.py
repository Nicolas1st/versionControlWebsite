from app import app, db, bcrypt
from app import execute_sql as sql
from flask import request, render_template, session, redirect, url_for, flash
from app import forms
from sqlalchemy import text


@app.route('/', methods=['GET', 'POST'])
@app.route('/login/', methods=['GET', 'POST'])
def login():

    if 'username' in session:
        return redirect(url_for('profile'))

    form = forms.LoginForm()

    if request.method == 'POST':

        if form.validate_on_submit():

            query = text(f"""
            SELECT hashed_password
            FROM Users
            WHERE name='{form.name.data}'
            """)

            with db.engine.connect() as connection:
                result = [record for record in connection.execute(query)]

            if len(result) > 0:

                hashed_password = result[0][0]
                if bcrypt.check_password_hash(hashed_password, form.password.data):
                    session['username'] = form.name.data
                    return redirect(url_for('profile'))
                else:
                    flash("Wrong password")
            
            else:
                flash("User with this name does not exist")

    return render_template('login.html', form=form)


@app.route('/logout/')
def logout():
    if 'username' in session:
        session.pop('username')
    return redirect(url_for('login'))


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    form = forms.SignupForm()
    if request.method == 'POST':
        if form.validate_on_submit():

            messages = []

            query = text(f"""
            SELECT name
            FROM Users
            WHERE name='{form.name.data}';
            """)
            with db.engine.connect() as connection:
                result = [record for record in connection.execute(query)]
            if len(result) > 0:
                messages.append("The user with the name specified already exists")

            query = text(f"""
            SELECT email
            FROM Users 
            WHERE email='{form.email.data}';
            """)
            with db.engine.connect() as connection:
                result = [record for record in connection.execute(query)]
            if len(result) > 0:
                messages.append("The email is already occupied by another user")
            
            if form.password.data != form.repeated_password.data:
                messages.append("The passwords should match")

            if messages:
                for m in messages:
                    flash(m)
                return render_template("signup.html", form=form)

            res = sql.insert(db, 'Users',
                       columns=['name', 'email', 'hashed_password'],
                       values=[request.form['name'],
                               request.form['email'],
                               bcrypt.generate_password_hash(request.form['password']).decode('utf-8')])
            return redirect(url_for('login'))
    return render_template('signup.html', form=form)


@app.route('/profile/', methods=['GET', 'POST'])
def profile():
    # change_name_form = forms.ChangeNameForm()
    # change_email_form = forms.ChangeEmailForm()
    # change_password_form = forms.ChangePasswordForm()

    if 'username' in session:
        # if request.method == 'POST':
        #     if form.validate_on_submit():
        #         hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        #         sql.update(db, 'Users', columns=['hashed_password'], values=[hashed_password], condition=f"name='{session['username']}'")
        user = sql.select(db, 'Users', columns=['name', 'email'], condition=f"name='{session['username']}'")[0]
        return render_template('profile.html', pagename='Profile', user=user)
    return redirect(url_for('login'))


@app.route('/profile/projects/')
def projects():
    if 'username' in session:
        query = text(f"""
        SELECT Projects.name, Projects.description
        FROM Projects
        WHERE owner_id=(SELECT id
                        FROM Users
                        WHERE Users.name='{session['username']}')
        """)

        with db.engine.connect() as connection:
            projects = [record for record in connection.execute(query)]
            print(projects)

        return render_template('projects.html', pagename='Projects', projects=projects)
    return redirect(url_for('login'))


@app.route('/profile/contributions/')
def contributions():
    if 'username' in session:
        query = text(f"""
        SELECT Projects.name, Projects.description
        FROM Projects
        WHERE owner_id=(SELECT Participants.project_id
                        FROM Participants
                        WHERE Participants.user_id=(SELECT id
                                                    FROM Users
                                                    WHERE Users.name = '{session['username']}'))
        """)
        with db.engine.connect() as connection:
            projects = [record for record in connection.execute(query)]
            print(projects)

        return render_template('contributions.html', pagename='Contributions', projects=projects)
    return redirect(url_for('login'))


@app.route('/projects/{project_name}/', methods=['GET', 'POST'])
def project(project_name):
    """
    check whether the project is public
    and then ether display it or not
    there should be a button to go to the form to make a commit
    """
    pass


@app.route('/projects/{project_name}/issues/')
def user_project_issues(project_name):
    pass


@app.route('/projects/{project_name}/commits/')
def user_project_commits(project_name):
    pass


@app.route('/projects/{project_name}/participants/')
def user_project_participants(project_name):
    pass


@app.route('/profile/change-name/', methods=['GET', 'POST'])
def change_name():
    form = forms.ChangeNameForm()
    if 'username' in session:
        if request.method == 'POST':
            pass
        return render_template('change_name.html', form=form)
    return redirect(url_for('login'))


@app.route('/profile/change-email/', methods=['GET', 'POST'])
def change_email():
    form = forms.ChangeEmailForm()
    if 'username' in session:
        if request.method == 'POST':
            pass
        return render_template('change_email.html', form=form)
    return redirect(url_for('login'))


@app.route('/profile/change-password/', methods=['GET', 'POST'])
def change_password():
    form = forms.ChangePasswordForm()
    if 'username' in session:
        if request.method == 'POST':
            pass
        return render_template('change_password.html', form=form)
    return redirect(url_for('login'))


@app.route('/test/')
def test():
    query = text(f""" describe Users """)
    with db.engine.connect() as connection:
        result = [val for val in connection.execute(query)]
    print(result)
    print(type(result))
    return 'Hello'