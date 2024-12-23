import mysql.connector
from dotenv import load_dotenv
import os
import re
from fuzzywuzzy import process  # Adding fuzzy matching
from transformers import pipeline  # Hugging Face transformer model

# Load environment variables from .env file
load_dotenv("C:/Users/User/AddmathsAI/AddmathsESKey.env")

# Connect to MySQL database
def connect_to_db():
    return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # No password
            database="addmaths_es"
    )

# Fetch data from the database
def fetch_from_db(query, params=None):
    db = connect_to_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(query, params or ())
    results = cursor.fetchall()
    cursor.close()
    db.close()
    return results

# Get all topic names for fuzzy matching
def get_all_topics():
    query = "SELECT TopicName FROM topic"
    return fetch_from_db(query)

# Get topic details
def get_topic_details(topic_name):
    query = "SELECT * FROM topic WHERE TopicName = %s"
    topics = fetch_from_db(query, (topic_name,))
    return topics[0] if topics else None

# Get formulas for a topic
def get_formulas_for_topic(topic_id):
    query = "SELECT FormulaContent FROM formulas WHERE TopicID = %s"
    return fetch_from_db(query, (topic_id,))

# Get steps for a question
def get_steps_for_question(question_id):
    query = "SELECT Description FROM steps WHERE QuestionID = %s"
    return fetch_from_db(query, (question_id,))

# Get questions for a topic
def get_questions_for_topic(topic_id):
    query = "SELECT QuestionID, Description FROM questions WHERE TopicID = %s"
    return fetch_from_db(query, (topic_id,))

# Initialize Hugging Face model pipeline (For text generation, e.g., GPT-2)
generator = pipeline("text-generation", model="gpt2")

# Generate AI response (using Hugging Face instead of OpenAI)
def generate_ai_response(prompt):
    response = generator(prompt, max_length=150, num_return_sequences=1)
    return response[0]['generated_text'].strip()

# Normalize the user input (remove extra spaces and convert to lowercase)
def normalize_input(user_input):
    return re.sub(r'\s+', ' ', user_input.strip().lower())

# Fuzzy matching to find the best topic match
def fuzzy_match_topic(user_query, topics):
    best_match = process.extractOne(user_query, [topic['TopicName'].lower() for topic in topics])
    return best_match

# Main expert system logic
def expert_system():
    print("Welcome to the AddMaths Expert System!")
    
    # Fetch all topics from the database for fuzzy matching
    all_topics = get_all_topics()

    while True:
        user_query = input("\nEnter your query (or type 'exit' to quit): ").strip().lower()
        
        if user_query == "exit":
            print("Goodbye!")
            break
        
        # Normalize and process user input
        normalized_query = normalize_input(user_query)

        # Handle the list topics query
        if "list" in normalized_query and "topics" in normalized_query:
            topic_names = [topic['TopicName'] for topic in all_topics]
            print("Available topics:")
            for name in topic_names:
                print(f"- {name}")
            continue

        # Fuzzy match the user query to the closest topic name
        matched_topic = fuzzy_match_topic(normalized_query, all_topics)
        if matched_topic:
            # Fetch detailed info on the matched topic
            topic_details = get_topic_details(matched_topic[0])
            if not topic_details:
                print("Sorry, I couldn't find information about that topic.")
                continue

            topic_id = topic_details['TopicID']
            topic_name = topic_details['TopicName']

            print(f"\nTopic: {topic_name}\n")

            # Retrieve and display formulas
            formulas = get_formulas_for_topic(topic_id)
            if formulas:
                print("Formulas:")
                for formula in formulas:
                    print(f"- {formula['FormulaContent']}")

            # Retrieve and display questions
            questions = get_questions_for_topic(topic_id)
            if questions:
                print("\nSample Questions:")
                for i, question in enumerate(questions, 1):
                    print(f"{i}. {question['Description']}")
                    # Fetch and display steps for each question
                    steps = get_steps_for_question(question['QuestionID'])
                    if steps:
                        print("  Steps:")
                        for step in steps:
                            print(f"  - {step['Description']}")

            # AI-powered explanation using Hugging Face
            explanation_prompt = f"Explain the topic '{topic_name}' in simple terms."
            explanation = generate_ai_response(explanation_prompt)
            print("\nAI Explanation:")
            print(explanation)

        else:
            print("Sorry, I couldn't find information about that topic.")

# Run the expert system
if __name__ == "__main__":
    expert_system()
