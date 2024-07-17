from flask import Blueprint, render_template, request, redirect, url_for, session, flash, Flask, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Table, MetaData
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from datetime import time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import json
from app.models import generate_response, get_restaurants_menus, train_menu_model
import nltk

nltk.download('punkt')
from nltk.tokenize import word_tokenize

# import secrets
# secret_key = secrets.token_hex(16)  # Generates a 32-character hexadecimal key
#app = Flask(__name__)
#app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')  # Set a secret key for flash messages

main = Blueprint('main', __name__)

restaurant_freq_dist = None

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')  # Set a secret key for flash messages

def serialize_row(row):
    serialized_row = {}
    for key, value in row.items():
        if isinstance(value, datetime):
            serialized_row[key] = value.isoformat()
        elif isinstance(value, time):
            serialized_row[key] = value.strftime('%H:%M:%S')
        else:
            serialized_row[key] = value
    return serialized_row

def convert_to_12hr(time_obj):
    if time_obj is None or time_obj == "NULL":
        return "Closed"
    if isinstance(time_obj, str):
        time_24hr = datetime.strptime(time_obj, "%H:%M:%S")
    else:
        time_24hr = datetime.strptime(time_obj.strftime("%H:%M:%S"), "%H:%M:%S")
    return time_24hr.strftime("%I:%M %p")

@main.route('/', methods=['GET', 'POST'])
def homepage():
    try:
        username = session.get('username')
        engine = create_engine("postgresql://SavorSense_owner:iX2EMY6TzLlf@ep-shrill-cloud-a40et0x7.us-east-1.aws.neon.tech/SavorSense?sslmode=require")
        metadata = MetaData()
        metadata.reflect(bind=engine)
        users_table = metadata.tables['users']
        with engine.connect() as connection:
            select_stmt = users_table.select().where(users_table.c.username == username)
            result2 = connection.execute(select_stmt).fetchone()
        cuisine = result2.cuisine if result2 and result2.cuisine else ''
        other_cuisine = result2.cuisine_other if result2 and result2.cuisine_other else ''

        if isinstance(other_cuisine, list):
            other_cuisine = ', '.join(other_cuisine)
        elif other_cuisine:
            other_cuisine = other_cuisine.strip('[]"').replace('", "', ', ') 
        print(f"other_cuisine: {other_cuisine}")
        if isinstance(cuisine, list):
            cuisine = ', '.join(cuisine)
        elif cuisine:
           cuisine = cuisine.strip('[]"').replace('", "', ', ')  

        user_preferences = []
        if cuisine:
            user_preferences.extend([c.lower().strip() for c in cuisine.split(',')])
        if other_cuisine:
            user_preferences.extend([c.lower().strip() for c in other_cuisine.split(',')])
        print(f"UP: {user_preferences}")
        metadata.reflect(bind=engine)
        restaurants_table = metadata.tables['restaurants']
        with engine.connect() as connection:
            result = connection.execute(restaurants_table.select())
            restaurants = result.fetchall()

        restaurant_data = [serialize_row(dict(row._asdict())) for row in restaurants]
        time_data = []
        for row in restaurants:
            restaurant = serialize_row(dict(row._asdict()))
            for day in ['monday', 'tues', 'wed', 'thurs','fri', 'sat','sun']:
                start_key = f'start_hour_{day}'
                end_key = f'end_hour_{day}'
                restaurant[start_key] = convert_to_12hr(restaurant.get(start_key))
                restaurant[end_key] = convert_to_12hr(restaurant.get(end_key))
            time_data.append(restaurant)
        
        def sort_key(restaurant):
            restaurant_cuisines = [restaurant['cuisine'].lower().strip()] if restaurant['cuisine'] else []
            matches = sum(1 for pref in user_preferences if pref in restaurant_cuisines)
            return -matches
        
        sorted_restaurant_data = sorted(restaurant_data, key=sort_key)
        sorted_time_data = sorted(time_data, key=sort_key)

        length = len(restaurants)
        for i in range(len(sorted_restaurant_data)):
            print(f"RD: {sorted_restaurant_data[i]['name']}, {sorted_restaurant_data[i]['cuisine']}")
        
        for i in range(len(sorted_restaurant_data)):
            print(f"TD: {sorted_time_data[i]['name']}, {sorted_time_data[i]['cuisine']}")
        i = 0
        return render_template('homepage.html', time = sorted_time_data, res = sorted_restaurant_data, restaurant=restaurant_data, len = length, i = i, min = min, cuisine=cuisine, other_cuisine=other_cuisine)
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
@main.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template('signup.html')
    
