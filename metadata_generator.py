import PyPDF2
from langchain_core.pydantic_v1 import BaseModel, Field
import os
from langchain.prompts.chat import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from prompts import *
groq_api_key=os.getenv('GROQ_API_KEY')

class MetaData(BaseModel):
    law: str = Field(description="The specific law related to the paragraph content")
    content: str = Field(description="A brief summary of the paragraph content")
    category: str = Field(description="The category of law to which the paragraph content belongs")


def meta_data_formation(page_content, pdf_name):
    llm = ChatGroq(groq_api_key=groq_api_key, model_name="llama3-8b-8192", temperature=0)
    parser = JsonOutputParser(pydantic_object=MetaData)  # JSON formatter

    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", Meta_Data_Prompt),
        ("human", f"""Provide metadata for the following paragraph: "{page_content}" from the PDF titled "{pdf_name}".|<Only return the JSON output>|""")
    ])

    chain = chat_prompt | llm | parser
    response = chain.invoke({"page_content": page_content})
    return response



def extract_paragraphs_from_pdf(pdf_path):
    paragraphs = []
    
    # Open the PDF file in binary read mode
    with open(pdf_path, "rb") as file:
        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(file)
        
        # Iterate through all the pages and extract text
        for page in pdf_reader.pages:
            text = page.extract_text()
            
            if text:
                # Split text into paragraphs based on newline characters
                page_paragraphs = text.split('\n\n')  # Assuming paragraphs are separated by two newlines
                paragraphs.extend(page_paragraphs)
    
    # Clean up the paragraphs
    cleaned_paragraphs = [p.strip() for p in paragraphs if p.strip()]

    return cleaned_paragraphs

def format_paragraphs_to_metadata(paragraphs, pdf_name):
    json_list = []

    for i, paragraph in enumerate(paragraphs):
        # Get metadata from the meta_data_formation function
        tries=3
        metadata={"law":"","content":"","category":""}
        while(tries>0):
            try:
                metadata = meta_data_formation(paragraph, pdf_name)
                break
            except Exception as e:
                print("Error occured in generating metadata , llm hallucinated , error: ",e)
                tries-=1
        # Format the metadata into the desired JSON structure
        formatted_json = {
            "page_content": paragraph,
            "metadata": {
                "law": metadata['metadata'].get('law', 'Reformation'),
                "content": metadata['metadata'].get('content', ''),
                "category": metadata['metadata'].get('category', 'Reformation')
            }
        }
        
        # Add the formatted JSON to the list
        json_list.append(formatted_json)
    
    return json_list

import json

def meta_data_generator(pdf_path, pdf_name):
    paragraphs = extract_paragraphs_from_pdf(pdf_path) #will return paragraph list
    document_list = format_paragraphs_to_metadata(paragraphs, pdf_name)
    # with open("metadata.json", "w") as json_file:
    #     json.dump(document_list, json_file, indent=4)
    return document_list

if(__name__=="__main__"):
    import json
    doc_json=meta_data_generator("data\Digital Personal Data Protection Act 2023.pdf","Digital Personal Data Protection Act 2023")
    output_file_path = "metadata.json"
    with open(output_file_path, "w") as json_file:
        json.dump(doc_json, json_file, indent=4)
