import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
import os
import re
from fuzzywuzzy import process, fuzz
import functools
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='addmaths_ai.log'
)
logger = logging.getLogger('addmaths_ai')

# Load environment variables once at startup
try:
    load_dotenv("C:/Users/User/AddmathsAI/AddmathsESKey.env")
    logger.info("Environment variables loaded successfully")
except Exception as e:
    logger.error(f"Failed to load environment variables: {e}")

# Constants
FUZZY_MATCH_THRESHOLD = 50
MAX_POOL_SIZE = 5
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "addmaths_es"
}

# Global caches
topics_cache = {}
questions_cache = {}

# Create a connection pool
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="addmaths_pool",
        pool_size=MAX_POOL_SIZE,
        **DB_CONFIG
    )
    logger.info("Database connection pool created successfully")
except mysql.connector.Error as err:
    logger.critical(f"Failed to create connection pool: {err}")
    exit(1)

# Context manager for database connections
@contextmanager
def get_db_connection():
    conn = connection_pool.get_connection()
    try:
        yield conn
    finally:
        conn.close()

# Fetch data from the database with improved error handling
def fetch_from_db(query, params=None):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            cursor.close()
            return results
    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}, Query: {query}, Params: {params}")
        return []

# Cache decorators with improved timeouts and error handling
@functools.lru_cache(maxsize=32, typed=True)
def get_all_topics():
    logger.debug("Fetching all topics from database")
    query = "SELECT TopicID, TopicName FROM topic"
    results = fetch_from_db(query)
    return results or []

@functools.lru_cache(maxsize=128, typed=True)
def get_all_questions():
    logger.debug("Fetching all questions from database")
    query = """
    SELECT q.QuestionID, q.Description, t.TopicName 
    FROM questions q
    JOIN topic t ON q.TopicID = t.TopicID
    ORDER BY t.TopicName, q.QuestionID
    """
    return fetch_from_db(query)

@functools.lru_cache(maxsize=32, typed=True)
def get_topic_details(topic_name):
    query = "SELECT * FROM topic WHERE TopicName = %s"
    topics = fetch_from_db(query, (topic_name,))
    return topics[0] if topics else None

@functools.lru_cache(maxsize=32, typed=True)
def get_formulas_for_topic(topic_id):
    query = "SELECT FormulaContent FROM formulas WHERE TopicID = %s"
    return fetch_from_db(query, (topic_id,))

@functools.lru_cache(maxsize=64, typed=True)
def get_steps_for_question(question_id):
    query = "SELECT Description FROM steps WHERE QuestionID = %s"
    return fetch_from_db(query, (question_id,))

@functools.lru_cache(maxsize=32, typed=True)
def get_questions_for_topic(topic_id):
    query = "SELECT QuestionID, Description FROM questions WHERE TopicID = %s"
    return fetch_from_db(query, (topic_id,))

@functools.lru_cache(maxsize=32, typed=True)
def get_question_by_id(question_id):
    query = "SELECT QuestionID, Description, TopicID FROM questions WHERE QuestionID = %s"
    questions = fetch_from_db(query, (question_id,))
    return questions[0] if questions else None

# Clear all caches
def clear_caches():
    get_all_topics.cache_clear()
    get_all_questions.cache_clear()
    get_topic_details.cache_clear()
    get_formulas_for_topic.cache_clear()
    get_steps_for_question.cache_clear()
    get_questions_for_topic.cache_clear()
    get_question_by_id.cache_clear()
    logger.info("All caches cleared")

# Text processing utilities
def normalize_input(user_input):
    """Normalize and clean user input"""
    return re.sub(r'\s+', ' ', user_input.strip().lower())

def preprocess_topics(topics):
    """Preprocess topics for faster matching"""
    global topics_cache
    topics_cache = {topic['TopicID']: topic['TopicName'].lower() for topic in topics}
    logger.debug(f"Topics preprocessed: {len(topics_cache)} topics cached")

