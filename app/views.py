from app import app, db, bcrypt, tables
from flask import request, render_template, session, redirect, url_for, flash
from app import forms
from sqlalchemy import text
from functools import reduce
from werkzeug.utils import secure_filename
import os
import time
from random import randint


# authentication blueprint
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
                    flash("Wrong password", category='error')
            else:
                flash("User with this name does not exist", category='error')

    return render_template('login.html', form=form)


@app.route('/logout/')
def logout():
    if 'username' in session:
        session.pop('username')
    return redirect(url_for('login'))


@app.route('/signup/', methods=['GET', 'POST'])
def signup():

    if 'username' in session:
        return redirect(url_for('profile'))

    form = forms.SignupForm()
    if request.method == 'POST':

        if form.validate_on_submit():

            messages = []

            # check whether the name specified is occupied
            users = tables.Users.select(columns=['name'], condition=f"name='{form.name.data}'")
            if users:
                messages.append("The user with the name specified already exists")

            emails = tables.Users.select(columns=['email'], condition=f"'{form.email.data}'")
            if emails:
                messages.append("The email is already occupied by another user")
            
            if form.password.data != form.repeated_password.data:
                messages.append("The passwords should match")

            if messages:
                for m in messages:
                    flash(m, category='error')
                return render_template("signup.html", form=form)

            tables.Users.insert(columns=['name', 'email', 'hashed_password'],
                                values=[request.form['name'],
                                request.form['email'],
                                bcrypt.generate_password_hash(request.form['password']).decode('utf-8')])
            
            flash('You have successfully signed up', category='success')

            return redirect(url_for('login'))

    return render_template('signup.html', form=form)


# profile blueprint
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

        return render_template('contributions.html', pagename='Contributions', projects=projects)
    return redirect(url_for('login'))


@app.route('/profile/create-new-project/', methods=['GET', 'POST'])
def create_new_project():

    if 'username' not in session:
        return redirect(url_for('login'))

    form = forms.CreateProjectForm()
    if request.method == 'POST':

        if form.validate_on_submit():

            # check whether the project with the same name already exists
            projects = tables.Projects.select(columns=['name'],
                                            condition=f"name='{form.name.data}'")
            
            if projects:
                flash('Projects with this name already exists, please choose another', category='error')
                return render_template('create_new_project.html', form=form)
            else:
                owner_id = tables.Users.select(columns=['id'],
                                               condition=f"name='{session['username']}'")[0]['id']
                tables.Projects.insert(columns=['name', 'description', 'owner_id'],
                                       values=[form.name.data, form.description.data, owner_id])
                flash(f'Created project {form.name.data}', category='success')
                return redirect(url_for('project_files', project_name=form.name.data))

    return render_template('create_new_project.html', form=form)


@app.route('/profile/remove-project/<string:project_name>/', methods=['GET', 'POST'])
def remove_project(project_name):

    if 'username' not in session:
        return redirect(url_for('login'))

    form = forms.RemoveProjectConfirmationForm()

    if request.method == 'POST':

        if form.answer.data == 'yes':
            check = check_project_belongs_to_user(project_name, session['username'])
            if check['belongs']:
                tables.Projects.delete(condition=f"name='{project_name}'")
                flash(f"The project '{project_name}' has bene successfully removed", category='success')
            else:
                flash('You have no permission to remove this project, only the owner of the project can do this', category='error')

        return redirect(url_for('projects'))

    return render_template('remove-project.html', form=form)
    

@app.route('/profile/add-participant/<string:project_name>/', methods=['GET', 'POST'])
def add_participant(project_name):

    if 'username' not in session:
        return redirect(url_for('login'))

    form = forms.AddParticipantForm()
    if request.method == 'POST':

        if form.validate_on_submit():
            check = check_project_belongs_to_user(project_name, session['username'])
            if not check['belongs']:
                flash('You do not have the required privileges to add contributors to this project')
                return redirect(url_for('projects'))
            
            # get id of the user from the form
            user = tables.Users.select(columns=['id'],
                                       condition=f"name='{form.name.data}'")
            if not user:
                flash(f"The user with the name '{form.name.data}' does not exist")
                return redirect(url_for('add_participant', project_name=project_name))
            else:
                user_id = user[0]['id']
            print(user_id)

            # check whether the user is already a participant of the project
            participant = tables.Participants.select(columns=['id'],
                                                     condition=f"user_id={user_id} AND project_id={check['project_id']}")

            if participant:
                flash(f"The user '{form.name.data}' is already a member of the project", category='error')
                return redirect(url_for('add_participant', project_name=project_name))
            else:
                tables.Participants.insert(columns=['user_id', 'project_id'],
                                           values=[user_id, check['project_id']])
                flash(f"The user '{form.name.data}' has been added as member to the project {project_name}", category='success')
            
    return render_template('add_participant.html', form=form, project_name=project_name)
    

