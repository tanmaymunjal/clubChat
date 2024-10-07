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


# Function to find most similar texts using FAISS
def find_most_similar_texts(query: str, top_k: int = 5) -> List[Dict]:
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


def get_club_info(query: str, history: List[Dict[str, str]] = None) -> str:
    # Find most relevant texts
    relevant_texts = find_most_similar_texts(query)

    # Prepare the context with club information, including links and images
    context = ""
    for text in relevant_texts:
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
                        
                        This formatting will allow the chat interface to properly display images and clickable links. Make sure to format the image link such that the
                        image is visible on something like streamlit interface!""",
        },
        {
            "role": "user",
            "content": f"Based on the following information about clubs and organizations, please answer the user's question: {context}",
        },
    ]

    # Add conversation history if provided
    if history:
        for message in history:
            messages.append({"role": message["role"], "content": message["content"]})

    # Add the current query to the messages
    messages.append({"role": "user", "content": query})

    # Get the response from OpenAI
    response = client.chat.completions.create(
        model="gpt-4", messages=messages, stream=True
    )

    for chunk in response:
            yield chunk
