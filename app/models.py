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
import json
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

def get_restaurants_by_rating_max():
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT name FROM restaurants ORDER BY rating DESC LIMIT 3")
    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [result[0] for result in results]

def get_restaurants_by_rating_min():
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT name FROM restaurants ORDER BY rating LIMIT 3")
    cur.execute(query)
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

def get_restaurants_by_price_max():
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT name FROM restaurants ORDER BY high_price, low_price DESC LIMIT 3")
    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [result[0] for result in results]

def get_restaurants_by_price_min():
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT name FROM restaurants ORDER BY high_price, low_price LIMIT 3")
    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [result[0] for result in results]

def get_restaurants_by_low_price(price_range):
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT name FROM restaurants WHERE low_price < %s and high_price <= %s ORDER BY rating DESC LIMIT 5")
    cur.execute(query, [price_range, price_range])
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [result[0] for result in results]

def get_restaurants_by_high_price(price_range):
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT name FROM restaurants WHERE low_price >= %s and high_price > %s ORDER BY rating DESC LIMIT 5")
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

def get_restaurants_by_reviews_max():
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT name FROM restaurants ORDER BY num_reviews DESC, rating DESC LIMIT 3")
    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [result[0] for result in results]

def get_restaurants_by_reviews_min():
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT name FROM restaurants ORDER BY num_reviews, rating LIMIT 3")
    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [result[0] for result in results]

def get_restaurants_by_hours(day, time):
    conn = connect_db()
    cur = conn.cursor()
    #query = sql.SQL(f"SELECT name FROM restaurants WHERE start_hour_{day} <= %s AND end_hour_{day} >= %s ORDER BY rating DESC LIMIT 5")
    query = sql.SQL(f"""
        SELECT name 
        FROM restaurants 
        WHERE (
        start_hour_{day} <= end_hour_{day} AND
        start_hour_{day} <= %s AND 
        end_hour_{day} >= %s
        )
        OR (
        start_hour_{day} > end_hour_{day} AND
        (
        start_hour_{day} <= %s OR 
        end_hour_{day} >= %s
        )
        )
        ORDER BY rating DESC 
        LIMIT 5;
    """)
    cur.execute(query, [time, time, time, time])
    results = cur.fetchall()
    for result in results:
        print(f"A: {result[0]}")
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

def get_restaurants_by_day(day):
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL(f"SELECT name FROM restaurants WHERE start_hour_{day} != NULL AND end_hour_{day} != NULL ORDER BY rating DESC LIMIT 5")
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
            time_phrase = time_phrase.replace('am', ':00am').replace('pm', ':00pm').replace('AM', ':00am').replace('PM', ':00pm')
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

def get_restaurants_by_name():
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT name FROM restaurants")
    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [result[0] for result in results]

api_key = 'e7431a414289413c9de8c7ac0e548747'
# api_key = '6cb87a4a0c6a4723b373e210049a58e7'