@app.route('/profile/remove-participant/<string:project_name>/', methods=['GET', 'POST'])
def remove_participant(project_name):

    if 'username' not in session:
        return redirect(url_for('login'))

    form = forms.RemoveParticipantForm()
    if request.method == 'POST':

        check = check_project_belongs_to_user(project_name, session['username'])
        if not check['belongs']:
            flash('You do not have the required privileges to add contributors to this project')
            return redirect(url_for('projects'))
        else:

            # check whether the user is already a participant of the project
            participant = tables.Participants.select(columns=['id'],
                                                     condition=f"user_id={check['user_id']} AND project_id={check['project_id']}")
            if not participant:
                flash(f"The user '{form.name.data}' is not a member of the project", category='error')
                return redirect(url_for('add_participant', project_name=project_name))

            tables.Participants.delete(condition=f"user_id={check['user_id']} AND project_id={check['project_id']}")
            flash(f"The user '{form.name.data}' has been successfuly removed from the the project '{project_name}'", category='success')

    return render_template('remove_participant.html', form=form, project_name=project_name)


@app.route('/profile/change-name/', methods=['GET', 'POST'])
def change_name():

    if 'username' not in session:
        return redirect(url_for('login'))

    form = forms.ChangeNameForm()
    if request.method == 'POST':

        if form.validate_on_submit():

            if form.name.data == session['username']:
                flash("You already have the name '{form.name.data}'", category='error')
                return render_template('change_name.html', form=form)

            users = tables.Users.select(columns=['name'],
                                        condition=f"name='{form.name.data}'")
            
            if len(users) > 0:
                flash('The name is already occupied', category='error')
                return render_template('change_name.html', form=form)

            tables.Users.update(columns=['name'],
                                values=[form.name.data],
                                condition=f"name='{session['username']}'")
            session['username'] = form.name.data
            flash('The name has been succesfully changed', category='success')
            return redirect(url_for('profile'))

    return render_template('change_name.html', form=form)


@app.route('/profile/change-email/', methods=['GET', 'POST'])
def change_email():

    if 'username' not in session:
        return redirect(url_for('login'))

    form = forms.ChangeEmailForm()
    if request.method == 'POST':

        if form.validate_on_submit():
           

            users = tables.Users.select(columns=['email'],
                                        condition=f"name='{session['username']}'")

            if form.email.data == users[0]['email']:
                flash("You already have the email '{form.email.data}'", category='error')
                return render_template('change_email.html', form=form)

            # check whether the emails has been occupied by another user
            emails = tables.Users.select(columns=['email'],
                                            condition=f"email='{form.email.data}'")

            if emails:
                flash('The email is already occupied', category='error')
                return render_template('change_email.html', form=form)

            tables.Users.update(columns=['email'],
                                values=[form.email.data],
                                condition=f"name='{session['username']}'")

            flash("The email has been succesfully changed", category='success')
            return redirect(url_for('profile'))

    return render_template('change_email.html', form=form)


@app.route('/profile/change-password/', methods=['GET', 'POST'])
def change_password():

    if 'username' not in session:
        return redirect(url_for('login'))

    form = forms.ChangePasswordForm()
    if request.method == 'POST':

        if form.validate_on_submit():
            tables.Users.update(columns=['hashed_password'],
                                values=[bcrypt.generate_password_hash(form.password.data).decode('utf-8')])
            flash('The password has been updated', category='success')
            return redirect(url_for('profile'))
        flash('The passwords do not match', category='error')
    return render_template('change_password.html', form=form)


# projects blueprint
@app.route('/projects/<string:project_name>/upload-files/', methods=['GET', 'POST'])
def make_commit(project_name):

    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        privileges = check_user_has_privileges_to_make_changes_to_project(session['username'],  project_name)

        if privileges['user_can_make_changes']:

            project_path = os.path.join(app.config['UPLOAD_FOLDER'], project_name)
            if not os.path.exists(project_path):
                os.mkdir(project_path)


            files = request.files.getlist("file")

            commit_numbers = os.listdir(project_path)
            if commit_numbers:
                new_commit_number = max(list(map(int, commit_numbers))) + 1
            else:
                new_commit_number = 1

            commit_path = os.path.join(project_path, str(new_commit_number))
            os.mkdir(commit_path)

            for file in files:
                filename = secure_filename(file.filename)
                file.save(os.path.join(commit_path, filename))
            flash('The files had been commited to the project', category='success')
            return redirect(url_for('project_files', project_name=project_name))
    
    return render_template('new_commit_form.html')


@app.route('/projects/<string:project_name>/files/', methods=['GET', 'POST'])
def project_files(project_name):

    privileges = check_user_has_privileges_to_make_changes_to_project(session['username'], project_name)
    project_dir = os.path.join(app.config['UPLOAD_FOLDER'], project_name)
    commits = os.listdir(project_dir)
    last_commit_number = ''
    file_names = []
    if commits:
        last_commit_number = max(list(map(int, commits)))
        file_names = os.listdir(os.path.join(project_dir, str(last_commit_number)))
    return render_template('project_page.html',
                           project_name=project_name,
                           pagename='Files',
                           user_can_make_changes=privileges['user_can_make_changes'],
                           user_is_admin=privileges['user_is_admin'], 
                           file_names=file_names,
                           commit_name=last_commit_number)


