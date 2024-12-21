import mysql.connector
import openai

# Configure OpenAI API key
openai.api_key = "your_openai_api_key"

# Connect to MySQL database
def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user="your_mysql_user",
        password="your_mysql_password",
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

# Get topic details
def get_topic_details(topic_name):
    query = "SELECT * FROM topics WHERE TopicName = %s"
    topics = fetch_from_db(query, (topic_name,))
    return topics[0] if topics else None

# Get formulas for a topic
def get_formulas_for_topic(topic_id):
    query = "SELECT FormulaContent FROM formulas WHERE TopicID = %s"
    return fetch_from_db(query, (topic_id,))

# Get steps for a topic
def get_steps_for_topic(topic_id):
    query = "SELECT Description FROM steps WHERE TopicID = %s"
    return fetch_from_db(query, (topic_id,))

# Get questions for a topic
def get_questions_for_topic(topic_id):
    query = "SELECT QuestionContent FROM questions WHERE TopicID = %s"
    return fetch_from_db(query, (topic_id,))

# Get subquestions for a topic
def get_subquestions_for_topic(topic_id):
    query = "SELECT SubQuestionContent FROM subquestions WHERE TopicID = %s"
    return fetch_from_db(query, (topic_id,))

# Generate AI response
def generate_ai_response(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )
    return response['choices'][0]['text'].strip()

# Main expert system logic
def expert_system():
    print("Welcome to the AddMaths Expert System!")
    while True:
        user_query = input("\nEnter your query (or type 'exit' to quit): ").strip().lower()
        if user_query == "exit":
            print("Goodbye!")
            break
        
        # Match user query to a topic
        topic_details = get_topic_details(user_query)
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
        
        # Retrieve and display steps
        steps = get_steps_for_topic(topic_id)
        if steps:
            print("\nSteps:")
            for i, step in enumerate(steps, 1):
                print(f"{i}. {step['Description']}")
        
        # Retrieve and display questions
        questions = get_questions_for_topic(topic_id)
        if questions:
            print("\nSample Questions:")
            for i, question in enumerate(questions, 1):
                print(f"{i}. {question['QuestionContent']}")
        
        # Retrieve and display subquestions
        subquestions = get_subquestions_for_topic(topic_id)
        if subquestions:
            print("\nSub-questions:")
            for i, subquestion in enumerate(subquestions, 1):
                print(f"{i}. {subquestion['SubQuestionContent']}")
        
        # AI-powered explanation
        explanation_prompt = f"Explain the topic '{topic_name}' in simple terms."
        explanation = generate_ai_response(explanation_prompt)
        print("\nAI Explanation:")
        print(explanation)

# Run the expert system
if __name__ == "__main__":
    expert_system()