def fuzzy_match_topic(user_query, topics_dict):
    """Find the best matching topic using fuzzy logic"""
    best_match = None
    highest_score = 0
    
    for topic_id, topic_name in topics_dict.items():
        score = fuzz.token_sort_ratio(user_query, topic_name)
        if score > highest_score and score > FUZZY_MATCH_THRESHOLD:
            highest_score = score
            best_match = topic_name
    
    return (best_match, highest_score) if best_match else None

# Pattern matching for user queries
def extract_question_id(query_text):
    """Extract question ID from input text"""
    patterns = [
        r'question\s+(\d+)',  # question 5
        r'q\s*(\d+)',         # q5 or q 5
        r'#\s*(\d+)',         # #5 or # 5
        r'number\s+(\d+)',    # number 5
        r'(\d+)',             # Just try to find any number as a fallback
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query_text)
        if match:
            return int(match.group(1))
    return None

def determine_intent(user_query):
    """Determine user intent from query"""
    query = user_query.lower()
    
    # Intent for listing all questions
    if any(phrase in query for phrase in ['all questions', 'every question', 'list all questions', 'show all questions', 
                                         'all problems', 'every problem', 'all exercises']):
        return "list_all_questions"
    
    # Intent for listing topics
    if any(keyword in query for keyword in ['list topic', 'show topic', 'all topic', 'what topic', 'available topic']):
        return "list_topics"
    
    # Intent for showing steps for a question
    if any(keyword in query for keyword in ['step', 'solution', 'solve', 'how to']) and extract_question_id(query):
        return "show_steps"
    
    # Intent for listing questions for a topic
    list_questions_patterns = [
        r'(list|show|get|what|give)\s+.*(questions|problems|exercises).*(?:for|on|about|in)\s+(.+)',
        r'questions\s+(?:for|on|about|in)\s+(.+)',
        r'problems\s+(?:for|on|about|in)\s+(.+)'
    ]
    
    for pattern in list_questions_patterns:
        match = re.search(pattern, query)
        if match:
            # If the pattern has 3 groups, the topic is in the 3rd group
            # If it has fewer, the topic is in the last group
            topic_group = match.group(3) if len(match.groups()) >= 3 else match.group(len(match.groups()))
            return "list_questions_for_topic", topic_group.strip()
    
    # Default intent is to show topic information
    return "show_topic_info"

def extract_topic_from_query(query, pattern_type="questions"):
    """Extract topic from user query"""
    if pattern_type == "questions":
        patterns = [
            r'(?:questions|problems)\s+(?:for|on|about|in)\s+(.+)',
            r'(?:list|show|get)\s+(?:questions|problems).*(?:for|on|about|in)\s+(.+)',
            r'what\s+(?:questions|problems).*(?:for|on|about|in)\s+(.+)'
        ]
    else:
        patterns = [r'(.+)']  # Fallback pattern to capture anything
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            return match.group(1).strip()
    
    return query  # Return the original query if no pattern matches

# Command handlers
def handle_list_all_questions():
    """Handler for listing all questions"""
    all_questions = get_all_questions()
    
    if not all_questions:
        return "No questions available in the database."
    
    global questions_cache
    questions_cache = {q['QuestionID']: q for q in all_questions}
    
    output = ["\nAll Available Questions:", "======================="]
    current_topic = None
    
    for question in all_questions:
        # Print topic header when topic changes
        if current_topic != question['TopicName']:
            current_topic = question['TopicName']
            output.append(f"\n[{current_topic}]")
        
        output.append(f"ID: {question['QuestionID']} - {question['Description']}")
    
    output.append("\nTo see steps for any question, ask 'show steps for question #'")
    return "\n".join(output)

def handle_list_topics():
    """Handler for listing all topics"""
    all_topics = get_all_topics()
    topic_names = [topic['TopicName'] for topic in all_topics]
    
    output = ["\nAvailable Topics:", "----------------"]
    for name in topic_names:
        output.append(f"- {name}")
    
    output.append("\nFor information on a topic, just type its name.")
    output.append("To see questions for a topic, type 'list questions for [topic name]'")
    
    return "\n".join(output)

