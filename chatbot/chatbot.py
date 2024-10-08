import json
from typing import List, Dict
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import streamlit as st

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


# Function to load JSON data from a file
def load_clubs_data(file_path: str) -> List[Dict]:
    with open(file_path, "r") as file:
        return json.load(file)


# Load the JSON data from a file
clubs_data = load_clubs_data("chatbot/all_organizations.json")

# Prepare the data for embedding
texts = [f"{club['name']}: {club['description']}" for club in clubs_data]

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings(openai_api_key=st.secrets["OPENAI_API_KEY"])

# Create a vector store
vector_store = FAISS.from_texts(texts, embeddings)


def extract_sub_queries(query: str, history: List[Dict[str, str]] = None) -> List[str]:
    # Prepare the conversation history
    conversation = ""
    if history:
        for message in history:
            conversation += f"{message['role'].capitalize()}: {message['content']}\n"

    conversation += f"Human: {query}\n"
    # Use GPT to extract relevant keywords and phrases for vector search
    messages = [
        {
            "role": "system",
            "content": "You are an AI assistant that extracts relevant keywords and phrases for searching university clubs and organizations. Focus on extracting terms that might appear in club names or descriptions. Consider the entire conversation context when extracting search terms.Please make sure to look at last human query and be very relevant to that. Also you allowed to output nothing if the conversation does not need some club info right now.",
        },
        {
            "role": "user",
            "content": f"Given the following conversation, extract relevant search terms for finding university clubs and organizations. Provide only the search terms, separated by newlines. Keep terms concise and relevant to club names or activities.\n\nConversation:\n{conversation}",
        },
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", messages=messages, max_tokens=100
    )
    sub_queries = response.choices[0].message.content.strip().split("\n")
    return [sq.strip() for sq in sub_queries if sq.strip()]


def find_most_similar_texts(query: str, top_k: int = 3) -> List[Dict]:
    similar_docs = vector_store.similarity_search(query, k=top_k)
    results = []
    for doc in similar_docs:
        club_info = next(
            (club for club in clubs_data if f"{club['name']}:" in doc.page_content),
            None,
        )
        if club_info:
            results.append(
                {
                    "content": doc.page_content,
                    "name": club_info["name"],
                    "link": club_info["link"],
                    "image_url": club_info.get("image_url"),
                }
            )
    return results


def get_club_info(query: str, history: List[Dict[str, str]] = None):
    # Extract search terms (subqueries) from the main query and conversation history
    search_terms = extract_sub_queries(query, history)

    # Find relevant texts for each search term
    all_relevant_texts = []
    for term in search_terms:
        relevant_texts = find_most_similar_texts(term)
        all_relevant_texts.extend(relevant_texts)

    # Remove duplicates while preserving order
    seen = set()
    unique_relevant_texts = [
        x for x in all_relevant_texts if not (x["name"] in seen or seen.add(x["name"]))
    ]

    # Prepare the context with club information
    context = ""
    for text in unique_relevant_texts:
        context += f"{text['content']}\n"
        context += f"Club Name: {text['name']}\n"
        context += f"Club Link: {text['link']}\n"
        if text["image_url"]:
            context += f"Club Image: {text['image_url']}\n"
        context += "\n"

    # Prepare the messages for the chat completion
    messages = [
        {
            "role": "system",
            "content": """You are a helpful assistant that provides information about clubs and organizations to uAlberta students. Many students have been feeling lonely
                        recently, and your goal is to help. uAlberta is a commuter school, and it can be very hard to make friends or socialize unless you are very active in the community
                        and join clubs that interest you! Please help these people get out and become their best selves! 
                        
                        When mentioning a specific club, format your response like this:
                        
                        Club Name: [club name]
                        Club Link: [club link]
                        Club Image: [image url] (if available)
                        
                        [Your description and recommendation about the club]
                        
                        This formatting will allow the chat interface to properly display images and clickable links.""",
        },
    ]

    # Add conversation history if provided
    if history:
        for message in history:
            messages.append({"role": message["role"], "content": message["content"]})

    # Add the current query and context to the messages
    messages.append(
        {
            "role": "user",
            "content": f"Based on the following information about clubs and organizations, please answer the user's question: {context}\n\nUser's query: {query}",
        }
    )

    # Get the response from OpenAI
    response = client.chat.completions.create(
        model="gpt-4", messages=messages, stream=True
    )

    for chunk in response:
        yield chunk