def search_restaurant_by_name(api_key, restaurant_name):
    url = f'https://api.spoonacular.com/food/menuItems/search'
    all_menu_items = []
    offset = 0
    number = 5  # The maximum number of items to fetch per request (adjust as needed)
    params = {
        'query': restaurant_name,
        'number': number,
        'apiKey': api_key
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    menu_items = data.get('menuItems', [])
    filtered_items = [
            {
                'restaurant': item.get('restaurantChain', 'N/A'),
                'title': item.get('title', 'N/A')
            }
            for item in menu_items
            #if item.get('restaurantChain', '').lower() == restaurant_name.lower()
    ]
    all_menu_items.extend(filtered_items)
    # while True:
    #     params = {
    #         'query': restaurant_name,
    #         'number': number,
    #         'offset': offset,
    #         'apiKey': api_key
    #     }
    #     response = requests.get(url, params=params)
    #     response.raise_for_status()
    #     data = response.json()
    #     menu_items = data.get('menuItems', [])
        
    #     if not menu_items:
    #         break  # No more items to fetch
        
        
    #     filtered_items = [
    #         {
    #             'restaurant': item.get('restaurantChain', 'N/A'),
    #             'title': item.get('title', 'N/A')
    #         }
    #         for item in menu_items
    #         if item.get('restaurantChain', '').lower() == restaurant_name.lower()
    #     ]
    #     all_menu_items.extend(filtered_items)
    #     offset += number  # Move to the next page

    return all_menu_items
    # params = {
    #     'query': restaurant_name,
    #     'number': number,
    #     'apiKey': api_key
    # }
    # response = requests.get(url, params=params)
    # response.raise_for_status()
    # return response.json()
#result = search_restaurant_by_name(api_key, "PF Changs")
#print(result)

def fetch_all_menu_items(api_key):
    restaurant_names = get_restaurants_by_name()
    all_menu_items = []

    for restaurant in restaurant_names:
        menu_items = search_restaurant_by_name(api_key, restaurant)
        all_menu_items.extend(menu_items)

    return all_menu_items

def extract_food_item(user_input):
    # Split user input into words
    words = user_input.lower().split()
    return words

def extract_restaurant_id_by_name(search_results, restaurant_name):
    for item in search_results['menuItems']:
        if restaurant_name.lower() in item['title'].lower():
            return item['id']
    return None


def fetch_menu_items(api_key, restaurant_id):
    url = f'https://api.spoonacular.com/food/menuItems/{restaurant_id}'
    params = {
        'apiKey': api_key
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

# Use your Spoonacular API key
#api_key = 'e7431a414289413c9de8c7ac0e548747'
#api_key = '6cb87a4a0c6a4723b373e210049a58e7'

#display_menu_items(search_results)

# Extract the restaurant ID from the search results
#restaurant_id = extract_restaurant_id_by_name(search_results, restaurant_name)


# Search for restaurants based on a query


# Extract restaurant IDs from the search results





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

# menu_url = 'http://www.tacobell.com/food'
# html_content = fetch_menu_html(menu_url)
# if html_content:
#     preprocessed_menu = process_menu(html_content)
#     print(preprocessed_menu)

# def build_menu_database():
#     restaurants = get_restaurants_menus()
#     menu_database = {}
#     for name in restaurants:
#         menu_items = process_menu(html_content)
#         menu_database[name] = menu_items
#     return menu_database

# menu_database = build_menu_database()


def search_menu(item, menu_database):
    results = []
    for restaurant, menu in menu_database.items():
        for menu_item in menu:
            if item.lower() in menu_item.lower():
                results.append((restaurant, menu_item))
    return results

def preprocess_text(text):
    stop_words = set(stopwords.words('english'))
    # Remove 'under' and 'over' from the stop words list and other words
    custom_stop_words = stop_words - {'under', 'over', 'below', 'above', 'than', 'more', 'less', 'a lot', 'not'}

    word_tokens = word_tokenize(text)
    filtered_text = [w.lower() for w in word_tokens if not w.lower() in custom_stop_words]
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

number_words = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11,
    'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
    'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60,
    'seventy': 70, 'eighty': 80, 'ninety': 90, 'hundred': 100,
    'thousand': 1000
}

def word_to_num(word):
    return number_words.get(word.lower(), None)

def parse_days_input(words):
    total = 0
    current = 0
    for word in words:
        num = word_to_num(word)
        if num is not None:
            if num == 100:
                current *= num
            elif num == 1000:
                total += current * num
                current = 0
            else:
                current += num
        else:
            total += current
            current = 0
    total += current
    return total

def extract_days_from_input(input_text):
    words = input_text.split()
    days = parse_days_input(words)
    return days if days > 0 else None

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
            
    if 'rating' in processed_input or '' or 'ratings' in processed_input or 'how good' in user_input.lower() or 'stars' in processed_input  or 'star' in processed_input or 'rate' in processed_input or 'good' in processed_input or 'great' in processed_input or 'awesome' in processed_input or 'amazing' in processed_input or 'delicious' in processed_input or 'spectacular' in processed_input or 'satisfying' in processed_input or 'up to par' in user_input.lower() or 'bad' in processed_input or 'horrible' in processed_input or 'not up to par' in user_input.lower() or 'not good' in user_input.lower() or 'disgusting' in processed_input or 'dissatisfying' in processed_input  or 'best' in processed_input or 'worst' in processed_input:
        if 'how good' in user_input.lower() or 'good' in processed_input or 'great' in processed_input or 'awesome' in processed_input or 'amazing' in processed_input or 'delicious' in processed_input or 'spectacular' in processed_input or 'satisfying' in processed_input or 'up to par' in user_input.lower() or 'best' in processed_input or 'highest' in processed_input or 'high' in processed_input:
            for word in processed_input:
                try:
                    # rating = float(word)
                    # if 0 <= rating <= 5:
                    restaurant_names = get_restaurants_by_rating_max()
                    if restaurant_names:
                        return f"Here are some restaurants with the highest ratings: {', '.join(restaurant_names)}"
                    else:
                        return f"Sorry, I couldn't find any restaurants with your specified rating. Is there anything else I can help you with?"
                except ValueError:
                    continue
        elif 'bad' in processed_input or 'horrible' in processed_input or 'not up to par' in user_input.lower() or 'not good' in user_input.lower() or 'disgusting' in processed_input or 'dissatisfying' in processed_input or 'worst' in processed_input or 'low' in processed_input or 'lowest' in processed_input:
            for word in processed_input:
                try:
                    # rating = float(word)
                    # if 0 <= rating <= 5:
                    restaurant_names = get_restaurants_by_rating_min()
                    if restaurant_names:
                        return f"Here are some restaurants with the lowest ratings: {', '.join(restaurant_names)}"
                    else:
                        return f"Sorry, I couldn't find any restaurants with your specified rating. Is there anything else I can help you with?"
                except ValueError:
                    continue
        else:
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
    
    if 'price' in processed_input or '$' in processed_input or 'dollars' in processed_input or 'dollar' in processed_input or 'pricing' in processed_input or 'range' in processed_input or 'under' in processed_input or 'below' in processed_input or 'cost' in processed_input or 'costing' in processed_input or 'amount' in processed_input or 'over' in processed_input or 'above' in processed_input or 'cheap' in processed_input or 'cheaper than' in processed_input or 'more expensive than' in processed_input or 'expensive' in processed_input or 'affordable' in processed_input or 'high price' in processed_input or 'low price' in processed_input or 'cheapest' in processed_input or 'most expensive' in processed_input or 'lower prices' in processed_input or 'higher prices' in processed_input or 'lowest prices' in processed_input or 'highest prices' in processed_input or 'lower' in processed_input or 'more affordable than' in processed_input  or 'higher' in processed_input:
        print(processed_input)
        if 'under' in processed_input or 'below' in processed_input or 'cheaper' in processed_input or 'lower' in processed_input :
            for word in processed_input:
                try:
                    price = float(word)
                    print(f"price: {price}")
                    if 0 <= price:
                        restaurant_names = get_restaurants_by_low_price(price)
                        if restaurant_names:
                            return f"Here are some restaurants that fit your price range: {', '.join(restaurant_names)}"
                        else:
                            return f"Sorry, I couldn't find any restaurants with your price range. Is there anything else I can help you with?"
                except ValueError:
                    continue
        elif 'over' in processed_input or 'above' in processed_input or 'higher' in processed_input:
            for word in processed_input:
                try:
                    price = float(word)
                    print(f"price: {price}")
                    if 0 <= price:
                        restaurant_names = get_restaurants_by_high_price(price)
                        if restaurant_names:
                            return f"Here are some restaurants that fit your price range: {', '.join(restaurant_names)}"
                        else:
                            return f"Sorry, I couldn't find any restaurants with your price range. Is there anything else I can help you with?"
                except ValueError:
                    continue
        elif 'cheap' in processed_input or 'affordable' in processed_input or 'low price' in processed_input or 'cheapest' in processed_input or 'lowest prices' in processed_input or 'lower prices' in processed_input:
            for word in processed_input:
                try:
                    # price = float(word)
                    # print(f"price: {price}")
                    restaurant_names = get_restaurants_by_price_min()
                    if restaurant_names:
                        return f"Here are some restaurants that fit your price range: {', '.join(restaurant_names)}"
                    else:
                        return f"Sorry, I couldn't find any restaurants with your price range. Is there anything else I can help you with?"
                except ValueError:
                    continue
        elif 'expensive' in processed_input or 'high price' in processed_input or 'most expensive' in processed_input or 'highest prices' in processed_input or 'higher prices' in processed_input:
            for word in processed_input:
                try:
                    # price = float(word)
                    # print(f"price: {price}")
                    # if 0 <= price:
                    restaurant_names = get_restaurants_by_price_max()
                    if restaurant_names:
                        return f"Here are some restaurants that fit your price range: {', '.join(restaurant_names)}"
                    else:
                        return f"Sorry, I couldn't find any restaurants with your price range. Is there anything else I can help you with?"
                except ValueError:
                    continue
        else:
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
        
    if 'reviews' in processed_input or 'review' in processed_input or 'a lot' in user_input.lower() or 'many' in processed_input or 'much' in processed_input or 'tons' in processed_input or 'few' in processed_input or 'least' in processed_input or 'not a lot' in user_input.lower() or 'most' in processed_input:
        if 'a lot' in user_input.lower() or 'many' in processed_input or 'much' in processed_input or 'tons' in processed_input or 'most' in processed_input:
            for word in processed_input:
                try:
                    # min_reviews = int(word)
                    # if min_reviews >= 0:
                    restaurant_names = get_restaurants_by_reviews_max()
                    if restaurant_names:
                        return f"Here are some restaurants with the most reviews: {', '.join(restaurant_names)}"
                    else:
                        return f"Sorry, I couldn't find any restaurants with the specified number of reviews. Is there anything else I can help you with?"
                except ValueError:
                    continue
        elif 'few' in processed_input or 'least' in processed_input or 'not a lot' in user_input.lower():
            for word in processed_input:
                try:
                    # min_reviews = int(word)
                    # if min_reviews >= 0:
                    restaurant_names = get_restaurants_by_reviews_min()
                    if restaurant_names:
                        return f"Here are some restaurants with the least reviews: {', '.join(restaurant_names)}"
                    else:
                        return f"Sorry, I couldn't find any restaurants with the specified number of reviews. Is there anything else I can help you with?"
                except ValueError:
                    continue
        else:
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
        if day in processed_input or 'mon' in processed_input or 'tuesday' in processed_input or 'tue' in processed_input or 'tues' in processed_input or 'wednesday' in processed_input or 'wednes' in processed_input or 'wed' in processed_input or 'thursday' in processed_input or 'thur' in processed_input or 'thu' in processed_input or 'thurs' in processed_input or 'friday' in processed_input or 'fri' in processed_input or 'saturday' in processed_input or 'sat' in processed_input or 'sun' in processed_input or 'sunday' in processed_input:
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
                                
        elif any(phrase in user_input.lower() for phrase in ['current time', 'now', 'currently', 'right now', 'rn', 'right this minute', 'right this second', 'current', 'this moment', 'today']):
            yes = False
            if 'today' in user_input.lower():
                yes = True
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
                if yes == False:
                    return f"Here are some restaurants open today at {time_12_hour}: {', '.join(restaurant_names)}"
                else:
                    return f"Here are some restaurants open today: {', '.join(restaurant_names)}" 
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

        elif any(phrase in user_input.lower() for phrase in ['yesterday', 'days ago', 'day ago']):
            now = datetime.now()
            time = datetime.now().strftime("%H:%M")
            if 'yesterday' in user_input.lower():
                day = (now + timedelta(days=6)).strftime("%A").lower()
                if day == 'tuesday':
                    day = 'tues'
                elif day == 'wednesday':
                    day = 'wed'
                elif day == 'thursday':
                    day = 'thurs'
                elif day == 'friday':
                    day = 'fri'
                elif day == 'saturday':
                    day = 'sat'
                elif day == 'sunday':
                    day = 'sun' 
                restaurant_names = get_restaurants_by_hours(day, time)
                if restaurant_names:
                    return f"Here are some restaurants open yesterday: {', '.join(restaurant_names)}"
                else:
                    return f"Sorry, I couldn't find any restaurants open yesterday. Is there anything else I can help you with?" 
            else: 
                days = extract_days_from_input(user_input.lower())
                num = 7 * (int(days) // 7 + 1) - int(days) 
                if days is not None:
                    day = (now + timedelta(days=num)).strftime("%A").lower()
                    print(f"Day: {day}")
                    if day == 'tuesday':
                        day = 'tues'
                    elif day == 'wednesday':
                        day = 'wed'
                    elif day == 'thursday':
                        day = 'thurs'
                    elif day == 'friday':
                        day = 'fri'
                    elif day == 'saturday':
                        day = 'sat'
                    elif day == 'sunday':
                        day = 'sun'
                    restaurant_names = get_restaurants_by_hours(day, time)
                    if restaurant_names:
                        if days == 1:
                            return f"Here are some restaurants open {days} day ago: {', '.join(restaurant_names)}"
                        else:
                            return f"Here are some restaurants open {days} days ago: {', '.join(restaurant_names)}" 
                    else:
                        if days == 1:
                            return f"Sorry, I couldn't find any restaurants open {days} day ago. Is there anything else I can help you with?"  
                        else:
                            return f"Sorry, I couldn't find any restaurants open {days} days ago. Is there anything else I can help you with?" 
                else:
                    for word in processed_input:
                        try:
                            days = 7 * (int(word) // 7 + 1) - int(word)
                            if days >= 0:
                                day = (now + timedelta(days=days)).strftime("%A").lower()
                                print(f"Day: {day}")
                                if day == 'tuesday':
                                    day = 'tues'
                                elif day == 'wednesday':
                                    day = 'wed'
                                elif day == 'thursday':
                                    day = 'thurs'
                                elif day == 'friday':
                                    day = 'fri'
                                elif day == 'saturday':
                                    day = 'sat'
                                elif day == 'sunday':
                                    day = 'sun' 
                                restaurant_names = get_restaurants_by_hours(day, time)
                                if restaurant_names:
                                    if int(word) == 1:
                                        return f"Here are some restaurants open {int(word)} day ago: {', '.join(restaurant_names)}" 
                                    else:
                                        return f"Here are some restaurants open {int(word)} days ago: {', '.join(restaurant_names)}"
                                else:
                                    if int(word) == 1:
                                        return f"Sorry, I couldn't find any restaurants open {int(word)} day ago. Is there anything else I can help you with?"
                                    else: 
                                        return f"Sorry, I couldn't find any restaurants open {int(word)} days ago. Is there anything else I can help you with?"
                        except ValueError:
                            continue

        elif any(phrase in user_input.lower() for phrase in ['tomorrow', 'tmr', 'days', 'day']):
            now = datetime.now()
            time = datetime.now().strftime("%H:%M")
            if 'tomorrow' in user_input.lower() or 'tmr' in user_input.lower():
                day = (now + timedelta(days=1)).strftime("%A").lower()
                if day == 'tuesday':
                        day = 'tues'
                elif day == 'wednesday':
                    day = 'wed'
                elif day == 'thursday':
                    day = 'thurs'
                elif day == 'friday':
                    day = 'fri'
                elif day == 'saturday':
                    day = 'sat'
                elif day == 'sunday':
                    day = 'sun' 
                restaurant_names = get_restaurants_by_hours(day, time)
                if restaurant_names:
                    return f"Here are some restaurants open tomorrow: {', '.join(restaurant_names)}"
                else:
                    return f"Sorry, I couldn't find any restaurants open tomorrow. Is there anything else I can help you with?" 
            else:
                days = extract_days_from_input(user_input.lower())
                if days is not None: 
                    day = (now + timedelta(days=days)).strftime("%A").lower()
                    print(f"Day: {day}")
                    if day == 'tuesday':
                        day = 'tues'
                    elif day == 'wednesday':
                        day = 'wed'
                    elif day == 'thursday':
                        day = 'thurs'
                    elif day == 'friday':
                        day = 'fri'
                    elif day == 'saturday':
                        day = 'sat'
                    elif day == 'sunday':
                        day = 'sun' 
                    restaurant_names = get_restaurants_by_hours(day, time)
                    if restaurant_names:
                        if days == 1:
                            return f"Here are some restaurants open in {days} day: {', '.join(restaurant_names)}"
                        else:
                            return f"Here are some restaurants open in {days} days: {', '.join(restaurant_names)}"
                    else:
                        if days == 1:
                            return f"Sorry, I couldn't find any restaurants open in {days} day. Is there anything else I can help you with?"
                        else:
                            return f"Sorry, I couldn't find any restaurants open in {days} days. Is there anything else I can help you with?"
                else:
                    for word in processed_input:
                        try:
                            days = int(word)
                            if days >= 0:
                                day = (now + timedelta(days=days)).strftime("%A").lower()
                                print(f"Day: {day}")
                                if day == 'tuesday':
                                    day = 'tues'
                                elif day == 'wednesday':
                                    day = 'wed'
                                elif day == 'thursday':
                                    day = 'thurs'
                                elif day == 'friday':
                                    day = 'fri'
                                elif day == 'saturday':
                                    day = 'sat'
                                elif day == 'sunday':
                                    day = 'sun' 
                                restaurant_names = get_restaurants_by_hours(day, time)
                                if restaurant_names:
                                    if days == 1:
                                        return f"Here are some restaurants open in {days} day: {', '.join(restaurant_names)}"
                                    else:
                                        return f"Here are some restaurants open in {days} days: {', '.join(restaurant_names)}"
                                else:
                                    if days == 1:
                                        return f"Sorry, I couldn't find any restaurants open in {days} day. Is there anything else I can help you with?"
                                    else:
                                        return f"Sorry, I couldn't find any restaurants open in {days} days. Is there anything else I can help you with?"
                        except ValueError:
                            continue 
            
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
            
        time_phrase = extract_time_phrase(user_input)
        if time_phrase:
            time = parse_time(time_phrase)
            if time:
                print(f"Time: {time}")
                time_24_hour = time.strftime("%H:%M") 
                print(f"24 hour: {time_24_hour}") 
                time_12_hour = time.strftime("%I:%M %p")
                print(f"12 hour: {time_12_hour}")
                day = datetime.now().strftime("%A").lower() 
                now = datetime.now()
                print(f"Now: {now.time()}")
                print(f"klefls: {time.time()}")
                if now.time().replace(second=0, microsecond=0) > time.time():
                    day = (now + timedelta(days=1)).strftime("%A").lower()
                    if day == 'tuesday':
                        day = 'tues'
                    elif day == 'wednesday':
                        day = 'wed'
                    elif day == 'thursday':
                        day = 'thurs'
                    elif day == 'friday':
                        day = 'fri'
                    elif day == 'saturday':
                        day = 'sat'
                    elif day == 'sunday':
                        day = 'sun'
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
                        return f"Here are some restaurants open at {time_12_hour} tomorrow on {day.capitalize()}: {', '.join(restaurant_names)}"
                    else:
                        return f"Sorry, I couldn't find any restaurants open at {time_12_hour} tomorrow on {day.capitalize()}. Please be more specific."
                if day == 'tuesday':
                    day = 'tues'
                elif day == 'wednesday':
                    day = 'wed'
                elif day == 'thursday':
                    day = 'thurs'
                elif day == 'friday':
                    day = 'fri'
                elif day == 'saturday':
                    day = 'sat'
                elif day == 'sunday':
                    day = 'sun'

                restaurant_names = get_restaurants_by_hours(day, time_24_hour)
                if restaurant_names:
                    return f"Here are some restaurants open at {time_12_hour} today: {', '.join(restaurant_names)}"
            else:
                return f"Sorry, I couldn't find any restaurants open at {time_12_hour}. Please be more specific."

    food_words = extract_food_item(user_input)

    import string

    # Restricted ingredients associated with dietary restrictions
    restricted_ingredients = {
        "vegetarian": ["chicken", "beef", "pork", "fish", "seafood", "shrimp", "sausage", "wing", "burger"],
        "vegan": ["chicken", "beef", "pork", "fish", "seafood", "shrimp", "dairy", "milk", "cheese", "butter", "egg", "honey", "sausage", "wing", "burger", "cheesecake"],
        "pescatarian": ["chicken", "beef", "pork", "sausage", "wing", "Cheeseburger"],
        "lactose-intolerant": ["dairy", "milk", "cheese", "butter", "queso", "cheesecake"],
        "lactose intolerant": ["dairy", "milk", "cheese", "butter", "queso", "cheesecake"],
        "omnivore": [],  # Omnivores can eat anything
        "keto": ["bread", "pasta", "rice", "potato", "sugar"],
        "paleo": ["bread", "pasta", "rice", "legume", "dairy", "sugar"],
        "nut-free": ["peanut", "almond", "cashew", "walnut", "pecan", "nut"],
        "nut free": ["peanut", "almond", "cashew", "walnut", "pecan", "nut"],
        "halal": ["pork", "bacon", "ham", "pepperoni"],
        "kosher": ["pork", "shellfish"],
        "low-carb": ["bread", "pasta", "rice", "potato"],
        "low carb": ["bread", "pasta", "rice", "potato"],
        "low-fat": ["butter", "oil", "fatty", "fried"],
        "low fat": ["butter", "oil", "fatty", "fried"],
        "gluten-free": ["bread", "pasta", "wheat", "barley", "rye"],
        "gluten free": ["bread", "pasta", "wheat", "barley", "rye"],
        "organic": [],  # Assume organic is not restricted by ingredients but by quality
        "FODMAP": ["garlic", "onion", "wheat", "legume", "dairy", "milk", "cheese", "butter", "apple", "honey"],
        "fodmap": ["garlic", "onion", "wheat", "legume", "dairy", "milk", "cheese", "butter", "apple", "honey"],
        "Fodmap": ["garlic", "onion", "wheat", "legume", "dairy", "milk", "cheese", "butter", "apple", "honey"]
    }

    def normalize_word(word):
        # Remove trailing punctuation and convert to lowercase
        word = word.rstrip(string.punctuation).lower()
        # Remove trailing "s" to handle plural forms
        if word.endswith("s"):
            word = word[:-1]
        # Normalize specific words to a common form
        if word in ["hamburger", "cheeseburger"]:
            return "burger"
        return word

    def normalize_menu_item_title(title):
        words = title.lower().split()
        normalized_words = []
        for word in words:
            # Normalize words containing "burger"
            if "burger" in word:
                normalized_words.append("burger")
            else:
                normalized_words.append(normalize_word(word))
        return normalized_words

    def matches_dietary_restrictions(item_title, dietary_restrictions):
        item_title_words = normalize_menu_item_title(item_title)
        for restriction in dietary_restrictions:
            for ingredient in restricted_ingredients.get(restriction, []):
                if ingredient in item_title_words:
                    print(f"Item '{item_title}' contains restricted ingredient '{ingredient}' for restriction '{restriction}'")
                    return False
        return True

    if food_words:
        dietary_restrictions = ["vegetarian", "vegan", "pescatarian",
                                "lactose-intolerant", "lactose intolerant",
                                "omnivore", "keto", "paleo", "nut-free",
                                "nut free", "halal", "kosher", "low-carb",
                                "low carb", "low-fat", "low fat", "gluten-free",
                                "gluten free", "organic", "FODMAP", "fodmap", "Fodmap"]  # Example list of dietary restrictions
        all_menu_items = fetch_all_menu_items(api_key)
        matched_items = []
        dietary_items = []
        restricted_items = []

        # Normalize food_words
        normalized_food_words = [normalize_word(word.lower()) for word in food_words]
        print(f"Normalized food words: {normalized_food_words}")

        for item in all_menu_items:
            print(f"Item: {item}")
            # Normalize the title of each menu item
            normalized_title_words = normalize_menu_item_title(item['title'])
            print(f"Normalized title words: {normalized_title_words}")
            # Check if item matches food words
            word_match = any(word in normalized_title_words for word in normalized_food_words)
            # Check if item matches dietary restrictions
            dietary_match = matches_dietary_restrictions(item['title'], dietary_restrictions)
            
            if word_match and dietary_match:
                # Check if word_match corresponds to restricted ingredients
                if any(word in restricted_ingredients.get(dietary_restrictions[0], []) for word in normalized_title_words):
                    restricted_items.append(item)
                else:
                    matched_items.append(item)
            elif word_match:
                matched_items.append(item)
            elif dietary_match:
                dietary_items.append(item)

        if restricted_items:
            print(restricted_items)
            response = "Here are some items that match your dietary preferences:\n"
            for item in restricted_items:
                response += f"{item['title']} at {item['restaurant']},\n"
            response = response.rstrip(',\n')  # Remove trailing comma and newline
        elif matched_items:
            print(matched_items)
            response = "Here are some options you might like:\n"
            for item in matched_items:
                response += f"{item['title']} at {item['restaurant']},\n"
            response = response.rstrip(',\n')  # Remove trailing comma and newline
        elif dietary_items:
            print(dietary_items)
            response = "Here are some options that match your dietary restrictions:\n"
            for item in dietary_items:
                response += f"{item['title']} at {item['restaurant']},\n"
            response = response.rstrip(',\n')  # Remove trailing comma and newline
        else:
            response = "Sorry, I couldn't find any menu items matching your request. Is there anything else I can help you with?"

        print(response)
        return response
    
    return("Sorry, I don't think I understand your request. Can you try again?")

# Example usage
if __name__ == "__main__":
    menus = get_restaurants_menus()
    freq_dist = train_menu_model(menus)
    user_input = input("Ask me for a food recommendation: ")
    response = generate_response(user_input, freq_dist)
    print(response)