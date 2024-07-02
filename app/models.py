import random
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.probability import FreqDist
import psycopg2
import re
from psycopg2 import sql
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

nltk.download('punkt')
nltk.download('stopwords')

food_recommendations = {
    'vegetarian': ['Vegetable Stir Fry', 'Veggie Burger', 'Pasta Primavera'],
    'vegan': ['Vegan Tacos', 'Vegan Buddha Bowl', 'Vegan Burger'],
    'gluten-free': ['Grilled Chicken Salad', 'Gluten-Free Pizza', 'Quinoa Salad'],
    'keto': ['Keto Salad', 'Keto Burger', 'Grilled Chicken'],
    # Add more categories and food items as needed
}

GREETING_INPUTS = ("hello", "hi", "greetings", "sup", "what's up","hey", "hola", "bonjour", "nihao")
GREETING_RESPONSES = ["Hi! How can I help you today?"]

def greeting(sentence):
    """If user's input is a greeting, return a greeting response"""
    for word in sentence:
        if word.lower() in GREETING_INPUTS:
            return random.choice(GREETING_RESPONSES)
    return None

def connect_db():
    database_url = "postgresql://SavorSense_owner:iX2EMY6TzLlf@ep-shrill-cloud-a40et0x7.us-east-1.aws.neon.tech/SavorSense?sslmode=require"
    conn = psycopg2.connect(database_url)
    return conn 

def get_restaurant_recommendations(cuisine_type):
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT name FROM restaurants WHERE cuisine = %s ORDER BY rating DESC, num_reviews DESC LIMIT 5")
    cur.execute(query, [cuisine_type])
    results = cur.fetchall()
    print(f"Restaurant results: {results}")
    cur.close()
    conn.close()
    return [result[0] for result in results]

def get_restaurants_by_rating(min_rating):
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT name FROM restaurants WHERE rating >= %s ORDER BY rating DESC LIMIT 5")
    cur.execute(query, [min_rating])
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [result[0] for result in results]

def get_restaurants_by_price(price_range):
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT name FROM restaurants WHERE low_price <= %s and high_price >= %s ORDER BY rating DESC LIMIT 5")
    cur.execute(query, [price_range, price_range])
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [result[0] for result in results]

def get_restaurants_by_reviews(min_reviews):
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT name FROM restaurants WHERE num_reviews >= %s ORDER BY num_reviews DESC, rating DESC LIMIT 5")
    cur.execute(query, [min_reviews])
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [result[0] for result in results]

def get_restaurants_by_hours(day, time):
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL(f"SELECT name FROM restaurants WHERE start_hour_{day} <= %s AND end_hour_{day} >= %s ORDER BY rating DESC LIMIT 5")
    cur.execute(query, [time, time])
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [result[0] for result in results]

def parse_time(word):
    """
    Try to parse the time in 12-hour format with AM/PM.
    Return the time object.
    """
    try:
        # Try 12-hour format with AM/PM
        return datetime.strptime(word, "%I:%M %p").time()
    except ValueError:
        return None

def extract_time_phrase(input_text):
    """
    Extract the time phrase from the user input.
    """
    match = re.search(r'\b\d{1,2}:\d{2}\s?(AM|PM|am|pm)\b', input_text, re.IGNORECASE)
    if match:
        return match.group(0)
    return None

def extract_offset_phrase(input_text):
    match = re.search(r'\b(\d+)\s?(minutes?|hours?|days?)\s?\b', input_text, re.IGNORECASE)
    if match:
        return int(match.group(1)), match.group(2).lower()
    return None, None

def calculate_future_time(offset_value, offset_unit):
    now = datetime.now()
    if offset_unit.startswith('minute'):
        future_time = now + timedelta(minutes=offset_value)
    elif offset_unit.startswith('hour'):
        future_time = now + timedelta(hours=offset_value)
    elif offset_unit.startswith('day'):
        future_time = now + timedelta(days=offset_value)
    else:
        future_time = now
    return future_time

