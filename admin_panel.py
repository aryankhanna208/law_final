import streamlit as st
from docs import save_document, save_documents
from langchain_core.documents import Document
import time
from metadata_generator import meta_data_generator
import os

# Define the admin panel function
def admin_panel():
    st.title("Admin Panel")

    # Existing "Add Data" section
    with st.expander("Add Data"):
        with st.form("add_data_form"):
            document_content = st.text_area("Document Content", height=200)
            st.text("Metadata:")
            law_name = st.text_input("Law Name", placeholder="Enter the full law name here")
            content_description = st.text_input("Content Description", placeholder="Describe the content of the added text")
            category = st.text_input("Category", placeholder="Enter the category of the law here")
            submit_button = st.form_submit_button(label="Submit")

            if submit_button:
                try:
                    add_document(document_content, law_name, content_description, category)
                    st.success("Data added successfully!")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                time.sleep(1)
                st.experimental_rerun()

    # New "Add PDFs" section
    with st.expander("Add PDFs"):
        with st.form("add_pdf_form"):
            pdf_name = st.text_input("PDF Name", placeholder="Enter the name of the PDF here")
            uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
            pdf_submit_button = st.form_submit_button(label="Submit")

            if pdf_submit_button:
                if uploaded_file is not None:
                        # Save the uploaded PDF to the current working directory
                        pdf_path = os.path.join(os.getcwd(), uploaded_file.name)
                        with open(pdf_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        # Generate metadata from the PDF
                        document_list=[]
                        try:
                            document_list = meta_data_generator(pdf_path, pdf_name)
                            st.success(f"Successfully extracted metadata from PDF. Total documents: {len(document_list)}")
                            
                        except Exception as e:
                            st.error(f"Failed to extract metadata from PDF. Error: {e}")

                        # Save documents to MongoDB
                        try:
                            save_documents(document_list)
                            st.success(f"{pdf_name} uploaded and processed successfully!")
                        except Exception as e:
                            st.error(f"Failed to upload data to the database. Error: {e}")
                            
                        # displaying documents
                        for i, doc in enumerate(document_list):
                            st.write(f"**Document {i + 1} Content:** {doc.get('page_content', 'No content available')}")
                            st.write(f"**Metadata:** {doc.get('metadata', 'No metadata available')}")
                    
                        # clean up
                        try:
                            os.remove(pdf_path)
                        except Exception as e:
                            st.error(f"Failed to delete the PDF file. Error: {e}")


                else:
                    st.error("Please upload a PDF file.")

def add_document(page_content, law_name, content_description, category):
    new_doc = Document(
        page_content=page_content,
        metadata={
            "law": law_name,
            "content": content_description + " for the law - " + law_name,
            "category": category
        }
    )
    save_document(new_doc)

# Run the admin panel function
if __name__ == "__main__":
    admin_panel()
