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
import requests
from bs4 import BeautifulSoup

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

def get_restaurants_by_morning(day):
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL(f"SELECT name FROM restaurants WHERE start_hour_{day} <= 11:59:59 AND end_hour_{day} >= %s ORDER BY rating DESC LIMIT 5")
    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [result[0] for result in results]

def parse_time(time_phrase):
    """
    Try to parse the time in 12-hour format with AM/PM.
    Return the time object.
    """
    try:
        time_phrase = time_phrase.replace('.', '').replace(' ', '')
        if ':' not in time_phrase and ('am' in time_phrase.lower() or 'pm' in time_phrase.lower()):
            time_phrase = time_phrase.replace('am', ':00am').replace('pm', ':00pm')
        if ':' not in time_phrase:
            time_phrase += ':00'
        return datetime.strptime(time_phrase, '%I:%M%p')
    except ValueError:
        return None

def extract_time_phrase(input_text):
    """
    Extract the time phrase from the user input.
    """
    time_patterns = [
        r'\b\d{1,2}(:\d{2})?\s*(am|pm|a\.m\.|p\.m\.|AM|PM|A\.M\.|P\.M\.)?\b',
        r'\b\d{1,2}(:\d{2})(am|pm|a\.m\.|p\.m\.|AM|PM|A\.M\.|P\.M\.)?\b',
        r'\b\d{1,2}(am|pm|a\.m\.|p\.m\.|AM|PM|A\.M\.|P\.M\.)\b',
        r'\b\d{1,2}?\s*(am|pm|a\.m\.|p\.m\.|AM|PM|A\.M\.|P\.M\.)\b', 
    ]
    for pattern in time_patterns:
        match = re.search(pattern, input_text)
        if match:
            return match.group()
    return None

def extract_offset_phrase(input_text):
    match = re.search(r'\b(\d+)\s?(minutes?|hours?|days?|min?|hr?|hrs?|day?|minute?|hour?)\s?\b', input_text, re.IGNORECASE)
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
    query = sql.SQL("SELECT name, menu FROM restaurants")
    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def fetch_menu_html(menu_link):
    if not menu_link.startswith("http://") and not menu_link.startswith("https://"):
        print(f"Invalid URL: {menu_link}")
        return []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(menu_link, headers=headers)
        response.raise_for_status()
        if response.status_code == 200:
            return response.content
        else:
            print(f"Failed to fetch menu from {menu_link}: {response.status_code} {response.reason}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch menu from {menu_link}: {e}")
        return None

def process_menu(html_content):
    if not html_content:
        return None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract all text content from the HTML
    text_content = soup.get_text()
    
    # Example: Filter menu-related information
    keywords = ['menu', 'item', 'price', 'description']
    filtered_text = filter_menu_content(text_content, keywords)
    
    return filtered_text

def filter_menu_content(text, keywords):
    # Example: Simple keyword matching
    lines = text.split('\n')
    menu_lines = []
    
    for line in lines:
        if any(keyword in line.lower() for keyword in keywords):
            menu_lines.append(line.strip())
    
    return '\n'.join(menu_lines)

