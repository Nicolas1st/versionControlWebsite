from app import app, db, bcrypt, tables
from flask import request, render_template, session, redirect, url_for, flash
from app import forms
from sqlalchemy import text
from functools import reduce


@app.route('/', methods=['GET', 'POST'])
@app.route('/login/', methods=['GET', 'POST'])
def login():

    if 'username' in session:
        return redirect(url_for('profile'))

    form = forms.LoginForm()

    if request.method == 'POST':

        if form.validate_on_submit():

            users = tables.Users.select(columns=['hashed_password'], condition=f"name='{form.name.data}'")

            if len(users) > 0:

                hashed_password = users[0]['hashed_password']
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

            # check whether the name specified is occupied
            users = tables.Users.select(columns=['name'], condition=f"name='{form.name.data}'")
            if len(users) > 0:
                messages.append("The user with the name specified already exists")

            emails = tables.Users.select(columns=['email'], condition=f"'{form.email.data}'")
            if len(emails) > 0:
                messages.append("The email is already occupied by another user")
            
            if form.password.data != form.repeated_password.data:
                messages.append("The passwords should match")

            if messages:
                for m in messages:
                    flash(m)
                return render_template("signup.html", form=form)

            tables.Users.insert(columns=['name', 'email', 'hashed_password'],
                                values=[request.form['name'],
                                request.form['email'],
                                bcrypt.generate_password_hash(request.form['password']).decode('utf-8')])
            
            flash('You have successfully signed up')

            return redirect(url_for('login'))

    return render_template('signup.html', form=form)


@app.route('/profile/')
def profile():
    if 'username' in session:
        user = tables.Users.select(columns=['name', 'email'],
                                   condition=f"name='{session['username']}'")[0]
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


@app.route('/profile/create-new-project/', methods=['GET', 'POST'])
def create_new_project():

    if 'username' not in session:
        return redirect(url_for('login'))

    form = forms.CreateProjectForm()
    if request.method == 'POST':

        if not form.validate_on_submit():
            return render_template('create_new_project.html', form=form)

        # check whether the project with the same name already exists
        projects = tables.Projects.select(columns=['name'],
                                          condition=f"name='{form.name.data}'")
        
        if projects:
            flash('Projects with this name already exists, please choose another')
            return render_template('create_new_project.html', form=form)
        else:
            owner_id = tables.Users.select(columns=['id'],
                                           condition=f"name='{session['username']}'")[0]['id']
            tables.Projects.insert(columns=['name', 'description', 'owner_id'],
                                  values=[form.name.data, form.description.data, owner_id])
            flash(f'Created project {form.name.data}')
            return redirect(url_for('projects'))

    return render_template('create_new_project.html', form=form)


@app.route('/profile/remove-project/<string:project>/')
def remove_project():
    pass


@app.route('/projects/<string:project_name>/upload-files', methods=['POST'])
def upload_files():
    # figure out whether the user is a participant of the project
    # then upload the files and create a new commit
    pass


@app.route('/projects/<string:project_name>/remove-files/', methods=['POST'])
def remove_files(project_name):
    pass


def check_user_has_privelleges_to_make_changes_to_project(username, project_name):
    project_info = tables.Projects.select(columns=['id', 'owner_id'],
                                            condition=f"name='{project_name}'")

    if project_info:
        project_id = project_info[0]['id']
    else:
        flash('The project with the name provided does not exist')
        return redirect(url_for('profile'))

    project_owner_id = project_info[0]['owner_id']
    user_id = tables.Users.select(columns=['id'],
                                    condition=f"name='{username}'")[0]['id']

    participant_ids = tables.Participants.select(columns=['user_id'],
                                                    condition=f"user_id={user_id} AND project_id={project_id}")
    if participant_ids:
        participant_ids = reduce(lambda lst1, lst2: lst1 + lst2, participant_ids)

    if project_owner_id == user_id or user_id in participant_ids:
        return True
    
    return False