@app.route('/projects/<string:project_name>/<commit_number>/files/', methods=['GET', 'POST'])
def see_commit(project_name, commit_number):

    privileges = check_user_has_privileges_to_make_changes_to_project(session['username'], project_name)
    project_dir = os.path.join(app.config['UPLOAD_FOLDER'], project_name)
    commits = os.listdir(project_dir)
    if not str(commit_number) in commits:
        return redirect(url_for('project_commits', project_name=project_name))

    file_names = []
    if commits:
        file_names = os.listdir(os.path.join(project_dir, str(commit_number)))
    return render_template('project_page.html',
                           project_name=project_name,
                           pagename='Files',
                           user_can_make_changes=privileges['user_can_make_changes'],
                           user_is_admin=privileges['user_is_admin'], 
                           file_names=file_names,
                           commit_name=commit_number)


@app.route('/projects/<string:project_name>/<commit_number>/<file_name>/', methods=['GET', 'POST'])
def see_file_contents(project_name, commit_number, file_name):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], project_name, commit_number, file_name)
    with open(file_path, 'r') as f:
        content = f.read()
    return render_template("file_contents.html", content=content, file_name=file_name, project_name=project_name)


@app.route('/projects/<string:project_name>/issues/')
def project_issues(project_name):

    privileges = check_user_has_privileges_to_make_changes_to_project(session['username'], project_name)
    project_id = tables.Projects.select(columns=['id'],
                                        condition=f"name='{project_name}'")[0]['id']
    issues = tables.Issues.select(columns=['name', 'description'],
                                  condition=f"project_id='{project_id}'")
    return render_template('project_issues.html',
                           project_name=project_name,
                           pagename='Issues',
                           user_can_make_changes=privileges['user_can_make_changes'],
                           user_is_admin=privileges['user_is_admin'],
                           issues=issues)


@app.route('/projects/<string:project_name>/commits/')
def project_commits(project_name):

    privileges = check_user_has_privileges_to_make_changes_to_project(session['username'], project_name)
    project_dir = os.path.join(app.config['UPLOAD_FOLDER'], project_name)
    commits = sorted(os.listdir(project_dir))

    return render_template('project_commits.html',
                           project_name=project_name,
                           pagename='Commits',
                           user_can_make_changes=privileges['user_can_make_changes'],
                           user_is_admin=privileges['user_is_admin'],
                           commits=commits)


@app.route('/projects/<string:project_name>/add-issue/', methods=['GET', 'POST'])
def add_issues(project_name):

    form = forms.AddProjectIssuesForm()
    if request.method == 'POST':

        # find project id
        project = tables.Projects.select(columns=['id'],
                                         condition=f"name='{project_name}'")
        if not project:
            flash('The project does not exist', category='error')
            return redirect(url_for('projects'))
        else:
            project_id = project[0]['id']

        tables.Issues.insert(columns=['project_id', 'name', 'description'],
                             values=[project_id, form.name.data, form.description.data])
        flash('The issue has been submitted', category='success')

        return redirect(url_for('projects', project_name=project_name))
    
    return render_template('submit_issues.html', form=form, project_name=project_name)


# put it into utils.py
def check_user_has_privileges_to_make_changes_to_project(username, project_name):

    res = {}
    project_info = tables.Projects.select(columns=['id', 'owner_id'],
                                            condition=f"name='{project_name}'")

    if project_info:
        project_id = project_info[0]['id']
    else:
        flash('The project with the name provided does not exist', category='error')
        return redirect(url_for('profile'))

    project_owner_id = project_info[0]['owner_id']
    user_id = tables.Users.select(columns=['id'],
                                    condition=f"name='{username}'")[0]['id']

    participant_ids = tables.Participants.select(columns=['user_id'],
                                                    condition=f"user_id={user_id} AND project_id={project_id}")
    if participant_ids:
        print(participant_ids)
        participant_ids = reduce(lambda lst1, lst2: lst1['user_id'] + lst2['user_id'], participant_ids)

    res['user_can_make_changes'] = user_id in participant_ids or project_owner_id == user_id
    res['user_is_admin'] = project_owner_id == user_id
    res['project_id'] = project_id
    
    return res


def check_project_belongs_to_user(project_name, user_name):

    result = {'belongs': False,}

    # check the user exists
    user = tables.Users.select(columns=['id'],
                        condition=f"name='{user_name}'")
    if not user:
        flash(f"The user {user_name} does not exist", category='error')
    
    # check the project_exists
    project = tables.Projects.select(columns=['id', 'owner_id'],
                        condition=f"name='{project_name}'")
    if not project:
        flash(f"The project {project_name} does not exist", category='error')
        return False
    
    user_id = user[0]['id']
    project_owner_id = project[0]['owner_id']

    result['user_id'] = user_id
    result['owner_id'] = project_owner_id
    result['project_id'] =  project[0]['id']
    result['belongs'] = user_id == project_owner_id
    
    return result