def print_menu_html_for_restaurant(restaurant_name, menu_link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(menu_link, headers=headers)
        response.raise_for_status()
        print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch menu from {menu_link}: {e}")

menu_url = 'http://www.tacobell.com/food'
html_content = fetch_menu_html(menu_url)
if html_content:
    preprocessed_menu = process_menu(html_content)
    print(preprocessed_menu)

def build_menu_database():
    restaurants = get_restaurants_menus()
    menu_database = {}
    for name in restaurants:
        menu_items = process_menu(html_content)
        menu_database[name] = menu_items
    return menu_database

menu_database = build_menu_database()


def search_menu(item, menu_database):
    results = []
    for restaurant, menu in menu_database.items():
        for menu_item in menu:
            if item.lower() in menu_item.lower():
                results.append((restaurant, menu_item))
    return results

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

def get_time_range(period):
    time_ranges = {
        "morning": ("06:00", "12:00"),
        "afternoon": ("12:00", "17:00"),
        "evening": ("17:00", "21:00"),
        "night": ("21:00", "06:00")
    }
    return time_ranges.get(period.lower(), None)

# Generate a response based on user input
def generate_response(user_input):
    processed_input = preprocess_text(user_input)
    if greeting(processed_input) != None:
        return greeting(processed_input)
    
    cuisine_types = ["Italian", "Mexican", "Japanese", "Indian", "Thai", "Chinese", "French", "Mediterranean", "Middle Eastern", "American", "Korean", "Vietnamese", "Burmese", "German", "Other"]
    days_of_week = ["monday", "tues", "wed", "thurs", "fri", "sat", "sun"]
    periods = ["morning", "afternoon", "evening", "night"]
    
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
        if day in processed_input or 'mon' in processed_input or 'tuesday' in processed_input or 'tue' in processed_input or 'wednesday' in processed_input or 'wednes' in processed_input or 'thursday' in processed_input or 'thur' in processed_input or 'thu' in processed_input or 'friday' in processed_input or 'saturday' in processed_input or 'sunday' in processed_input:
            print("In Loop")
            if 'mon' in processed_input:
                day = 'monday'
            elif 'tuesday' or 'tue' in processed_input:
                day = 'tues'
            elif 'wednesday' or 'wednes' in processed_input:
                day = 'wed'
            elif 'thursday' or 'thu' or 'thur' in processed_input:
                day = 'thurs'
            elif 'friday' in processed_input:
                day = 'fri'
            elif 'saturday' in processed_input:
                day = 'sat'
            elif 'sunday' in processed_input:
                day = 'sun'
            time_phrase = extract_time_phrase(user_input)
            print(time_phrase)
            print(user_input.lower())
            if time_phrase:
                print("Time is key to success")
                time = parse_time(time_phrase)
                print(f"time: {time}")
                if time:
                    print(f"Time: {time}")
                    time_24_hour = time.strftime("%H:%M") 
                    print(f"24 hour: {time_24_hour}") 
                    time_12_hour = time.strftime("%I:%M %p")
                    print(f"12 hour: {time_12_hour}") 
                    restaurant_names = get_restaurants_by_hours(day, time_24_hour)
                    if day == 'monday':
                        day = 'monday'
                    elif day == 'tues':
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
            elif 'morning' in user_input.lower() or 'afternoon' in user_input.lower() or 'evening' in user_input.lower() or 'night' in user_input.lower():
                print("Phrase") 
                for period in periods:
                    if period in processed_input:
                        time_range = get_time_range(period)
                        if time_range:
                            start_time, end_time = time_range
                            # Special handling for night time range which spans two days
                            if period == "night":
                                restaurant_names = get_restaurants_by_hours(day, start_time) + get_restaurants_by_hours(day, end_time)
                            else:
                                restaurant_names = get_restaurants_by_hours(day, start_time) + get_restaurants_by_hours(day, end_time)
                            if restaurant_names:
                                return f"Here are some restaurants open in the {period}: {', '.join(set(restaurant_names))}"
                            else:
                                return f"Sorry, I couldn't find any restaurants open in the {period}. Is there anything else I can help you with?"
                                
        elif any(phrase in user_input.lower() for phrase in ['current time', 'now', 'currently', 'right now', 'rn', 'right this minute', 'right this second', 'current', 'this moment']):
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
        elif any(phrase in user_input.lower() for phrase in periods): 
            for period in periods:
                if period in processed_input:
                    time_range = get_time_range(period)
                    if time_range:
                        start_time, end_time = time_range
                        # Special handling for night time range which spans two days
                        if period == "night":
                            restaurant_names = get_restaurants_by_hours(day, start_time) + get_restaurants_by_hours(day, end_time)
                        else:
                            restaurant_names = get_restaurants_by_hours(day, start_time) + get_restaurants_by_hours(day, end_time)
                        if restaurant_names:
                            return f"Here are some restaurants open in the {period}: {', '.join(set(restaurant_names))}"
                        else:
                            return f"Sorry, I couldn't find any restaurants open in the {period}. Is there anything else I can help you with?"

            
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
    
    for word in processed_input:
        search_results = search_menu(word, menu_database)
        if search_results:
            response = "Here are some options you might like:\n"
            for restaurant, menu_item in search_results:
                response += f"{menu_item} at {restaurant}\n"
            return response.strip()

    return "I'm not sure what you would like. Can you be more specific? Make sure everything is spelled properly."

# Example usage
if __name__ == "__main__":
    menus = get_restaurants_menus()
    freq_dist = train_menu_model(menus)
    user_input = input("Ask me for a food recommendation: ")
    response = generate_response(user_input, freq_dist)
    print(response)