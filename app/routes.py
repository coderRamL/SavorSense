from flask import Blueprint, render_template
from sqlalchemy import create_engine, Column, Integer, String, Table, MetaData
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from datetime import time

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

@main.route('/')
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
        print(restaurant_data)
        length = len(restaurants)
        print(length)
        i = 0
        return render_template('homepage.html', res = restaurants, restaurant=restaurant_data, len = length, i = i)
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")

@main.route('/signup')
def signup():
    return render_template('signup.html')
@main.route('/login')
def login():
    return render_template('login.html')

@main.route('/profile')
def profile():
    return render_template('profile.html')