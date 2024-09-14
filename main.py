import os

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_groq import ChatGroq
from docs import load_documents
import streamlit as st
from langchain_chroma import Chroma
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from prompts import *

from admin_panel import admin_panel
import pickle
import pathlib as Path
import streamlit_authenticator as stauth

os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["AZURE_OPENAI_ENDPOINT"] = os.getenv("AZURE_OPENAI_ENDPOINT")
groq_api_key = os.getenv('GROQ_API_KEY')

# Initialization function to be called once
available_models = {
    "Llama 3.1": "llama-3.1-8b-instant",
    "Gemma 2": "gemma2-9b-it",
    "Gemma": "gemma-7b-it",
    "Mixtral": "mixtral-8x7b-32768"
}
def init():
    st.session_state.documents = load_documents()
    
    st.session_state.embeddings = AzureOpenAIEmbeddings(
        azure_deployment="lala",
        openai_api_version="2024-03-01-preview",
    )

    st.session_state.metadata_field_info = [
        AttributeInfo(
            name="law",
            description="the Indian Penal Code section that is being discussed in the document",
            type="string",
        ),
        AttributeInfo(
            name="content",
            description="The type of content in the document- [law definition , exception, explanation , state amendments , key points]",
            type="integer",
        ),
        AttributeInfo(
            name="category",
            description="The category of the described crime or law",
            type="string",
        ),
    ]

    st.session_state.document_content_description = "List of Indian laws applicable on sexual offences , theft and extortion"
    
    st.session_state.llm = ChatGroq(groq_api_key=groq_api_key, model_name="gemma2-9b-it", temperature=0)
    
    st.session_state.vectorstore = Chroma.from_documents(st.session_state.documents, st.session_state.embeddings)

    st.session_state.sqretriever = SelfQueryRetriever.from_llm(
        st.session_state.llm,
        st.session_state.vectorstore,
        st.session_state.document_content_description,
        st.session_state.metadata_field_info,
        enable_limit=False,
    )
    st.session_state.initialized = True

if 'initialized' not in st.session_state:
    init()



class Classifier(BaseModel):
    type: str = Field(description="Type of Question Whether case/law_query/normal_query")

def question_classifier(question):
    parser = JsonOutputParser(pydantic_object=Classifier) #json formatter

    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", classifier_prompt),
        ("human", f"""Classify the following question: {question}.|<Don't give any output other than the json>|""")
    ])

    chain = chat_prompt | st.session_state.llm | parser
    response = chain.invoke({"question": question})
    return response['category']


def answer(input):
    try:
        llm = ChatGroq(groq_api_key=groq_api_key, model_name="gemma2-9b-it", temperature=0)

        response = question_classifier(input)
        print(response)
        if(response == 'case'):
            document_chain = create_stuff_documents_chain(llm, case_prompt)
        elif(response == 'law_query'):
            document_chain = create_stuff_documents_chain(llm, law_query_prompt)
        else:
            chat_prompt = ChatPromptTemplate.from_messages([
                ("system", normal_query_prompt),
                ("human", f"""Answer the following : {input}.|<If question is not law related ask, user to ask law related questions>|""")
            ])
            chain = chat_prompt | llm
            response = chain.invoke({"input": input})
            return response.content
        retrieval_chain = create_retrieval_chain(st.session_state.sqretriever, document_chain)
        response = retrieval_chain.invoke({"input": input})
        return response['answer']
    except Exception as e:
        st.error(f"Failed to generate answer. Reason: {e}")
        return "An error occurred while generating the answer."


def main():
    # Page navigation
    if "page" not in st.session_state:
        st.session_state.page = "main"

    if "authentication_status" not in st.session_state:
        st.session_state.authentication_status = None

    if st.session_state.page == "admin":
        admin_panel()
        if st.sidebar.button("Back"):
            st.session_state.page = "main"
            st.rerun()
    elif st.session_state.page == "login":
        login()
    else:
        main_page()
        if st.sidebar.button("Admin"):
            if st.session_state.authentication_status is not True:
                st.session_state.page = "login"
            else:
                st.session_state.page = "admin"
            st.rerun()

def main_page():
    st.title("Legal Buddy")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Enter your question:"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        try:
            response = answer(prompt)
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"An error occurred: {e}")

def login():
    # Authentication
    names = ['admin']
    usernames = ["admin"]

    file_path = Path.Path(__file__).parent / "hashed_pw.pkl"
    with file_path.open("rb") as file:
        hashed_passwords = pickle.load(file)
    authenticator = stauth.Authenticate(names, usernames, hashed_passwords, "user_data", "abcdef", cookie_expiry_days=15)

    name, authentication_status, username = authenticator.login("Login", "main")

    if authentication_status == False:
        st.error("Username or Password is incorrect")
    if authentication_status == None:
        st.warning("Please enter your username and password")
    if authentication_status:
        st.session_state.authentication_status = True
        st.session_state.page = "admin"
        st.rerun()


if __name__ == "__main__":
    main()