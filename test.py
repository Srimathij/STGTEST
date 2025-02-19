import os
from dotenv import load_dotenv
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from groq import Groq

# Load environment variables from .env
load_dotenv()

# Define the persistent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.join(current_dir, "db")
persistent_directory = os.path.join(db_dir, "chroma_db_apple")

# Step 1: Scrape the content from the URL using WebBaseLoader
urls = ["https://www.askmh.malaysiaairlines.com/faq/s/"]
loader = WebBaseLoader(urls)
documents = loader.load()

# Step 2: Split the scraped content into chunks
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
docs = text_splitter.split_documents(documents)

# Display information about the split documents
print("\n--- Document Chunks Information ---")
print(f"Number of document chunks: {len(docs)}")
if docs:
    print(f"Sample chunk:\n{docs[0].page_content}\n")

# Step 3: Define an embedding function for Groq
class GroqEmbeddings:
    def __init__(self):
        self.client = Groq()
        self.model = "llama-3.3-70b-versatile"

    def embed_documents(self, documents):
        embeddings = []
        for doc in documents:
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": doc}],
                    temperature=0,
                    max_tokens=512,
                    top_p=1,
                    stop=None,
                )
                embedding = []
                for chunk in completion:
                    print(f"Chunk structure: {chunk}")  # Debugging: Inspect chunk structure
                    if isinstance(chunk, dict) and "choices" in chunk:
                        embedding.append(chunk["choices"][0]["delta"]["content"] or "")
                    else:
                        print("Unhandled response format:", chunk)
                embeddings.append("".join(embedding))
            except Exception as e:
                print(f"Error processing document chunk: {e}")
                embeddings.append([0.0] * 768)  # Fallback to a zero vector
        return embeddings

    def embed_query(self, query):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": query}],
                temperature=0,
                max_tokens=512,
                top_p=1,
                stop=None,
            )
            embedding = []
            for chunk in completion:
                print(f"Chunk structure: {chunk}")  # Debugging: Inspect chunk structure
                if isinstance(chunk, dict) and "choices" in chunk:
                    embedding.append(chunk["choices"][0]["delta"]["content"] or "")
                else:
                    print("Unhandled response format:", chunk)
            return "".join(embedding)
        except Exception as e:
            print(f"Error processing query: {e}")
            return [0.0] * 768  # Fallback to a zero vector for the query

# Instantiate the embedding function
embedding_function = GroqEmbeddings()

# Step 4: Create and persist the vector store
if not os.path.exists(persistent_directory):
    print(f"\n--- Creating vector store in {persistent_directory} ---")
    db = Chroma.from_documents(docs, embedding_function, persist_directory=persistent_directory)
    print(f"--- Finished creating vector store in {persistent_directory} ---")
else:
    print(f"Vector store {persistent_directory} already exists. No need to initialize.")
    db = Chroma(persist_directory=persistent_directory, embedding_function=embedding_function)

# Step 5: Query the vector store
retriever = db.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3},
)

query = "can you tell me about booking?"
relevant_docs = retriever.invoke(query)

# Display the relevant results with metadata
print("\n--- Relevant Documents ---")
for i, doc in enumerate(relevant_docs, 1):
    print(f"Document {i}:\n{doc.page_content}\n")
    if doc.metadata:
        print(f"Source: {doc.metadata.get('source', 'Unknown')}\n")
