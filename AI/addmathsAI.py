import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
import os
import re
from fuzzywuzzy import process, fuzz
import functools

# Load environment variables once at startup
load_dotenv("C:/Users/User/AddmathsAI/AddmathsESKey.env")

# Global variables
topics_cache = {}
questions_cache = {}

# Create a connection pool
connection_pool = pooling.MySQLConnectionPool(
    pool_name="addmaths_pool",
    pool_size=5,
    host="localhost",
    user="root",
    password="",
    database="addmaths_es"
)

# Use a connection from the pool
def get_connection():
    return connection_pool.get_connection()

# Fetch data from the database with connection pooling
def fetch_from_db(query, params=None):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()
        conn.close()

# Cache results
@functools.lru_cache(maxsize=32)
def get_all_topics():
    query = "SELECT TopicID, TopicName FROM topic"
    return fetch_from_db(query)

@functools.lru_cache(maxsize=32)
def get_topic_details(topic_name):
    query = "SELECT * FROM topic WHERE TopicName = %s"
    topics = fetch_from_db(query, (topic_name,))
    return topics[0] if topics else None

@functools.lru_cache(maxsize=32)
def get_formulas_for_topic(topic_id):
    query = "SELECT FormulaContent FROM formulas WHERE TopicID = %s"
    return fetch_from_db(query, (topic_id,))

@functools.lru_cache(maxsize=64)
def get_steps_for_question(question_id):
    query = "SELECT Description FROM steps WHERE QuestionID = %s"
    return fetch_from_db(query, (question_id,))

@functools.lru_cache(maxsize=32)
def get_questions_for_topic(topic_id):
    query = "SELECT QuestionID, Description FROM questions WHERE TopicID = %s"
    return fetch_from_db(query, (topic_id,))

@functools.lru_cache(maxsize=32)
def get_question_by_id(question_id):
    query = "SELECT QuestionID, Description, TopicID FROM questions WHERE QuestionID = %s"
    questions = fetch_from_db(query, (question_id,))
    return questions[0] if questions else None

# Normalize the user input
def normalize_input(user_input):
    return re.sub(r'\s+', ' ', user_input.strip().lower())

# Preprocess topics for faster matching
def preprocess_topics(topics):
    global topics_cache
    topics_cache = {topic['TopicID']: topic['TopicName'].lower() for topic in topics}

# Optimized fuzzy matching
def fuzzy_match_topic(user_query, topics_dict):
    best_match = None
    highest_score = 0
    
    for topic_id, topic_name in topics_dict.items():
        score = fuzz.token_sort_ratio(user_query, topic_name)
        if score > highest_score and score > 60:  # Set a threshold
            highest_score = score
            best_match = topic_name
    
    return (best_match, highest_score) if best_match else None

# Main expert system logic
def expert_system():
    global questions_cache
    
    print("Welcome to the AddMaths Expert System!")
    print("Commands:")
    print("- 'list topics' - Shows all available topics")
    print("- 'list questions for [topic]' - Lists questions for a specific topic")
    print("- 'show steps for question [ID]' - Shows steps for a specific question")
    print("- '[topic name]' - Displays information about a topic")
    print("- 'exit' - Quits the program")
    
    # Fetch all topics from the database once
    all_topics = get_all_topics()
    preprocess_topics(all_topics)

    while True:
        user_query = input("\nEnter your query: ").strip().lower()
        
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

        # Handle show steps for a specific question
        if ("show" in normalized_query or "get" in normalized_query) and "steps" in normalized_query and "question" in normalized_query:
            # Extract question ID using regex
            question_pattern = r"question\s+(\d+)"
            match = re.search(question_pattern, normalized_query)
            
            if match:
                question_id = int(match.group(1))
                question = get_question_by_id(question_id)
                
                if question:
                    steps = get_steps_for_question(question_id)
                    print(f"\nQuestion {question_id}: {question['Description']}")
                    if steps:
                        print("Steps:")
                        for i, step in enumerate(steps, 1):
                            print(f"{i}. {step['Description']}")
                    else:
                        print("No steps available for this question.")
                else:
                    print(f"Question with ID {question_id} not found.")
                continue
            else:
                print("Please provide a valid question ID (e.g., 'show steps for question 5').")
                continue

        # Handle listing questions for a specific topic
        if "list" in normalized_query and "questions" in normalized_query:
            # Extract topic name from query
            topic_pattern = r"questions\s+(?:for|on|about)\s+(.+)"
            match = re.search(topic_pattern, normalized_query)
            
            if match:
                topic_query = match.group(1).strip()
                matched_topic = fuzzy_match_topic(topic_query, topics_cache)
                
                if matched_topic:
                    # Find topic details
                    original_topic_name = None
                    for topic in all_topics:
                        if topic['TopicName'].lower() == matched_topic[0]:
                            original_topic_name = topic['TopicName']
                            topic_id = topic['TopicID']
                            break
                            
                    if original_topic_name:
                        questions = get_questions_for_topic(topic_id)
                        print(f"\nQuestions for {original_topic_name}:")
                        
                        # Save questions to cache for reference
                        questions_cache = {q['QuestionID']: q for q in questions}
                        
                        if questions:
                            for question in questions:
                                print(f"ID: {question['QuestionID']} - {question['Description']}")
                        else:
                            print("No questions available for this topic.")
                        continue
            
            print("Please specify a valid topic when listing questions.")
            continue

        # Fuzzy match using the preprocessed topics
        matched_topic = fuzzy_match_topic(normalized_query, topics_cache)
        if matched_topic:
            # Find the original topic name from the matched lowercase name
            original_topic_name = None
            for topic in all_topics:
                if topic['TopicName'].lower() == matched_topic[0]:
                    original_topic_name = topic['TopicName']
                    break
                    
            if not original_topic_name:
                print("Sorry, I couldn't find information about that topic.")
                continue
                
            # Fetch detailed info on the matched topic
            topic_details = get_topic_details(original_topic_name)
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
            
            # Save questions to cache for reference
            questions_cache = {q['QuestionID']: q for q in questions}
            
            if questions:
                print("\nSample Questions:")
                for question in questions:
                    print(f"ID: {question['QuestionID']} - {question['Description']}")
                    # Fetch and display steps for each question
                    steps = get_steps_for_question(question['QuestionID'])
                    if steps:
                        print(f"  (Use 'show steps for question {question['QuestionID']}' for detailed steps)")

        else:
            print("Sorry, I couldn't find information about that topic.")

# Run the expert system
if __name__ == "__main__":
    expert_system()