import random
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download('punkt')
nltk.download('stopwords')

food_recommendations = {
    'vegetarian': ['Vegetable Stir Fry', 'Veggie Burger', 'Pasta Primavera'],
    'vegan': ['Vegan Tacos', 'Vegan Buddha Bowl', 'Vegan Burger'],
    'gluten-free': ['Grilled Chicken Salad', 'Gluten-Free Pizza', 'Quinoa Salad'],
    'keto': ['Keto Salad', 'Keto Burger', 'Grilled Chicken'],
    # Add more categories and food items as needed
}

# Preprocess input text
def preprocess_text(text):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    filtered_text = [w.lower() for w in word_tokens if not w in stop_words]
    return filtered_text

# Generate a response based on user input
def generate_response(user_input):
    processed_input = preprocess_text(user_input)
    for category in food_recommendations:
        if category in processed_input:
            return random.choice(food_recommendations[category])
    return "I'm not sure what you would like. Can you specify a dietary preference?"

# Example usage
if __name__ == "__main__":
    user_input = input("Ask me for a food recommendation: ")
    response = generate_response(user_input)
    print(response)