def handle_show_steps(normalized_query):
    """Handler for showing steps to solve a question"""
    question_id = extract_question_id(normalized_query)
    if not question_id:
        return "I couldn't identify which question you're asking about. Please include a question number."
    
    question = get_question_by_id(question_id)
    if not question:
        return f"Question with ID {question_id} not found."
    
    steps = get_steps_for_question(question_id)
    output = [f"\nQuestion {question_id}: {question['Description']}"]
    
    if steps:
        output.append("Steps:")
        for i, step in enumerate(steps, 1):
            output.append(f"{i}. {step['Description']}")
    else:
        output.append("No steps available for this question.")
    
    return "\n".join(output)

def handle_list_questions_for_topic(topic_query, all_topics):
    """Handler for listing questions for a specific topic"""
    matched_topic = fuzzy_match_topic(topic_query, topics_cache)
    
    if not matched_topic:
        return f"I couldn't find the topic '{topic_query}'. Please try another topic."
    
    # Find topic details
    original_topic_name = None
    topic_id = None
    
    for topic in all_topics:
        if topic['TopicName'].lower() == matched_topic[0]:
            original_topic_name = topic['TopicName']
            topic_id = topic['TopicID']
            break
            
    if not original_topic_name:
        return f"I couldn't find the topic '{topic_query}'. Please try another topic."
    
    questions = get_questions_for_topic(topic_id)
    global questions_cache
    questions_cache = {q['QuestionID']: q for q in questions}
    
    output = [f"\nQuestions for {original_topic_name}:", 
              "-" * (len(f"Questions for {original_topic_name}:"))]
    
    if questions:
        for question in questions:
            output.append(f"ID: {question['QuestionID']} - {question['Description']}")
        output.append("\nTo see steps for a question, type 'show steps for question #'")
    else:
        output.append("No questions available for this topic.")
    
    return "\n".join(output)

def handle_show_topic_info(normalized_query, all_topics):
    """Handler for showing information about a topic"""
    # First try to match directly with the topics
    matched_topic = fuzzy_match_topic(normalized_query, topics_cache)
    
    if not matched_topic:
        # If no direct match, try to extract potential topic mentions
        words = re.findall(r'\b\w+\b', normalized_query)
        for i in range(len(words)):
            for j in range(i + 1, min(i + 5, len(words) + 1)):  # Look at phrases up to 4 words long
                phrase = ' '.join(words[i:j])
                if len(phrase) > 2:  # Only consider phrases longer than 2 characters
                    potential_match = fuzzy_match_topic(phrase, topics_cache)
                    if potential_match and (not matched_topic or potential_match[1] > matched_topic[1]):
                        matched_topic = potential_match
    
    if not matched_topic:
        return ("I'm not sure what topic you're asking about.\n"
                "Type 'list topics' to see all available topics or 'help' for command assistance.")
    
    # Find the original topic name from the matched lowercase name
    original_topic_name = None
    for topic in all_topics:
        if topic['TopicName'].lower() == matched_topic[0]:
            original_topic_name = topic['TopicName']
            break
            
    if not original_topic_name:
        return ("Sorry, I couldn't find information about that topic.\n"
                "Try asking about a specific mathematics topic or type 'list topics' to see what's available.")
    
    # Fetch detailed info on the matched topic
    topic_details = get_topic_details(original_topic_name)
    if not topic_details:
        return "Sorry, I couldn't find information about that topic."

    topic_id = topic_details['TopicID']
    topic_name = topic_details['TopicName']

    output = [f"\nTopic: {topic_name}", "-" * (len(f"Topic: {topic_name}"))]

    # Retrieve and display formulas
    formulas = get_formulas_for_topic(topic_id)
    if formulas:
        output.append("\nFormulas:")
        for formula in formulas:
            output.append(f"- {formula['FormulaContent']}")

    # Retrieve and display questions
    questions = get_questions_for_topic(topic_id)
    
    # Save questions to cache for reference
    global questions_cache
    questions_cache = {q['QuestionID']: q for q in questions}
    
    if questions:
        output.append("\nSample Questions:")
        for question in questions:
            output.append(f"ID: {question['QuestionID']} - {question['Description']}")
        output.append("\nTo see steps for a question, type 'show steps for question #'")
    else:
        output.append("\nNo questions available for this topic.")
    
    return "\n".join(output)

