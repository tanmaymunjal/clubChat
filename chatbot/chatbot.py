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
clubs_data = load_clubs_data("../scrape_data/all_organizations.json")

# Prepare the data for embedding
texts = [f"{club['name']}: {club['description']}" for club in clubs_data]

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings(openai_api_key=st.secrets["OPENAI_API_KEY"])

# Create a vector store
vector_store = FAISS.from_texts(texts, embeddings)


# Function to find most similar texts using FAISS
def find_most_similar_texts(query: str, top_k: int = 5) -> List[str]:
    similar_docs = vector_store.similarity_search(query, k=top_k)
    return [doc.page_content for doc in similar_docs]


def get_club_info(query: str, history: List[Dict[str, str]] = None) -> str:
    # Find most relevant texts
    relevant_texts = find_most_similar_texts(query)

    # Prepare the messages for the chat completion
    messages = [
        {
            "role": "system",
            "content": """You are a helpful assistant that provides information about clubs and organizations to uAlberta student.A lot of them have been feeling very lonely
                        recently and your goal is to help. uAlberta is a commuter school and it can be very hard to make friends or socialize unless you are very active in the community
                        and join clubs that interest you! Please help these poeple get out and become their best self!""",
        },
        {
            "role": "user",
            "content": f"Based on the following information about clubs and organizations, please answer the user's question: {' '.join(relevant_texts)}",
        },
        {"role": "user", "content": query},
    ]

    # Add conversation history if provided
    if history:
        for message in history:
            messages.append({"role": message["role"], "content": message["content"]})

    # Get the response from OpenAI
    response = client.chat.completions.create(
        model="gpt-4", messages=messages, stream=True
    )

    for chunk in response:
        yield chunk