@app.route('/projects/<string:project_name>/files/', methods=['GET', 'POST'])
def project_files(project_name):

    """
    check whether the project is public
    and then ether display it or not
    there should be a button to go to the form to make a commit
    """

    if check_user_has_privelleges_to_make_changes_to_project(session['username'], project_name):
        return render_template('project_page.html', project_name=project_name, pagename='Files', user_can_make_changes=True)

    return render_template('project_page.html', project_name=project_name, pagename='Files', user_can_make_changes=False)


@app.route('/projects/<string:project_name>/issues/')
def project_issues(project_name):

    if check_user_has_privelleges_to_make_changes_to_project(session['username'], project_name):
        return render_template('project_issues.html', project_name=project_name, pagename='Issues', user_can_make_changes=True)

    return render_template('project_issues.html', project_name=project_name, pagename='Issues', user_can_make_changes=False)


@app.route('/projects/<string:project_name>/commits/')
def project_commits(project_name):

    if check_user_has_privelleges_to_make_changes_to_project(session['username'], project_name):
        return render_template('project_commits.html', project_name=project_name, pagename='Commits', user_can_make_changes=True)

    return render_template('project_commits.html', project_name=project_name, pagename='Commits', user_can_make_changes=False)


@app.route('/projects/<string:project_name>/participants/')
def project_participants(project_name):

    if check_user_has_privelleges_to_make_changes_to_project(session['username'], project_name):
        return render_template('project_participants.html', project_name=project_name, pagename='Participants', user_can_make_changes=True)

    return render_template('project_participants.html', project_name=project_name, pagename='Participants', user_can_make_changes=False)


@app.route('/profile/change-name/', methods=['GET', 'POST'])
def change_name():
    form = forms.ChangeNameForm()
    if 'username' in session:
        if request.method == 'POST':

            if not form.validate_on_submit():
                return render_template('change_name.html', form=form)

            if form.name.data == session['username']:
                flash("You already have the name '{form.name.data}'")
                return render_template('change_name.html', form=form)

            users = tables.Users.select(columns=['name'],
                                        condition=f"name='{form.name.data}'")
            
            if len(users) > 0:
                flash('The name is already occupied')
                return render_template('change_name.html', form=form)

            tables.Users.update(columns=['name'],
                                values=[form.name.data],
                                condition=f"name='{session['username']}'")
            session['username'] = form.name.data
            flash("The name has been succesfully changed")
            return redirect(url_for('profile'))

        return render_template('change_name.html', form=form)
    return redirect(url_for('login'))


@app.route('/profile/change-email/', methods=['GET', 'POST'])
def change_email():
    form = forms.ChangeEmailForm()
    if 'username' in session:

        if request.method == 'POST':

            if not form.validate_on_submit():
                return render_template('change_email.html', form=form)

            users = tables.Users.select(columns=['email'],
                                        condition=f"name='{session['username']}'")

            if form.email.data == users[0]['email']:
                flash("You already have the email '{form.email.data}'")
                return render_template('change_email.html', form=form)

            # check whether the emails has been occupied by other user
            emails = tables.Users.select(columns=['email'],
                                         condition=f"email='{form.email.data}'")

            if emails:
                flash('The email is already occupied')
                return render_template('change_email.html', form=form)

            tables.Users.update(columns=['email'],
                                values=[form.email.data],
                                condition=f"name='{session['username']}'")

            flash("The email has been succesfully changed")
            return redirect(url_for('profile'))

        return render_template('change_email.html', form=form)

    return redirect(url_for('login'))


@app.route('/profile/change-password/', methods=['GET', 'POST'])
def change_password():
    form = forms.ChangePasswordForm()
    if 'username' in session:

        if request.method == 'POST':

            if not form.validate_on_submit():
                return render_template('change_password.html', form=form)

            if form.validate_on_submit():
                tables.Users.update(columns=['hashed_password'],
                                    values=[bcrypt.generate_password_hash(form.password.data).decode('utf-8')])
                flash("The password has been updated")
                return redirect(url_for('profile'))
            flash("The passwords do not match")
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