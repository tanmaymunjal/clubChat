import streamlit as st
from chatbot import get_club_info
from streamlit_extras.colored_header import colored_header
from streamlit_extras.app_logo import add_logo


def set_page_config():
    st.set_page_config(page_title="clubChat UAlberta", page_icon="🎓", layout="wide")


def apply_custom_css():
    st.markdown(
        """
    <style>
    .stChat {
        border-radius: 10px;
        border: 1px solid rgba(var(--text-color), 0.1);
    }
    .stTextInput > div > div > input {
        border-radius: 20px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def main():
    set_page_config()
    apply_custom_css()

    # Add logo (replace with UAlberta logo URL)
    add_logo(
        "https://www.ualberta.ca/media-library/ualberta/homepage/university-of-alberta-logo.jpg"
    )

    # Sidebar
    with st.sidebar:
        st.title("About")
        st.info("This chatbot provides information about UAlberta clubs.")

    # Main content
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        colored_header(
            label="clubChat UAlberta",
            description="Ask me about University of Alberta clubs!",
            color_name="green-70",
        )

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Accept user input
        if prompt := st.chat_input("Ask about UAlberta clubs..."):
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)

            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                stream = get_club_info(prompt, st.session_state.messages)
                response = st.write_stream(stream)

            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
