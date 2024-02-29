import csv
import PyPDF2  # Import PyPDF2 for PDF processing

from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores.chroma import Chroma
import shutil
import nltk
from dotenv import load_dotenv
import os

import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt')

CHROMA_PATH = "chroma"
DATA_PATH = "data/books"
load_dotenv()


def main():
    generate_data_store()


def generate_data_store():
    documents = load_documents()
    chunks = split_text(documents)
    save_to_chroma(chunks)


def load_documents():
    loaders = [
        DirectoryLoader(DATA_PATH, glob="*.md"),
        DirectoryLoader(DATA_PATH, glob="*.csv"),  # Load CSV files
        DirectoryLoader(DATA_PATH, glob="*.pdf"),  # Load PDF files
    ]

    documents = []
    for loader in loaders:
        documents.extend(loader.load())

    return documents


def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # Handle PDF files specifically
    for doc in documents:
        if doc.metadata.get("extension") == ".pdf":
            with open(doc.metadata["file_path"], "rb") as pdf_file:  # Open in binary mode
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    text += page_text

                doc.page_content = text  # Update page_content with extracted text

    return chunks


def save_to_chroma(chunks: list[Document]):
    # Clear out the database first.
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
    # Create a new DB from the documents.
    db = Chroma.from_documents(
        chunks, OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key="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"
        ),
        persist_directory=CHROMA_PATH
    )
    db.persist()
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")


if __name__ == "__main__":
    main()
