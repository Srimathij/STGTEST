import os
import streamlit as st
from dotenv import load_dotenv
from langdetect import detect, DetectorFactory
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.vectorstores import Chroma
from langchain import hub
from langchain_core.runnables import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
from groq import Groq

# Ensure consistent language detection results
DetectorFactory.seed = 0

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize the Groq client
client = Groq(api_key=groq_api_key)

def get_response(question):
    # Detect the language of the question
    lang = detect(question)

    # Set the prompt template with clear references to all three source URLs
    template_en = """
    You are a dedicated aviation data assistant specializing in delivering accurate, concise, and up-to-date information exclusively based on Malaysia Aviation Group's (MAG) official resources.

    Guidelines for Responses:
    1. Format: Always structure your answers in a point-wise format with bullet points for clarity and ease of reading.

    2. Focus Areas: Center your responses on:
    - Group Overview: Key subsidiaries (Malaysia Airlines, Firefly, MASkargo) and their unique offerings.
    - Services: Passenger travel, cargo logistics, and regional connectivity highlights.
    - Sustainability: Environmental initiatives, community engagement, and operational efficiency.
    - Market Position: Competitive advantages, global partnerships, and industry contributions.
    - Regulatory Updates: Key compliance or policy changes impacting aviation operations.

    3. Content Restrictions: Ensure all information is:
    - Directly relevant to Malaysia Aviation Group and its subsidiaries.
    - Based on verified, official, and current sources.
    - Free from references to unrelated aviation companies, speculative content, or personal opinions.

    4. Boundary Conditions:
    - For unrelated queries (not about Malaysia Aviation Group or its subsidiaries), respond with:
        "I am designed to provide information solely about Malaysia Aviation Group and its associated subsidiaries."
    - Avoid excessive details and keep responses succinct while maintaining value.

    Example Input & Output:
    Question: What are the sustainability initiatives of Malaysia Aviation Group?
    Answer:
    - Commitment to carbon-neutral growth by 2050.
    - Implementation of sustainable aviation fuel (SAF) programs.
    - Focus on operational efficiency to reduce emissions.
    - Community engagement through outreach and support programs.

    Example Question: {question}

    Answer:
    """


    # Set up callback manager for streaming responses
    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

    # Load data from specified URLs
    urls = ["https://malaysiaaviationgroup.com.my/en/home.html"]

    # Collect and split documents for better context retrieval
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

    # Helper function to format document content for model input
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Format content from relevant docs
    websites_content = format_docs(docs)

    # Choose prompt template based on detected language
    prompt_text = template_en.format(question=question)

    # Call the RAG model with an LLM fine-tuned for retrieval accuracy
    rag_prompt_llama = hub.pull("rlm/rag-prompt-llama")
    retriever = vectorstore.as_retriever()
    qa_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | rag_prompt_llama
    )

    # Invoke the RAG chain
    answer = qa_chain.invoke(question)

    # Groq API to post-process and improve the answer quality
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

        # Capture streamed response
        response = ""
        for chunk in completion:
            response += chunk.choices[0].delta.content or ""

        return response

    except Exception as e:
        return f"An error occurred: {e}"

# Initialize session state for Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello and welcome! 🎉 You're in the right place to explore the Mirae asset mutual fund. Just ask your question and let’s dive into the details!"}
    ]

# Chat input field at the top
user_input = st.chat_input("𝖠𝗌𝗄 𝖺𝗇𝗒𝗍𝗁𝗂𝗇𝗀 𝖺𝖻𝗈𝗎𝗍 𝖬𝗂𝗋𝖺𝖾 𝖠𝗌𝗌𝖾𝗍....!💸")

# Streamlit title
st.header("𝖬𝖨𝖱𝖠𝖤 𝖠𝖲𝖲𝖤𝖳")

# Process user input
if user_input:
    # Add the user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get RAG + Groq response
    response = get_response(user_input)
    
    # Add the assistant response to the chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Display the full chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
