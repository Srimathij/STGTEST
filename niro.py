import os
import time
import pandas as pd
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from langchain_community.document_loaders import CSVLoader

# Load environment variables
load_dotenv()

# Load the GROQ and Google API keys
groq_api_key = os.getenv('GROQ_API_KEY')
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# Initialize LLM
llm = ChatGroq(groq_api_key=groq_api_key, model_name="llama3-8b-8192")

# Define the prompt template
prompt_template = ChatPromptTemplate.from_template(
    """
    You are a highly knowledgeable assistant specializing in answering queries based on the data provided from an Excel file. The file contains detailed, structured information relevant to the user’s queries. You must base all your responses strictly on the provided data and context. Decline to answer if the query cannot be answered from the data or context.

    Guidelines:
    1. When responding to questions:
       - Reference specific details directly from the provided Excel data.
       - Ensure that responses are accurate, concise, and directly linked to the context.
       - Avoid assumptions or extrapolations not supported by the data.

    2. If the user asks about:
       - Specific products, include data like names, categories, or features as described in the file.
       - Pricing or availability, verify and provide details only if present in the file.
       - Comparative metrics, explain using clear numbers or trends directly from the data.

    3. If a question lacks sufficient context, politely ask the user for additional details (e.g., product name, category, or data column to reference).

    4. Always maintain professionalism and clarity in responses. Decline to answer queries unrelated to the context or data provided.

    Data context:
    The Excel file contains structured data with columns and rows detailing [general file contents]. Always use the relevant rows and columns to support your answers.

    Example questions and responses:
    Q: "What is the price of Product X?"
    A: "Based on the provided Excel data, the price of Product X is $25. Please let me know if you need additional details like availability or discounts."
    Q: "What is the best-selling product in 2023?"
    A: "According to the data, the best-selling product in 2023 is Product Y with a total sales volume of 15,000 units."
    Q: "Can you recommend a product for outdoor use?"
    A: "Based on the data, the most suitable product for outdoor use is Product Z, as it is specifically designed for external applications."

    <conversation_history>
    {conversation_history}
    </conversation_history>

    <context>
    {context}
    </context>

    Question: {input}
    """
)

# Function to load and process CSV or XLSX files
def load_file(file_path):
    print(f"Loading file: {file_path}")
    if file_path.endswith(".csv"):
        loader = CSVLoader(file_path)
        docs = loader.load()
        return [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs]
    elif file_path.endswith(".xlsx"):
        # For XLSX, we manually parse the Excel file and convert it to a document format
        data = pd.read_excel(file_path)
        docs = [{"page_content": row.to_string(), "metadata": {}} for _, row in data.iterrows()]
        return docs
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or XLSX file.")

# Function to process and embed files
def vector_embedding(file_paths):
    print("Generating vector embeddings...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    all_docs = []
    for file_path in file_paths:
        docs = load_file(file_path)
        all_docs.extend(docs)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    final_documents = text_splitter.split_documents(all_docs)

    vectors = FAISS.from_documents(final_documents, embeddings)
    return vectors, final_documents

# Function to handle user questions
def get_response(question, conversation_history, vectors, llm):
    temperature = 0.7
    document_chain = create_stuff_documents_chain(llm, prompt_template)
    retriever = vectors.as_retriever()
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    start = time.process_time()
    response = retrieval_chain.invoke({
        'input': question,
        'context': " ",
        'conversation_history': conversation_history,
        'temperature': temperature
    })
    response_time = time.process_time() - start
    print(f"Response time: {response_time:.2f} seconds")
    return response

# Main function
def Search_LLM_QA_Main(user_input):
    print("Welcome to the Conversational CSV/XLSX Q&A!")

    # Step 1: Define static file paths
    file_paths = [
        "tiles_data.csv",  # Replace with the actual path to your CSV file
        "tiles_data.xlsx"  # Replace with the actual path to your XLSX file
    ]

    # Step 2: Process files
    vectors, final_documents = vector_embedding(file_paths)
    print("Vector embeddings created successfully.")

    # Step 3: Start interaction loop
    conversation_history = ""
    while True:
        question = user_input.strip()
        if question.lower() == "exit":
            print("Goodbye!")
            break

        response = get_response(question, conversation_history, vectors, llm)
        answer = response.get('answer', "No response available")
        context = response.get('context', [])

        print(f"\nAnswer: {answer}")
        conversation_history += f"User: {question}\nBot: {answer}\n"

        return answer