@main.route('/success', methods=['GET', 'POST'])
def success():
    try:
        engine = create_engine("postgresql://SavorSense_owner:iX2EMY6TzLlf@ep-shrill-cloud-a40et0x7.us-east-1.aws.neon.tech/SavorSense?sslmode=require")
        metadata = MetaData()
        metadata.reflect(bind=engine)
        users_table = metadata.tables['users']

        if request.method == 'POST':
            # Get form data from the frontend
            name = request.form.get('name')
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            with engine.connect() as connection:
                # Check if the user already exists in the database
                existing_user = connection.execute(users_table.select().where(users_table.c.username == username).where(users_table.c.email == email)).fetchone()

                if existing_user:
                    # User already exists, handle accordingly (e.g., show an error message)
                    return render_template('signup.html', error_message="User already exists")

                # Insert the new user into the database
                connection.execute(users_table.insert().values(name=name, username=username, email=email, password=password))
                connection.commit()

                # Redirect to a success page
                return redirect(url_for('main.success'))

        # Render the signup page (GET request)
        return render_template('successpage.html')

    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")

    return render_template('successpage.html')

# Create an SQLAlchemy engine (replace with your actual database URL)
db_url = "postgresql://SavorSense_owner:iX2EMY6TzLlf@ep-shrill-cloud-a40et0x7.us-east-1.aws.neon.tech/SavorSense?sslmode=require"
engine = create_engine(db_url)

# Define User model (similar to the previous example)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    username = Column(String, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    password = Column(String)
    dietary = Column(String)
    

def authenticate_user(username, password):
    Session = sessionmaker(bind=engine)
    session = Session()

    user = session.query(User).filter_by(username=username).first()

    if user and user.password == password:
        return True
    else:
        return False

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        entered_username = request.form.get('username')
        entered_password = request.form.get('password')
        if authenticate_user(entered_username, entered_password):
            # Redirect to the profile or homepage route
            session['username'] = entered_username
            #Session = sessionmaker(bind=engine)
            #session = Session()
            #user = session.query(User).filter_by(username=entered_username).first()
            # if user:
            #     user_name = user.name  # Retrieve the user's name from the database
            # else:
            #     user_name = 'Guest'  # Default to 'Guest' if user not found

            #session.close()  # Close the session
            return redirect(url_for('main.homepage'))
            # return render_template('profile.html', user_name=user_name)
        else:
            flash("Invalid credentials. Please try again.", "error")  # Flash an error message
            return redirect(url_for('main.login'))  # Redirect back to the login page

    return render_template('login.html')

@main.route('/profile', methods=['GET', 'POST'])
def profile():
    # Assuming you've already authenticated the user
    # entered_username = request.args.get('username', 'Guest')  # Retrieve the username
    # Session = sessionmaker(bind=engine)
    # session = Session()
    # user = session.query(User).filter_by(username=entered_username).first()
    # if user:
    #     user_name = user.name
    # else:
    #     user_name = 'Guest'
    # session.close()
    # return render_template('profile.html', user_name=user_name)
    # Retrieve the username from the cookie
    username = session.get('username')
    print(username)
    if not username:
        return render_template('notlogin.html')

    Session = sessionmaker(bind=engine)
    db_session = Session()
    user = db_session.query(User).filter_by(username=username).first()
    name = user.name if user else 'Guest'
    age = user.age if user else ''
    try:
        metadata = MetaData()
        metadata.reflect(bind=engine)
        users_table = metadata.tables['users']
        with engine.connect() as connection:
            select_stmt = users_table.select().where(users_table.c.username == username)
            result = connection.execute(select_stmt).fetchone()
        dietary = result.dietary if result and result.dietary else ''
        cuisine = result.cuisine if result and result.cuisine else ''
        other_dietary = result.dietary_other if result and result.dietary_other else ''
        other_cuisine = result.cuisine_other if result and result.cuisine_other else '' 
        allergies = result.allergies if result and result.allergies else ''

        if isinstance(other_dietary, list):
            other_dietary = ', '.join(other_dietary)
        elif other_dietary:
            other_dietary = other_dietary.strip('[]"').replace('", "', ', ')

        if isinstance(other_cuisine, list):
            other_cuisine = ', '.join(other_cuisine)
        elif other_cuisine:
            other_cuisine = other_cuisine.strip('[]"').replace('", "', ', ')

        if isinstance(allergies, list):
            allergies = ', '.join(allergies)
        elif allergies:
            allergies = allergies.strip('[]"').replace('", "', ', ')

        print(dietary)
    except SQLAlchemyError as e:
        flash(f'An error occurred: {e}', 'danger')
        return redirect(url_for('main.login'))
    
    db_session.close()
    #user_name = request.cookies.get('username', 'Guest')  # Default to 'Guest' if not provided

    return render_template('profile.html', name=name, user_name=username, age=age, dietary=dietary, cuisine=cuisine, other_dietary=other_dietary, other_cuisine=other_cuisine, allergies=allergies)

@main.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('main.login'))

