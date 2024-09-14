import json
import os
from langchain_core.documents import Document

# MongoDB setup
from dotenv import load_dotenv
load_dotenv()
from pymongo import MongoClient

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client['legal-buddy-documents']
collection = db['legal-buddy-collection']

def load_documents():
    """Load documents from MongoDB."""
    documents = collection.find()
    return [Document(page_content=doc['page_content'], metadata=doc['metadata']) for doc in documents]

def save_document(document):
    """Insert a single document to MongoDB."""
    doc_to_insert = {
        'page_content': document.page_content,
        'metadata': document.metadata
    }
    
    # Insert the document
    collection.insert_one(doc_to_insert)

def save_documents(documents):
    """Insert multiple documents into MongoDB."""
    if not documents:
        print("No documents to insert.")
        return
    
    # Ensure each document is in the form of a dictionary
    docs_to_insert = []
    for doc in documents:
        if isinstance(doc, dict):
            docs_to_insert.append({
                'page_content': doc.get('page_content'),
                'metadata': doc.get('metadata')
            })
        else:
            print(f"Skipping invalid document: {doc}")

    # Insert all documents at once
    if docs_to_insert:
        collection.insert_many(docs_to_insert)
        print(f"{len(docs_to_insert)} documents inserted successfully!")
    else:
        print("No valid documents to insert.")


def save_documents_to_json(documents, json_file_path):
    """Save documents to a JSON file."""
    docs_to_save = [{
        'page_content': doc.page_content,
        'metadata': doc.metadata
    } for doc in documents]
    
    with open(json_file_path, 'w') as json_file:
        json.dump(docs_to_save, json_file, indent=4)

# Sample Usage
if __name__ == "__main__":
    # Load documents
    print("Loading documents...")
    documents = load_documents()
    
    # Save documents to fetch.json
    json_file_path = 'fetch.json'
    save_documents_to_json(documents, json_file_path)
    print(f"Documents saved to {json_file_path}")
    
    # Print loaded documents
    for doc in documents:
        print(f"Page Content: {doc.page_content}")
        print(f"Metadata: {doc.metadata}")
        print("-" * 40)
    
    # Add a new document
    new_doc = Document(
        page_content="Sample page content for the new document",
        metadata={
            "law": "Sample Law",
            "content": "Sample content description for the law - Sample Law",
            "category": "Sample Category"
        }
    )
    
    save_document(new_doc)
    print("New document added successfully!")
    
    # Load documents after insertion to verify
    print("Loading documents after adding new one...")
    documents = load_documents()
    
    # Save updated documents to fetch.json
    save_documents_to_json(documents, json_file_path)
    print(f"Updated documents saved to {json_file_path}")
    
    # Print loaded documents
    for doc in documents:
        print(f"Page Content: {doc.page_content}")
        print(f"Metadata: {doc.metadata}")
        print("-" * 40)
