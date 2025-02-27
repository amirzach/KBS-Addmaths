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

@functools.lru_cache(maxsize=128)
def get_all_questions():
    query = """
    SELECT q.QuestionID, q.Description, t.TopicName 
    FROM questions q
    JOIN topic t ON q.TopicID = t.TopicID
    ORDER BY t.TopicName, q.QuestionID
    """
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
        if score > highest_score and score > 50:  # Reduced threshold for more flexibility
            highest_score = score
            best_match = topic_name
    
    return (best_match, highest_score) if best_match else None

# Extract question ID from input
def extract_question_id(query_text):
    # Multiple patterns to match different ways of specifying a question
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

# Determine intent from user query
def determine_intent(user_query):
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

# Extract topic from questions query
def extract_topic_from_query(query, pattern_type="questions"):
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

# Display help information
def show_help():
    print("\n" + "="*50)
    print("ADDMATHS EXPERT SYSTEM - COMMAND GUIDE")
    print("="*50)
    print("You can use these commands or natural language queries:")
    print("\n1. TOPIC INFORMATION:")
    print("   - Just type a topic name (e.g., 'Fungsi', 'Janjang')")
    print("   - You'll get formulas and sample questions for that topic")
    
    print("\n2. LIST COMMANDS:")
    print("   - 'list topics' or 'show available topics'")
    print("   - 'list questions for [topic]' (e.g., 'list questions for Fungsi')")
    print("   - 'list all questions' or 'show all questions'")
    
    print("\n3. QUESTION SOLUTIONS:")
    print("   - 'show steps for question 5' or 'solution for q5'")
    print("   - 'how to solve question 12' or 'steps for #12'")
    
    print("\n4. OTHER COMMANDS:")
    print("   - 'help' - Show this guide again")
    print("   - 'exit' - Quit the program")
    print("="*50)

# Main expert system logic
def expert_system():
    global questions_cache
    
    print("\n" + "="*60)
    print("     WELCOME TO THE ADDMATHS EXPERT SYSTEM!")
    print("="*60)
    print("This system helps with additional mathematics topics,")
    print("formulas, and step-by-step solutions to problems.")
    
    # Show initial help
    show_help()
    
    # Fetch all topics from the database once
    all_topics = get_all_topics()
    preprocess_topics(all_topics)

    while True:
        user_query = input("\nWhat would you like to know? ").strip()
        
        if user_query.lower() == "exit":
            print("Goodbye!")
            break
            
        if user_query.lower() == "help":
            show_help()
            continue
        
        # Normalize and process user input
        normalized_query = normalize_input(user_query)
        
        # Determine the user's intent
        intent_result = determine_intent(normalized_query)
        
        # Unpack the intent result
        if isinstance(intent_result, tuple):
            intent, *extra_args = intent_result
        else:
            intent = intent_result
            extra_args = []

        # Handle different intents
        if intent == "list_all_questions":
            all_questions = get_all_questions()
            
            if all_questions:
                current_topic = None
                print("\nAll Available Questions:")
                print("=======================")
                
                for question in all_questions:
                    # Print topic header when topic changes
                    if current_topic != question['TopicName']:
                        current_topic = question['TopicName']
                        print(f"\n[{current_topic}]")
                    
                    print(f"ID: {question['QuestionID']} - {question['Description']}")
                
                questions_cache = {q['QuestionID']: q for q in all_questions}
                print("\nTo see steps for any question, ask 'show steps for question #'")
            else:
                print("No questions available in the database.")
        
        elif intent == "list_topics":
            topic_names = [topic['TopicName'] for topic in all_topics]
            print("\nAvailable Topics:")
            print("----------------")
            for name in topic_names:
                print(f"- {name}")
            print("\nFor information on a topic, just type its name.")
            print("To see questions for a topic, type 'list questions for [topic name]'")
                
        elif intent == "show_steps":
            question_id = extract_question_id(normalized_query)
            if question_id:
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
            else:
                print("I couldn't identify which question you're asking about. Please include a question number.")
                
        elif intent == "list_questions_for_topic":
            topic_query = extra_args[0] if extra_args else extract_topic_from_query(normalized_query)
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
                    print("-" * (len(f"Questions for {original_topic_name}:")))
                    
                    # Save questions to cache for reference
                    questions_cache = {q['QuestionID']: q for q in questions}
                    
                    if questions:
                        for question in questions:
                            print(f"ID: {question['QuestionID']} - {question['Description']}")
                        print("\nTo see steps for a question, type 'show steps for question #'")
                    else:
                        print("No questions available for this topic.")
                else:
                    print(f"I couldn't find the topic '{topic_query}'. Please try another topic.")
            else:
                print(f"I couldn't find the topic '{topic_query}'. Please try another topic.")
                
        elif intent == "show_topic_info":
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
            
            if matched_topic:
                # Find the original topic name from the matched lowercase name
                original_topic_name = None
                for topic in all_topics:
                    if topic['TopicName'].lower() == matched_topic[0]:
                        original_topic_name = topic['TopicName']
                        break
                        
                if not original_topic_name:
                    print("Sorry, I couldn't find information about that topic.")
                    print("Try asking about a specific mathematics topic or type 'list topics' to see what's available.")
                    continue
                    
                # Fetch detailed info on the matched topic
                topic_details = get_topic_details(original_topic_name)
                if not topic_details:
                    print("Sorry, I couldn't find information about that topic.")
                    continue

                topic_id = topic_details['TopicID']
                topic_name = topic_details['TopicName']

                print(f"\nTopic: {topic_name}")
                print("-" * (len(f"Topic: {topic_name}")))

                # Retrieve and display formulas
                formulas = get_formulas_for_topic(topic_id)
                if formulas:
                    print("\nFormulas:")
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
                    print("\nTo see steps for a question, type 'show steps for question #'")
                else:
                    print("\nNo questions available for this topic.")

            else:
                print("I'm not sure what topic you're asking about.")
                print("Type 'list topics' to see all available topics or 'help' for command assistance.")

# Run the expert system
if __name__ == "__main__":
    expert_system()