def get_current_time():
    now = datetime.now()
    return now.strftime("%I:%M %p"), now.strftime("%H:%M")

def get_current_day_and_time():
    now = datetime.now()
    return now.strftime("%A").lower(), now.strftime("%H:%M"), now.strftime("%I:%M %p")

def get_restaurants_menus():
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT menu FROM restaurants")
    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [result[0] for result in results]

# Preprocess input text
def preprocess_text(text):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    filtered_text = [w.lower() for w in word_tokens if not w in stop_words]
    return filtered_text

# Train NLTK model using menu data
def train_menu_model(menus):
    all_words = []
    for menu in menus:
        tokens = preprocess_text(menu)
        all_words.extend(tokens)
    freq_dist = FreqDist(all_words)
    return freq_dist

# Generate a response based on user input
def generate_response(user_input):
    processed_input = preprocess_text(user_input)
    if greeting(processed_input) != None:
        return greeting(processed_input)
    
    cuisine_types = ["Italian", "Mexican", "Japanese", "Indian", "Thai", "Chinese", "French", "Mediterranean", "Middle Eastern", "American", "Korean", "Vietnamese", "Burmese", "German", "Other"]
    days_of_week = ["monday", "tues", "wed", "thurs", "fri", "sat", "sun"]
    
    for cuisine in cuisine_types:
        if cuisine.lower() in processed_input:
            restaurant_names = get_restaurant_recommendations(cuisine)
            if restaurant_names:
                return f"Here are some {cuisine} restaurants you might like: {', '.join(restaurant_names)}"
            else:
                return f"Sorry, I couldn't find any restaurants that match your preference. Is there anything else I can help you with?"           
            
    if 'rating' in processed_input:
        for word in processed_input:
            try:
                rating = float(word)
                if 0 <= rating <= 5:
                    restaurant_names = get_restaurants_by_rating(rating)
                    if restaurant_names:
                        return f"Here are some restaurants with a rating of {rating} or higher: {', '.join(restaurant_names)}"
                    else:
                        return f"Sorry, I couldn't find any restaurants with a rating of {rating} or higher. Is there anything else I can help you with?"
            except ValueError:
                continue
    
    if 'price' in processed_input or '$' in processed_input:
        for word in processed_input:
            try:
                price = float(word)
                print(f"price: {price}")
                if 0 <= price:
                    restaurant_names = get_restaurants_by_price(price)
                    if restaurant_names:
                        return f"Here are some restaurants that fit your price range: {', '.join(restaurant_names)}"
                    else:
                        return f"Sorry, I couldn't find any restaurants with your price range. Is there anything else I can help you with?"
            except ValueError:
                continue
        
    if 'reviews' in processed_input or 'review' in processed_input:
        for word in processed_input:
            try:
                min_reviews = int(word)
                if min_reviews >= 0:
                    restaurant_names = get_restaurants_by_reviews(min_reviews)
                    if restaurant_names:
                        return f"Here are some restaurants with {min_reviews} or more reviews: {', '.join(restaurant_names)}"
                    else:
                        return f"Sorry, I couldn't find any restaurants with {min_reviews} or more reviews. Is there anything else I can help you with?"
            except ValueError:
                continue
    
    for day in days_of_week:
        if day in processed_input or 'tuesday' in processed_input or 'wednesday' in processed_input or 'thursday' in processed_input or 'friday' in processed_input or 'saturday' in processed_input or 'sunday' in processed_input:
            print("In Loop")
            if 'tuesday' in processed_input:
                day = 'tues'
            elif 'wednesday' in processed_input:
                day = 'wed'
            elif 'thursday' in processed_input:
                day = 'thurs'
            elif 'friday' in processed_input:
                day = 'fri'
            elif 'saturday' in processed_input:
                day = 'sat'
            elif 'sunday' in processed_input:
                day = 'sun'
            time_phrase = extract_time_phrase(user_input)
            if time_phrase:
                time = parse_time(time_phrase)
                if time:
                    print(f"Time: {time}")
                    time_24_hour = time.strftime("%H:%M") 
                    print(f"24 hour: {time_24_hour}") 
                    time_12_hour = time.strftime("%I:%M %p")
                    print(f"12 hour: {time_12_hour}") 
                    restaurant_names = get_restaurants_by_hours(day, time_24_hour)
                    if day == 'tues':
                        day = 'tuesday'
                    elif day == 'wed':
                        day = 'wednesday'
                    elif day == 'thurs':
                        day = 'thursday'
                    elif day == 'fri':
                        day = 'friday'
                    elif day == 'sat':
                        day = 'saturday'
                    elif day == 'sun':
                        day = 'sunday'
                    if restaurant_names:
                        return f"Here are some restaurants open on {day.capitalize()} at {time_12_hour}: {', '.join(restaurant_names)}"
                    else:
                        return f"Sorry, I couldn't find any restaurants open on {day.capitalize()} at {time_12_hour}. Is there anything else I can help you with?"
        elif 'current time' in user_input.lower() or 'now' in user_input.lower() or 'currently' in user_input.lower() or 'right now' in user_input.lower() or 'rn' in user_input.lower() or 'right this minute' in user_input.lower() or 'right this second' in user_input.lower():
            time_12_hour, time_24_hour = get_current_time()
            current_day = datetime.now().strftime("%A").lower()
            print(f"current_day: {current_day}")
            if current_day == 'tuesday':
                current_day = 'tues'
            elif current_day == 'wednesday':
                current_day = 'wed'
            elif current_day == 'thursday':
                current_day = 'thurs'
            elif current_day == 'friday':
                current_day = 'fri'
            elif current_day == 'saturday':
                current_day = 'sat'
            elif current_day == 'sunday':
                current_day = 'sun'
            restaurant_names = get_restaurants_by_hours(current_day, time_24_hour)
            if restaurant_names:
                return f"Here are some restaurants open today at {time_12_hour}: {', '.join(restaurant_names)}"
            else:
                return f"Sorry, I couldn't find any restaurants open today at {time_12_hour}."
            
        offset_value, offset_unit = extract_offset_phrase(user_input)
        if offset_value and offset_unit:
            future_time = calculate_future_time(offset_value, offset_unit)
            future_day = future_time.strftime("%A").lower()
            if future_day == 'tuesday':
                future_day = 'tues'
            elif future_day == 'wednesday':
                future_day = 'wed'
            elif future_day == 'thursday':
                future_day = 'thurs'
            elif future_day == 'friday':
                future_day = 'fri'
            elif future_day == 'saturday':
                future_day = 'sat'
            elif future_day == 'sunday':
                future_day = 'sun' 
            future_time_24_hour = future_time.strftime("%H:%M")
            future_time_12_hour = future_time.strftime("%I:%M %p")
            restaurant_names = get_restaurants_by_hours(future_day, future_time_24_hour)
            if future_day == 'tues':
                future_day = 'tuesday'
            elif future_day == 'wed':
                future_day = 'wednesday'
            elif future_day == 'thurs':
                future_day = 'thursday'
            elif future_day == 'fri':
                future_day = 'friday'
            elif future_day == 'sat':
                future_day = 'saturday'
            elif future_day == 'sun':
                future_day = 'sunday'
            if restaurant_names:
                return f"Here are some restaurants open on {future_day.capitalize()} at {future_time_12_hour}: {', '.join(restaurant_names)}"
            else:
                return f"Sorry, I couldn't find any restaurants open on {future_day.capitalize()} at {future_time_12_hour}."

    return "I'm not sure what you would like. Can you be more specific?"

# Example usage
if __name__ == "__main__":
    menus = get_restaurants_menus()
    freq_dist = train_menu_model(menus)
    user_input = input("Ask me for a food recommendation: ")
    response = generate_response(user_input, freq_dist)
    print(response)