import os
import pandas as pd
from dotenv import load_dotenv
from langdetect import detect, DetectorFactory
from groq import Groq
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.vectorstores import Chroma
from langchain import hub
from langchain_core.runnables import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
import requests  # For potential Digi-Key API calls or web scraping
from bs4 import BeautifulSoup  # For web scraping Digi-Key if needed

# Ensure consistent language detection results
DetectorFactory.seed = 0

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize the Groq client
client = Groq(api_key=groq_api_key)


def load_keys_from_excel(file_path):
    """
    Load keys from an Excel file.
    """
    try:
        df = pd.read_excel(file_path)
        return df['Key'].tolist()  # Assuming a column named 'Key'
    except Exception as e:
        print(f"Error loading keys: {e}")
        return []


def detect_language(question):
    """
    Detect the language of a given question.
    """
    try:
        return detect(question)
    except:
        return "en"  # Default to English if detection fails


def search_digikey(key):
    """
    Search for a product on Digi-Key based on a key.
    """
    try:
        # Construct the search URL
        url = f"https://www.digikey.in/en/products?keywords={key}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)

        # Check for successful response
        if response.status_code != 200:
            return f"Error fetching data from Digi-Key: HTTP {response.status_code}"

        # Parse the page content
        soup = BeautifulSoup(response.content, "html.parser")
        # Example extraction logic (modify according to the website's structure)
        product_name = soup.find("h1").text if soup.find("h1") else "Product name not found"
        product_desc = soup.find("meta", {"name": "description"})["content"] if soup.find("meta", {"name": "description"}) else "Description not available"

        return f"Product Name: {product_name}\nDescription: {product_desc}"

    except Exception as e:
        return f"Error during search: {e}"


def fetch_product_details(key):
    """
    Fetch product details for a given key.
    """
    product_info = search_digikey(key)
    if product_info:
        return product_info
    else:
        return "No product found for the given key."


def get_response(question):
    """
    Main function to handle user questions and retrieve product details.
    """
    # Detect the language of the question
    lang = detect_language(question)

    # Select the appropriate prompt template
    template_en = """You are a product search assistant for the Digi-Key website. Your task is to find product details such as the name, description, and specifications based on the key provided by the user. Search for the given key on the Digi-Key website and retrieve accurate product information. If you encounter any issues or cannot find the product, provide a helpful response explaining the situation."""
    template_ar = """أنت مساعد متخصص في البحث عن المنتجات على موقع Digi-Key. تتمثل مهمتك في العثور على تفاصيل المنتجات مثل الاسم والوصف والمواصفات بناءً على المفتاح الذي يوفره المستخدم. ابحث عن المفتاح المقدم على موقع Digi-Key وقدم معلومات دقيقة عن المنتج. إذا واجهت أي مشكلات أو لم تتمكن من العثور على المنتج، قدم إجابة مفيدة توضح الموقف."""

    prompt_text = template_ar if lang == "ar" else template_en

    # Load data from the Digi-Key website
    urls = [
        "https://www.digikey.in/"
    ]
    all_data = []
    for url in urls:
        loader = WebBaseLoader(url)
        data = loader.load()
        all_data.extend(data)

    # Split the data into manageable chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
    all_splits = text_splitter.split_documents(all_data)

    # Embed documents into vector store
    vectorstore = Chroma.from_documents(documents=all_splits, embedding=GPT4AllEmbeddings())

    # Perform similarity search to get relevant documents based on question
    docs = vectorstore.similarity_search(question, k=5)

    # Format content from relevant docs
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    websites_content = format_docs(docs)

    # Set up the retrieval-augmented generation chain
    rag_prompt_llama = hub.pull("rlm/rag-prompt-llama")
    retriever = vectorstore.as_retriever()
    qa_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | rag_prompt_llama
    )

    # Invoke the RAG chain
    answer = qa_chain.invoke(question)

    # Use Groq API to refine and generate the final response
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt_text}],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )

        response = ""
        for chunk in completion:
            response += chunk.choices[0].delta.content or ""

        return response

    except Exception as e:
        return f"An error occurred: {e}"
