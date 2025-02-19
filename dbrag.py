import os
import subprocess
import psycopg2
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from some_module import hub, vectorstore, RunnablePassthrough  # Assuming `hub` is defined in your environment

app = Flask(__name__)

# Load environment variables (for database connection)
load_dotenv()

# Fetch relevant data from the database based on the user query
def fetch_relevant_data(user_query):
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS")
        )
        cur = conn.cursor()

        # Adjust query to filter results based on user input
        query = '''
            SELECT "Transaction Date", "Portfolio Code", "Portfolio Name", "Family Name", "Folio No", "RTA Scheme Code", "Scheme Name", "Units", "Transaction Type", "Transaction Amount", "Cost / Price per Unit", "Load", "STT", "Stamp Duty", "Product", "RM Name",
                    "As On Date", "Portfolio Code1", "Portfolio Name1", "AMFI Code", "Folio No1", "Units1", "Purchase Value", "Market Value", "Unrealized Gain/Loss Amount", "Xirr", "Asset Class", "RM Name1"
            FROM "Transactions_Holding";
        '''

        cur.execute(query)
        result = cur.fetchall()

        print("Result:------->", result)

        cur.close()
        conn.close()

        return result
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

# Function to chunk large text if needed
def chunk_large_text(text, chunk_size=3000):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

# Function to create a structured prompt template
def create_prompt_template(user_query, data_chunk):
    return f"""**You are BULLFINCH.AI**, a data assistant specialized in responding to queries about financial transactions and holdings data from the `Transactions_Holding` PostgreSQL database table. Your role is to provide precise, accurate, and concise answers (within **400 characters**) in a casual, **conversational format**.

    Table Fields:
            "Transaction Date", "Portfolio Code", "Portfolio Name", "Family Name", "Folio No", "RTA Scheme Code", "Scheme Name", "Units", "Transaction Type", "Transaction Amount", "Cost / Price per Unit", "Load", "STT", "Stamp Duty", "Product", "RM Name",
            "As On Date", "Portfolio Code1", "Portfolio Name1", "AMFI Code", "Folio No1", "Units1", "Purchase Value", "Market Value", "Unrealized Gain/Loss Amount", "Xirr", "Asset Class", "RM Name1"

### **Guidelines**:
1. **Language**: Respond in plain English. Avoid using any technical jargon unless explicitly asked.
2. **Scope**: Respond only to queries related to the `Transactions_Holding` table, covering fields such as transactions, portfolio details, and investment data.
Content:
{data_chunk}

Question: {user_query}
Respond:
    """

# Function to call RAG model and get the response
def generate_rag_response(user_query):
    try:
        # Fetch relevant data based on the user query
        relevant_data = fetch_relevant_data(user_query)
        if not relevant_data:
            return "The requested information is not available in the current data."

        # Combine database data into a readable format for the prompt
        data_string = '\n'.join([
            f"Transaction Date: {row[0]}, Portfolio Code: {row[1]}, Portfolio Name: {row[2]}, Family Name: {row[3]}, "
            f"Folio No: {row[4]}, RTA Scheme Code: {row[5]}, Scheme Name: {row[6]}, Units: {row[7]}, "
            f"Transaction Type: {row[8]}, Transaction Amount: {row[9]}, Cost / Price per Unit: {row[10]}, "
            f"Load: {row[11]}, STT: {row[12]}, Stamp Duty: {row[13]}, Product: {row[14]}, RM Name: {row[15]}, "
            f"As On Date: {row[16]}, Portfolio Code1: {row[17]}, Portfolio Name1: {row[18]}, AMFI Code: {row[19]}, "
            f"Folio No1: {row[20]}, Units1: {row[21]}, Purchase Value: {row[22]}, Market Value: {row[23]}, "
            f"Unrealized Gain/Loss Amount: {row[24]}, Xirr: {row[25]}, Asset Class: {row[26]}, RM Name1: {row[27]}"
            for row in relevant_data
        ])

        # Break data into chunks if it exceeds the model input limit
        all_chunks = chunk_large_text(data_string, chunk_size=3000)

        # Initialize the overall chunks
        overall_chunks = []

        # Append a maximum of 20 chunks
        for i, chunk in enumerate(all_chunks):
            if i < 1:
                overall_chunks.append(chunk)
            else:
                break

        full_chunk = "\n".join(overall_chunks)

        # Using the RAG model pipeline for retrieval and response generation
        rag_prompt_llama = hub.pull("rlm/rag-prompt-llama")
        retriever = vectorstore.as_retriever()
        qa_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | rag_prompt_llama
        )

        # Run the RAG model to generate the final response
        rag_response = qa_chain.invoke({"question": user_query, "context": full_chunk})

        return rag_response.strip() if rag_response.strip() else "No relevant response generated."

    except Exception as e:
        print(f"Unexpected error generating response: {e}")
        return "An unexpected error occurred."

@app.route('/document_qna', methods=["GET", 'POST'])
def handle_query():
    data = request.get_json()
    print(data)
    user_query = data.get("user_query", "")
    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    # Use the RAG response generation method instead
    response = generate_rag_response(user_query)
    print(response)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(port=5003)