@main.route('/delete', methods=['GET', 'POST'])
def delete():
    try:
        username = request.form.get('username')
        if not username:
            flash('No username provided', 'error')
            return redirect(url_for('main.profile'))

        engine = create_engine("postgresql://SavorSense_owner:iX2EMY6TzLlf@ep-shrill-cloud-a40et0x7.us-east-1.aws.neon.tech/SavorSense?sslmode=require")
        metadata = MetaData()
        metadata.reflect(bind=engine)
        users_table = metadata.tables['users']

        with engine.connect() as connection:
            # Delete the user from the database
            connection.execute(users_table.delete().where(users_table.c.username == username))
            connection.commit()

        session.pop('username', None)
        return redirect(url_for('main.homepage'))

    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        flash('An error occurred while deleting the user', 'error')
        return redirect(url_for('main.profile'))

@main.route('/update_age', methods=['POST'])
def update_age():
    try:
        # Get the username and new age from the form
        username = request.form.get('username')
        new_name = request.form.get('name')
        new_age = request.form.get('age')
        print(new_age)
        # Update the user's age in the database
        engine = create_engine("postgresql://SavorSense_owner:iX2EMY6TzLlf@ep-shrill-cloud-a40et0x7.us-east-1.aws.neon.tech/SavorSense?sslmode=require")
        metadata = MetaData()
        metadata.reflect(bind=engine)
        users_table = metadata.tables['users']

        with engine.connect() as connection:
            connection.execute(users_table.update().where(users_table.c.username == username).values(name=new_name, age=new_age))
            connection.commit()

        flash('Age updated successfully.', 'success')
        return redirect(url_for('main.profile'))
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        flash('An error occurred while updating your age. Please try again.', 'danger')
        return redirect(url_for('main.profile'))

@main.route('/dietary', methods=['GET', 'POST'])
def dietary():
    if 'username' not in session:
        flash('You must be logged in to update your preferences', 'danger')
        return redirect(url_for('main.login'))

    username = session['username']
    dietary_preferences = request.form.getlist('dietary-preferences')
    other_dietary = request.form.getlist('dietary-other')
    dietary_preferences_json = json.dumps(other_dietary) 
    print(other_dietary)
    try:
        engine = create_engine("postgresql://SavorSense_owner:iX2EMY6TzLlf@ep-shrill-cloud-a40et0x7.us-east-1.aws.neon.tech/SavorSense?sslmode=require")
        metadata = MetaData()
        metadata.reflect(bind=engine)
        users_table = metadata.tables['users']
        with engine.connect() as connection:
            connection.execute(users_table.update().where(users_table.c.username == username)
                .values(dietary=dietary_preferences, dietary_other=other_dietary))
            connection.commit()
        print("Successful commit")
    except SQLAlchemyError as e:
        flash(f'An error occurred: {e}', 'danger')

    return redirect(url_for('main.profile'))

@main.route('/cuisine', methods=['GET', 'POST'])
def cuisine():
    if 'username' not in session:
        flash('You must be logged in to update your preferences', 'danger')
        return redirect(url_for('main.login'))

    username = session['username']
    cuisine_preferences = request.form.getlist('cuisine-preferences')
    other_cuisine = request.form.getlist('cuisine-other')
    print(cuisine_preferences)
    try:
        engine = create_engine("postgresql://SavorSense_owner:iX2EMY6TzLlf@ep-shrill-cloud-a40et0x7.us-east-1.aws.neon.tech/SavorSense?sslmode=require")
        metadata = MetaData()
        metadata.reflect(bind=engine)
        users_table = metadata.tables['users']
        with engine.connect() as connection:
            connection.execute(users_table.update().where(users_table.c.username == username)
                .values(cuisine=cuisine_preferences, cuisine_other=other_cuisine))
            connection.commit()
        print("Successful commit")
    except SQLAlchemyError as e:
        flash(f'An error occurred: {e}', 'danger')

    return redirect(url_for('main.profile'))

@main.route('/allergies', methods=['GET', 'POST'])
def allergies():
    if 'username' not in session:
        flash('You must be logged in to update your preferences', 'danger')
        return redirect(url_for('main.login'))

    username = session['username']
    allergy_preferences = request.form.getlist('allergies')
    print("Allergies: %s" % allergy_preferences)
    try:
        engine = create_engine("postgresql://SavorSense_owner:iX2EMY6TzLlf@ep-shrill-cloud-a40et0x7.us-east-1.aws.neon.tech/SavorSense?sslmode=require")
        metadata = MetaData()
        metadata.reflect(bind=engine)
        users_table = metadata.tables['users']
        with engine.connect() as connection:
            connection.execute(users_table.update().where(users_table.c.username == username)
                .values(allergies=allergy_preferences))
            connection.commit()
        print("Successful commit")
    except SQLAlchemyError as e:
        flash(f'An error occurred: {e}', 'danger')

    return redirect(url_for('main.profile'))  

@main.route('/forget')
def forget():
    return render_template('forget.html')

@main.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    if not user_message:
        return jsonify({'response': 'Please enter a message.'})
    
    bot_response = generate_response(user_message)
    return jsonify({'response': bot_response})


@main.route("/", methods=["GET"])
def read_root():
    return jsonify({"message": "Welcome to the chatbot with NLTK processing!"})