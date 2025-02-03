import os
import streamlit as st
import sqlite3
from docx import Document
from bs4 import BeautifulSoup
import pypandoc

# Download Pandoc if not already installed
pypandoc.download_pandoc()

# Database setup
db_path = os.path.join(os.getcwd(), "markdown_files.db")
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()

# Create table if it doesn't exist
c.execute('''
    CREATE TABLE IF NOT EXISTS markdown_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        content TEXT
    )
''')
conn.commit()

# Function to save Markdown file to the database
def save_to_database(filename, content):
    c.execute('''
        INSERT INTO markdown_files (filename, content)
        VALUES (?, ?)
    ''', (filename, content))
    conn.commit()

# Function to fetch all Markdown files from the database
def fetch_all_files():
    c.execute('SELECT id, filename FROM markdown_files')
    return c.fetchall()

# Function to fetch content of a specific Markdown file by ID
def fetch_file_content(file_id):
    c.execute('SELECT content FROM markdown_files WHERE id = ?', (file_id,))
    return c.fetchone()[0]

# Function to delete a Markdown file from the database
def delete_file_from_database(file_id):
    c.execute('DELETE FROM markdown_files WHERE id = ?', (file_id,))
    conn.commit()

# Function to convert Markdown to DOCX with proper formatting using Pandoc
def markdown_to_docx(md_content, output_filename):
    try:
        # Convert Markdown to DOCX using Pandoc
        output = pypandoc.convert_text(
            md_content,
            'docx',
            format='markdown+tex_math_dollars'
        )
        with open(output_filename, 'wb') as f:
            f.write(output)
        return True
    except Exception as e:
        st.error(f"Error converting Markdown to DOCX: {e}")
        return False

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Upload Markdown", "View Markdown Files"])

# Upload Markdown Page
if page == "Upload Markdown":
    st.title("Upload Markdown File")
    uploaded_file = st.file_uploader("Upload a Markdown file", type=["md"])
    if uploaded_file is not None:
        md_content = uploaded_file.read().decode("utf-8")
        st.subheader("Uploaded Markdown Content:")
        st.text(md_content)
        if st.button("Save to Database"):
            save_to_database(uploaded_file.name, md_content)
            st.success(f"File '{uploaded_file.name}' saved to database!")

# View Markdown Files Page
elif page == "View Markdown Files":
    st.title("View Saved Markdown Files")
    files = fetch_all_files()
    if files:
        selected_file = st.selectbox("Select a Markdown file to preview", [filename for _, filename in files])
        selected_file_id = next(id for id, filename in files if filename == selected_file)
        selected_file_content = fetch_file_content(selected_file_id)
        st.subheader(f"Preview: {selected_file}")
        st.markdown(selected_file_content, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Delete {selected_file}", key=f"delete_{selected_file_id}"):
                delete_file_from_database(selected_file_id)
                st.experimental_rerun()
        with col2:
            if st.button(f"Download {selected_file} as DOCX", key=f"docx_{selected_file_id}"):
                docx_filename = f"{os.path.splitext(selected_file)[0]}.docx"
                success = markdown_to_docx(selected_file_content, docx_filename)
                if success:
                    with open(docx_filename, "rb") as docx_file:
                        st.download_button(
                            label=f"Download {selected_file} as DOCX",
                            data=docx_file,
                            file_name=docx_filename,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    os.remove(docx_filename)
    else:
        st.info("No Markdown files saved yet.")

# Close the database connection when the app is closed
conn.close()
