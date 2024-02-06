import argparse
from langchain.vectorstores.chroma import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from fuzzywuzzy import fuzz

CHROMA_PATH = "chroma"
COUNTER_FILE = "consecutive_apology_counter.txt"


# Load environment variables from a .env file
load_dotenv()

PROMPT_TEMPLATE = """
Hello! I'm here to assist you in the best way possible. How may I help you today?

Your question or request:

{query_text}

---

Additional information based on your query (please provide only important details):

{context}
"""

def contains_apology(text):
    apology_phrases = ["I'm sorry", "I apologize", "my apologies", "sorry for", "Apologies", "Sorry"]
    for phrase in apology_phrases:
        if phrase.lower() in text.lower():
            return True
    return False

def contains_semantic_request(query_text):
    keywords = ["connect", "human agent", "live agent", "speak to someone"]
    
    # Check if any of the keywords are present in the query_text
    return any(keyword in query_text.lower() for keyword in keywords)


def save_counter(counter):
    with open(COUNTER_FILE, "w") as file:
        file.write(str(counter))

def load_counter():
    val = 0
    try:
        with open(COUNTER_FILE, "r") as file:
            value = int(file.read())
            val = value
    except FileNotFoundError:
        return 0
    return val

def respond_to_greeting(greeting):
    greetings_list = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
    farewells_list = ["bye", "goodbye", "see you", "farewell"]
    gratitude_list = ["thank you", "thanks", "appreciate it", "thanks a lot"]

    # Check for similarity to predefined greetings, farewells, and gratitude expressions
    similarity_scores_greetings = {greet: fuzz.ratio(greeting.lower(), greet) for greet in greetings_list}
    similarity_scores_farewells = {farewell: fuzz.ratio(greeting.lower(), farewell) for farewell in farewells_list}
    similarity_scores_gratitude = {thanks: fuzz.ratio(greeting.lower(), thanks) for thanks in gratitude_list}

    # Identify the best match for each category
    best_match_greeting = max(similarity_scores_greetings, key=similarity_scores_greetings.get)
    best_match_farewell = max(similarity_scores_farewells, key=similarity_scores_farewells.get)
    best_match_gratitude = max(similarity_scores_gratitude, key=similarity_scores_gratitude.get)

    # Adjust the threshold as needed
    responses = []

    if similarity_scores_greetings[best_match_greeting] > 70:
        responses.append(f"Response: {best_match_greeting.capitalize()}! How can I assist you today?")

    if similarity_scores_farewells[best_match_farewell] > 70:
        responses.append(f"Response: {best_match_farewell.capitalize()}! If you have more questions, feel free to ask.")

    if similarity_scores_gratitude[best_match_gratitude] > 70:
        responses.append(f"Response: You're welcome! If you need further assistance, don't hesitate to ask.")

    return "\n".join(responses) if responses else None

def main():
    print("Starting Script.................")
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    query_text = args.query_text

    # Load the counter from the file or initialize to 0 if not exists
    consecutive_apology_counter = load_counter()

    print(consecutive_apology_counter, "APP")

    # Check for similar greetings
    greeting_response = respond_to_greeting(query_text)
    if greeting_response:
        print(greeting_response)
        return

    # Check for semantic requests to connect to a human agent
    print(contains_semantic_request(query_text), "SEMATIC")
    if contains_semantic_request(query_text):
        user_response = input("Response: I'm here to help! Would you like to connect to a live human agent? (yes/no) ").lower()
        if user_response == "yes" or user_response == "y":
            # Connect to the live chat via WebSocket (you need to implement this part)
            print("Connecting to live chat...")
            # After returning human agent response, reset the counter to 0
            consecutive_apology_counter = 0
            # Save the updated counter to the file
            save_counter(consecutive_apology_counter)
            return
        else:
            print("Okay, feel free to ask another question.")
            # After returning human agent response, reset the counter to 0
            consecutive_apology_counter = 1
            # Save the updated counter to the file
            save_counter(consecutive_apology_counter)
            return

    # Prepare the DB.
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    if len(results) > 0 and results[0][1] >= 0.7:
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    else:
        context_text = "I couldn't find additional information related to your query."

    # Check if consecutive apology threshold is reached
    if consecutive_apology_counter >= 2:
        print("Response: I apologize for any confusion. It seems I'm having difficulty understanding your query. Would you like to talk to a live human agent?")
        user_response = input("Your response (yes/no): ").lower()
        if user_response == "yes" or user_response == "y":
            # Connect to the live chat via WebSocket (you need to implement this part)
            print("Connecting to live chat...")
            # After returning human agent response, reset the counter to 0
            consecutive_apology_counter = 0
            # Save the updated counter to the file
            save_counter(consecutive_apology_counter)
            return
        else:
            print("Okay, feel free to ask another question.")
            # After returning human agent response, reset the counter to 0
            consecutive_apology_counter = 1
            # Save the updated counter to the file
            save_counter(consecutive_apology_counter)
            return

    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(query_text=query_text, context=context_text)

    model = ChatOpenAI()
    response_text = model.predict(prompt)

    # Check if the response contains an apology
    if contains_apology(response_text):
        print("I am here")
        consecutive_apology_counter += 1
    else:
        consecutive_apology_counter = 0 

    # Save the updated counter to the file
    print(consecutive_apology_counter)
    save_counter(consecutive_apology_counter)

    sources = [doc.metadata.get("source", None) for doc, _score in results]
    formatted_response = f"Response: {response_text}\nSources: {sources}"
    print(formatted_response)

if __name__ == "__main__":
    main()
