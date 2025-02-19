import os
import pandas as pd
from dotenv import load_dotenv
from langdetect import detect, DetectorFactory
# import streamlit as st
from groq import Groq
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.document_loaders import WebBaseLoader                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.vectorstores import Chroma
from langchain import hub
from langchain_core.runnables import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter

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
    template_en = """You are a specialized financial data assistant, designed to provide **accurate**, **precise**, and **up-to-date** information from trusted Saudi sources.

    If the question pertains to topics outside of Saudi financial data, respond with: "I'm trained to provide information exclusively on Saudi financial matters."

    Respond to the following question in a **point-wise format** that highlights key information clearly and succinctly. Avoid lengthy paragraphs. Focus on:
    - **Numerical data**
    - **Market performance**
    - **Trading volume**
    - **Regulatory updates**

    Start with "Pleased to provide the information you’re looking for!" and provide a confident response without recommending any external sources.

    Question: {question}

    Answer:
    """


    template_ar = """أنت مساعد بيانات مالية متخصص، مصمم لتقديم **معلومات دقيقة**، **حديثة** من **مصادر سعودية موثوقة**.

    إذا كان السؤال يتعلق بمواضيع خارج البيانات المالية السعودية، أجب بعبارة: "أنا مدرب على تقديم المعلومات المتعلقة بالمسائل المالية السعودية فقط."

    أجب على السؤال التالي في **تنسيق نقاط مختصرة** يبرز المعلومات الأساسية بوضوح وباختصار. تجنب الفقرات الطويلة. ركز على:
    - **البيانات الرقمية**
    - **أداء السوق**
    - **حجم التداول**
    - **التحديثات التنظيمية**

    ابدأ بعبارة "يسعدني مساعدتك!" وقدم إجابة واثقة دون التوصية بأي مصادر خارجية.

    السؤال: {question}

    الإجابة:
    """



    # Set up callback manager for streaming responses
    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

    # Load data from specified URLs
    urls = [
        "https://www.saudiexchange.sa/wps/portal/saudiexchange?locale=en",
        "https://www.tadawulgroup.sa/wps/portal/tadawulgroup",
        "https://www.tadawulgroup.sa/wps/portal/tadawulgroup/portfolio/edaa"
    ]

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
    if lang == 'ar':
        prompt_text = template_ar.format(question=question)
    else:
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

        # Friendly ending based on language
        response += "\n\nI'm here to help you with any other questions you might have! Feel free to ask. 🌟" if lang != 'ar' else "\n\nيسعدني مساعدتك! 😊"

        return response

    except Exception as e:
        return f"An error occurred: {e}"
