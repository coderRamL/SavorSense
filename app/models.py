import random
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
# from nltk.stem import WordNetLemmatizer
import psycopg2
from psycopg2 import sql

nltk.download('punkt')
nltk.download('stopwords')
# nltk.download('wordnet')

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
    return GREETING_RESPONSES
# Preprocess input text
def preprocess_text(text):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    filtered_text = [w.lower() for w in word_tokens if not w in stop_words]
    return filtered_text

# Generate a response based on user input
def generate_response(user_input):
    processed_input = preprocess_text(user_input)
    if greeting(processed_input) != None:
        return greeting(processed_input)
    
    for category in food_recommendations:
        if category in processed_input:
            return random.choice(food_recommendations[category])
    return "I'm not sure what you would like. Can you specify a dietary preference?"

def extract_data():
    # Database URL
    database_url = "postgresql://SavorSense_owner:iX2EMY6TzLlf@ep-shrill-cloud-a40et0x7.us-east-1.aws.neon.tech/SavorSense?sslmode=require"

    # Create a connection to the database
    conn = psycopg2.connect(database_url)

    # Create a cursor object
    cur = conn.cursor()

    # SQL query
    query = sql.SQL("SELECT * FROM {}").format(sql.Identifier('restaurants'))

    # Execute the query
    cur.execute(query)

    # Fetch all the rows
    rows = cur.fetchall()

    for row in rows:
        print(row)

    # Close the cursor and connection
    cur.close()
    conn.close()

# def preprocess_data():
#     rows = [row[0] for row in rows]

#     # Initialize the lemmatizer
#     lemmatizer = WordNetLemmatizer()

#     preprocessed_rows = []

#     for row in rows:
#         row = str(row)
#         # Tokenize the text
#         tokens = word_tokenize(row)

#         # Remove non-alphabetic tokens and convert to lower case
#         words = [token.lower() for token in tokens if token.isalpha()]

#         # Remove stop words
#         stop_words = set(stopwords.words('english'))
#         words = [word for word in words if word not in stop_words]

#         # Lemmatize the words
#         words = [lemmatizer.lemmatize(word) for word in words]

#         preprocessed_rows.append(words)

# Example usage
if __name__ == "__main__":
    user_input = input("Ask me for a food recommendation: ")
    response = generate_response(user_input)
    print(response)