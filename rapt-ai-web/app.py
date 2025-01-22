import streamlit as st

pages = {
    "Process": [
        st.Page("process.py", title="Upload Documents"),

    ],
    "Chat": [
        st.Page("chat.py", title="Chat Bot"),
    ],
}

pg = st.navigation(pages)
pg.run()
