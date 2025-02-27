import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
import sys
import io
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
    # Don't exit immediately, allow GUI to handle the error

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

# GUI Application Class
class AddMathsGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AddMaths Expert System")
        self.geometry("800x600")
        self.iconbitmap("math_icon.ico") if os.path.exists("math_icon.ico") else None
        self.configure(bg="#f0f0f0")
        self.all_topics = []
        
        self.create_widgets()
        self.setup_styles()
        
        # Initialize system in a separate thread
        self.init_thread = threading.Thread(target=self.initialize_system)
        self.init_thread.daemon = True
        self.init_thread.start()
        
        # Quick access buttons
        self.create_quick_access_buttons()
        
        # Redirect stdout to our custom output
        self.old_stdout = sys.stdout
        sys.stdout = self
        
        # Set up protocol for window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        # Main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top frame for output
        self.output_frame = ttk.LabelFrame(self.main_frame, text="AddMaths AI Output")
        self.output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Output text area with scrollbar
        self.output_text = scrolledtext.ScrolledText(self.output_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.output_text.config(state=tk.DISABLED)
        
        # Bottom frame for input
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Initializing system...")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Input field and send button
        self.input_entry = ttk.Entry(self.input_frame, font=("Consolas", 10))
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_entry.bind("<Return>", self.process_input)
        
        self.send_button = ttk.Button(self.input_frame, text="Send", command=self.process_input)
        self.send_button.pack(side=tk.RIGHT)
        
        # Focus on input
        self.input_entry.focus_set()
    
    def create_quick_access_buttons(self):
        self.quick_frame = ttk.Frame(self.main_frame)
        self.quick_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.help_button = ttk.Button(self.quick_frame, text="Help", command=lambda: self.execute_command("help"))
        self.help_button.pack(side=tk.LEFT, padx=2)
        
        self.topics_button = ttk.Button(self.quick_frame, text="List Topics", command=lambda: self.execute_command("list topics"))
        self.topics_button.pack(side=tk.LEFT, padx=2)
        
        self.questions_button = ttk.Button(self.quick_frame, text="All Questions", command=lambda: self.execute_command("list all questions"))
        self.questions_button.pack(side=tk.LEFT, padx=2)
        
        self.clear_button = ttk.Button(self.quick_frame, text="Clear", command=self.clear_output)
        self.clear_button.pack(side=tk.RIGHT, padx=2)
    
    def setup_styles(self):
        # Configure ttk styles
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabelframe", background="#f0f0f0")
        style.configure("TLabelframe.Label", font=("Arial", 10, "bold"))
        style.configure("TButton", font=("Arial", 9))
    
    def initialize_system(self):
        try:
            # Update status
            self.status_var.set("Loading topics from database...")
            
            # Fetch all topics from the database
            self.all_topics = get_all_topics()
            if not self.all_topics:
                self.write_to_output("Error: Unable to load topics from database. Please check your connection.")
                self.status_var.set("Error: Database connection failed")
                return
            
            preprocess_topics(self.all_topics)
            
            # Ready
            self.status_var.set("Ready")
            
            # Show welcome message and help
            welcome_message = "\n" + "="*60 + "\n"
            welcome_message += "     WELCOME TO THE ADDMATHS EXPERT SYSTEM!\n"
            welcome_message += "="*60 + "\n"
            welcome_message += "This system helps with additional mathematics topics,\n"
            welcome_message += "formulas, and step-by-step solutions to problems.\n"
            
            self.write_to_output(welcome_message)
            self.write_to_output(show_help())
            
        except Exception as e:
            logger.critical(f"Fatal error during startup: {e}")
            self.write_to_output(f"Error: Unable to initialize the expert system.\nDetails: {e}")
            self.status_var.set("Initialization failed")
    
    def write_to_output(self, text):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def clear_output(self):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def process_input(self, event=None):
        # Get input and clear entry field
        user_query = self.input_entry.get().strip()
        self.input_entry.delete(0, tk.END)
        
        if not user_query:
            return
        
        # Echo user input in output area
        self.write_to_output(f"\n>> {user_query}")
        
        # Process exit command
        if user_query.lower() == "exit":
            self.on_closing()
            return
        
        # Process in a separate thread to avoid UI freeze
        threading.Thread(target=self.execute_command, args=(user_query,), daemon=True).start()
    
    def execute_command(self, user_query):
        try:
            self.status_var.set("Processing...")
            
            # If topics not loaded yet, show error
            if not self.all_topics:
                self.write_to_output("System is still initializing. Please wait...")
                self.status_var.set("Still initializing...")
                return
            
            # Process help command directly
            if user_query.lower() == "help":
                self.write_to_output(show_help())
                self.status_var.set("Ready")
                return
            
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
            response = None
            
            if intent == "list_all_questions":
                response = handle_list_all_questions()
                
            elif intent == "list_topics":
                response = handle_list_topics()
                
            elif intent == "show_steps":
                response = handle_show_steps(normalized_query)
                
            elif intent == "list_questions_for_topic":
                topic_query = extra_args[0] if extra_args else extract_topic_from_query(normalized_query)
                response = handle_list_questions_for_topic(topic_query, self.all_topics)
                
            elif intent == "show_topic_info":
                response = handle_show_topic_info(normalized_query, self.all_topics)
            
            # Display the response
            if response:
                self.write_to_output(response)
                
            self.status_var.set("Ready")
            
        except Exception as e:
            logger.error(f"Error processing query '{user_query}': {e}", exc_info=True)
            self.write_to_output(f"Sorry, an error occurred: {e}")
            self.status_var.set("Error occurred")
    
    def write(self, text):
        """Required for stdout redirection"""
        self.write_to_output(text.rstrip())
    
    def flush(self):
        """Required for stdout redirection"""
        pass
    
    def on_closing(self):
        # Restore stdout
        sys.stdout = self.old_stdout
        
        # Clear caches
        clear_caches()
        
        # Close window
        self.destroy()
        
        # Log shutdown
        logger.info("GUI application closed")

# Entry point
if __name__ == "__main__":
    try:
        app = AddMathsGUI()
        app.mainloop()
    except Exception as e:
        logger.critical(f"Fatal error in GUI application: {e}", exc_info=True)
        messagebox.showerror("Fatal Error", f"A critical error occurred: {e}\nPlease check the log file for details.")
    finally:
        # Clean up resources
        clear_caches()
        logger.info("Application shutdown complete")