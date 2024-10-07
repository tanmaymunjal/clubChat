import json
from typing import List, Dict
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import streamlit as st

# Function to load JSON data from a file
def load_clubs_data(file_path: str) -> List[Dict]:
    with open(file_path, 'r') as file:
        return json.load(file)

# Load the JSON data from a file
clubs_data = load_clubs_data('../scrape_data/all_organizations.json')

# Prepare the data for embedding
texts = [f"{club['name']}: {club['description']}" for club in clubs_data]

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings(openai_api_key=st.secrets["OPENAI_API_KEY"])

# Create a vector store
vector_store = FAISS.from_texts(texts, embeddings)

# Initialize the language model with streaming
llm = ChatOpenAI(
    temperature=0,
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()],
    openai_api_key=st.secrets["OPENAI_API_KEY"]
)

# Set up the conversational memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Create the conversational chain
qa_chain = ConversationalRetrievalChain.from_llm(
    llm,
    retriever=vector_store.as_retriever(),
    memory=memory,
    verbose=True
)

def get_club_info(query: str, history: List[Dict[str, str]] = None) -> str:
    if history:
        # Convert history to the format expected by ConversationBufferMemory
        formatted_history = []
        for message in history:
            print(message)
            if message['role'] == 'user':
                formatted_history.append(HumanMessage(content=message['content']))
            elif message['role'] == 'assistant':
                formatted_history.append(AIMessage(content=message['content']))
        
        # Update the conversation memory with the provided history
        memory.chat_memory.messages = formatted_history

    result = qa_chain({"question": query})
    return result['answer']