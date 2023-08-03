import random
from flask import Flask, render_template, request, flash, redirect, url_for,session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, logout_user, login_user, current_user
from werkzeug.                     security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy() 
login_manager = LoginManager()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mcq_database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '12233445566'


db.init_app(app)
login_manager.login_view = 'login'
login_manager.init_app(app)
login_manager.login_message = u"Please login first to access the page, create account if not yet registred!."
login_manager.login_message_category = "info"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key="True")
    evsu_mail = db.Column(db.String(100), unique=True)
    student_id =db.Column(db.String(100))
    full_name = db.Column(db.String(100))
    age = db.Column(db.String(100))
    year_section = db.Column(db.String(100))
    password = db.Column(db.String(100))


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.relationship('Question', backref='subject', cascade='all, delete-orphan')


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    choices = db.relationship('Choice', backref='question', cascade='all, delete-orphan')


class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    choice_text = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)


class UserScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stud_name = db.Column(db.String(100), nullable=False) 
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.template_filter('alphabetic')
def alphabetic_filter(index):
    return chr(ord('A') + index - 1)


@app.route('/signup', methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        student_id = request.form.get("student_id")
        year_section = request.form.get("year_section")
        age = request.form.get("age")
        evsu_mail = request.form.get("evsu_mail")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password") 

        user = User.query.filter_by(evsu_mail=evsu_mail).first()

        if user:
            flash("Evsu mail used already exist, use another one!", category="error")
            return redirect(url_for('signup'))
        elif password != confirm_password:
            flash("The confirm password entered doesnt match with your current password", category="error")   
            return redirect(url_for('signup'))
        else:
            new_user = User(full_name=full_name, student_id=student_id, year_section=year_section, age=age, evsu_mail=evsu_mail, password=generate_password_hash(password, method='sha256'))   
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash("You have logged in succesfully, You can now take the MCQ test", category="success")   
            return redirect(url_for("dashboard"))
    return render_template("signup.html", user=current_user)


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        evsu_mail = request.form.get('evsu_mail')
        password = request.form.get('password')

        user = User.query.filter_by(evsu_mail=evsu_mail).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('dashboard'))
            else:
                flash('You have entered incorrect password, try again!.', category='error')
                return redirect(url_for('login'))
        else:
            flash('You have entered unregistred or incorrect email, try again!.', category='error')
            return redirect(url_for('login'))

    return render_template("login.html", user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have logged out succesfully", category="success")
    return redirect(url_for('home'))


@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get(user_id)

    if user:
        return render_template('profile.html', user=user)
    else:
        flash(f'User with ID {user_id} not found.', 'error')
        return redirect(url_for('home'))


@app.route('/', methods=["POST", "GET"])
def home():
    return render_template("index.html", user=current_user)


@app.route('/dashboard')
@login_required
def dashboard():
    sub = Subject.query.all()
    return render_template("dashboard.html", sub=sub, user=current_user)


@app.route('/all-users')
@login_required
def all_users():
    users = User.query.all()
    return render_template("users.html", users=users, user=current_user)


@app.route('/add-sub', methods=["POST", "GET"])
@login_required
def add_sub():
    if request.method == "POST":
        name = request.form.get("name")

        new_sub = Subject(name=name)
        db.session.add(new_sub)
        db.session.commit()
        flash(f'{new_sub.name} added succesfully!', category="success")

        return redirect(url_for("dashboard"))


@app.route('/add-question/<int:subject_id>', methods=['GET', 'POST'])
def add_question(subject_id):
    subject = Subject.query.get(subject_id)
    if request.method == 'POST':
        question_text = request.form['question_text']
        choices = request.form.getlist('choice_text')
        is_correct = request.form.getlist('is_correct')

        question = Question(question_text=question_text, subject=subject)
        db.session.add(question)
        db.session.commit()

        for i, choice_text in enumerate(choices):
            is_choice_correct = True if str(i) in is_correct else False
            choice = Choice(choice_text=choice_text, is_correct=is_choice_correct, question=question)
            db.session.add(choice)

        db.session.commit()
        flash("You have added a new question successfully.", category="success")
        return redirect(f'/add-question/{subject_id}')

    return render_template('add-question.html', subject=subject)


@app.route('/delete-user/<int:id>', methods=["POST", "GET"])
@login_required
def delete_user(id):
    user = User.query.filter_by(id=id).first()
    db.session.delete(user)
    db.session.commit()
    flash("User Deleted")
    return redirect(url_for("all_users"))
    

@app.route("/delete-question/<int:question_id>", methods=['GET', 'POST'])
def delete_questions(question_id):
    question = Question.query.get(question_id)

    if question:
        choices = Choice.query.filter_by(question_id=question_id).all()
        for choice in choices:
            db.session.delete(choice)
        
        db.session.delete(question)
        db.session.commit()

        flash('Successfully deleted question', category="success")
    else:
        flash("question not found", category='error')

    return redirect(url_for('dashboard'))  


@app.route("/delete-subject/<int:subject_id>", methods=['GET', 'POST'])
def delete_subject(subject_id):
    subject = Subject.query.get(subject_id)

    if subject:
        for question in subject.questions:
            choices = Choice.query.filter_by(question_id=question.id).all()
            for choice in choices:
                db.session.delete(choice)    
            db.session.delete(question)

        db.session.delete(subject)    
        db.session.commit()

        flash(f'{subject.name} deleted successfully', category="success")
    else:
        flash("Subject not found", category='error')

    return redirect(url_for('dashboard'))     


@app.route('/take_test/<int:subject_id>', methods=['GET', 'POST'])
def take_test(subject_id):
    subject = Subject.query.get(subject_id)
    total_questions = len(subject.questions)

    if request.method == 'POST':      
        current_user_id = f'{current_user.full_name}'

        UserScore.query.filter_by(stud_name=current_user_id, subject_id=subject_id).delete()

        score = 0
        for question in subject.questions:
            user_choice = request.form.get(f'question_{question.id}')


            if user_choice is not None:
                choice = Choice.query.get(int(user_choice))
              
                if choice.is_correct:
                    score += 1
                

        user_score = UserScore(stud_name=current_user_id, subject_id=subject_id, score=score)
        db.session.add(user_score)
        db.session.commit()

        flash('Your test score has been updated successfully!', 'success')
        return redirect(url_for('display_score', subject_id=subject_id, score=score))

    randomized_questions = random.sample(subject.questions, len(subject.questions))
    for question in randomized_questions:
        question.randomized_choices = random.sample(question.choices, len(question.choices))

    return render_template('take_test.html', subject=subject, randomized_questions=randomized_questions)


@app.route('/display_score/<int:subject_id>/<int:score>')
def display_score(subject_id, score):
    subject = Subject.query.get(subject_id)
    total_questions = len(subject.questions)


    randomized_questions = random.sample(subject.questions, len(subject.questions))
    for question in randomized_questions:
        question.randomized_choices = random.sample(question.choices, len(question.choices))

    return render_template('display_score.html', subject=subject, randomized_questions=randomized_questions, score=score, )

@app.route('/student_scores/<int:subject_id>')
def student_scores(subject_id):
    subject = Subject.query.get(subject_id)
    total_questions = len(subject.questions)
    students_scores = {}

    for user in User.query.all():
     
        user_scores = UserScore.query.filter_by(stud_name=f'{user.full_name}', subject_id=subject_id).all()

        if user_scores:
            total_score = sum(score.score for score in user_scores)
            num_attempts = len(user_scores)

            percentage_correct = (total_score / (total_questions * num_attempts)) * 100

            if percentage_correct == 100:
                color = 'green'
            elif percentage_correct >= 75:
                color = 'blue'
            else:
                color = 'red'

            students_scores[user.id] = {
                'full_name': user.full_name,
                'student_id': user.student_id,
                'year_section': user.year_section,
                'score': total_score,
                'color': color,
            }

    return render_template('student_scores.html', subject=subject, students_scores=students_scores)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)