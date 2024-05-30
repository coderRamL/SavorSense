from flask import Blueprint, render_template


main = Blueprint('main', __name__)

@main.route('/')
def homepage():
    return render_template('homepage.html')
@main.route('/signup')
def signup():
    return render_template('signup.html')
@main.route('/login')
def login():
    return render_template('login.html')

@main.route('/profile')
def profile():
    return render_template('profile.html')