def show_help():
    """Display help information"""
    return """
==================================================
ADDMATHS EXPERT SYSTEM - COMMAND GUIDE
==================================================
You can use these commands or natural language queries:

1. TOPIC INFORMATION:
   - Just type a topic name (e.g., 'Fungsi', 'Janjang')
   - You'll get formulas and sample questions for that topic

2. LIST COMMANDS:
   - 'list topics' or 'show available topics'
   - 'list questions for [topic]' (e.g., 'list questions for Fungsi')
   - 'list all questions' or 'show all questions'

3. QUESTION SOLUTIONS:
   - 'show steps for question 5' or 'solution for q5'
   - 'how to solve question 12' or 'steps for #12'

4. OTHER COMMANDS:
   - 'help' - Show this guide again
   - 'exit' - Quit the program
==================================================
"""

# Main expert system logic
def expert_system():
    """Main function to run the expert system"""
    logger.info("Starting AddMaths Expert System")
    
    print("\n" + "="*60)
    print("     WELCOME TO THE ADDMATHS EXPERT SYSTEM!")
    print("="*60)
    print("This system helps with additional mathematics topics,")
    print("formulas, and step-by-step solutions to problems.")
    
    # Show initial help
    print(show_help())
    
    # Fetch all topics from the database once
    try:
        all_topics = get_all_topics()
        if not all_topics:
            logger.critical("Failed to load topics from database")
            print("Error: Unable to load topics from database. Please check your connection.")
            return
        
        preprocess_topics(all_topics)
        logger.info(f"Loaded {len(all_topics)} topics from database")
    except Exception as e:
        logger.critical(f"Fatal error during startup: {e}")
        print("Error: Unable to initialize the expert system. Please check the log for details.")
        return

    while True:
        try:
            user_query = input("\nWhat would you like to know? ").strip()
            logger.debug(f"User query: {user_query}")
            
            if user_query.lower() == "exit":
                print("Goodbye!")
                logger.info("User exited the system")
                break
                
            if user_query.lower() == "help":
                print(show_help())
                continue
            
            # Normalize and process user input
            normalized_query = normalize_input(user_query)
            
            # Determine the user's intent
            intent_result = determine_intent(normalized_query)
            logger.debug(f"Determined intent: {intent_result}")
            
            # Unpack the intent result
            if isinstance(intent_result, tuple):
                intent, *extra_args = intent_result
            else:
                intent = intent_result
                extra_args = []

            # Handle different intents using dedicated handlers
            response = None
            
            if intent == "list_all_questions":
                response = handle_list_all_questions()
                
            elif intent == "list_topics":
                response = handle_list_topics()
                
            elif intent == "show_steps":
                response = handle_show_steps(normalized_query)
                
            elif intent == "list_questions_for_topic":
                topic_query = extra_args[0] if extra_args else extract_topic_from_query(normalized_query)
                response = handle_list_questions_for_topic(topic_query, all_topics)
                
            elif intent == "show_topic_info":
                response = handle_show_topic_info(normalized_query, all_topics)
            
            # Print the response
            if response:
                print(response)
                
        except KeyboardInterrupt:
            print("\nExiting program...")
            logger.info("User interrupted the program")
            break
            
        except Exception as e:
            logger.error(f"Error processing query '{user_query}': {e}", exc_info=True)
            print(f"Sorry, an error occurred: {e}")
            print("Please try again or type 'help' for assistance.")

# Run the expert system
if __name__ == "__main__":
    try:
        expert_system()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        print(f"A critical error occurred: {e}")
        print("Please check the log file for details.")
    finally:
        # Clean up resources
        clear_caches()
        logger.info("Expert system shutdown complete")