from flask import Blueprint, render_template, request, redirect, url_for, session
from sqlalchemy import create_engine, Column, Integer, String, Table, MetaData
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from datetime import time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

main = Blueprint('main', __name__)

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
        engine = create_engine("postgresql://SavorSense_owner:iX2EMY6TzLlf@ep-shrill-cloud-a40et0x7.us-east-1.aws.neon.tech/SavorSense?sslmode=require")
        metadata = MetaData()
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
        print(restaurant_data)
        length = len(restaurants)
        print(length)
        print(time_data[1]['start_hour_monday'])
        i = 0
        return render_template('homepage.html', time = time_data, res = restaurants, restaurant=restaurant_data, len = length, i = i, min = min)
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

@main.route('/login', methods=['GET', 'POST'])
def login():
    # Create an SQLAlchemy engine (replace with your actual database URL)
    db_url = "postgresql://SavorSense_owner:iX2EMY6TzLlf@ep-shrill-cloud-a40et0x7.us-east-1.aws.neon.tech/SavorSense?sslmode=require"
    engine = create_engine(db_url)
    
    # Define User model (similar to the previous example)
    Base = declarative_base()
    
    class User(Base):
        __tablename__ = 'Users'
        username = Column(String, primary_key=True)
        password = Column(String)

    # Authenticate user
    def authenticate_user(username, password):
        Session = sessionmaker(bind=engine)
        session = Session()
    
        if request.method == 'POST':
            entered_username = request.form.get('username')
            entered_password = request.form.get('password')
            if authenticate_user(entered_username, entered_password):
                # Redirect to the profile or homepage route
                return redirect(url_for('profile'))
            else:
                return "Invalid credentials. Please try again."
    return render_template('login.html')

@main.route('/profile')
def profile():
    return render_template('profile.html')

@main.route('/forget')
def forget():
    return render_template('forget.html')