# tools/pinecone.py

import os
import json
import pinecone
import openai

class PineconeManager:
    def __init__(self, index_name="chatbot-library", api_key=None, environment=None):
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment or os.getenv("PINECONE_ENVIRONMENT")
        self.index_name = index_name
        self.file_name = f"{self.index_name}.json"

        # Configure pinecone
        pinecone.init(api_key=self.api_key, environment=self.environment)
        print(pinecone.whoami())
        print(pinecone.list_indexes())

        # Initialize openai embedding
        self.embedding_model = "text-embedding-ada-002"

        # Check if the index exists and create it if it doesn't
        if self.index_name not in pinecone.list_indexes():
            print("NOTE: Creating pinecone index. This will take 30-60 seconds.")
            res = openai.Embedding.create(
                input=["This is sample test that will determine the length"],
                engine=self.embedding_model
            )
            
            embedding_length = len(res['data'][0]['embedding'])
            pinecone.create_index(
                self.index_name,
                dimension=embedding_length,
                metric='cosine',
                metadata_config={'indexed': ['title']})

        # Create the index instance for later operations
        self.index_instance = pinecone.Index(index_name=self.index_name)

        # Try loading the local file with the list of added documents
        try:
            with open(self.file_name, "r") as file:
                self.documents = json.load(file)
        except FileNotFoundError:
            self.documents = []

    def get_document_list(self):
        return self.documents


    def add_document(self, title, text):
        # Get the embedding for the text
        # Split the text by newline
        lines = text.split('\n')
    
        # Insert each section into Pinecone with the appropriate ID and metadata
        sections = []
        section = []
        count = 0
        for line in lines:
            line_word_count = len(line.split())
            if count + line_word_count > 1500:
                # Store entry and start new section
                sections.append('\n'.join(section))
                section = [line]
                count = line_word_count
            else:
                # Add line to current section
                section.append(line)
                count += line_word_count
        # Store last entry
        sections.append('\n'.join(section))

        # Calculate the embeddings
        embeddings = openai.Embedding.create(input=sections, engine=self.embedding_model)

        # Zip up the embeddings and insert
        to_upsert = [(title+'-'+str(i), embeddings['data'][i]['embedding'],
                      {'document':title, 'text':sections[i]}) 
                     for i in range(len(sections)) ]
        self.index_instance.upsert(vectors=to_upsert)

        # Add the document to the local list and save it
        self.documents.append(title)
        self.documents.sort()
        self.save_documents()
        
        # Return the number of sections added
        return len(sections)

    def remove_document(self, title):
        # Loop through sections, deleting while found
        i = 0
        while True:
            id = title+'-'+str(i)
            fetch = self.index_instance.fetch(ids=[id])
            if fetch.vectors:
                self.index_instance.delete(ids=[id])
                i += 1
            else:
                break
        
        # Remove the document from the local list and save it
        self.documents = [doc for doc in self.documents if doc != title]
        self.save_documents()

        # Return the number of sections removed
        return i
        
    def save_documents(self):
        # Save the list of documents to a local file
        with open(self.file_name, "w") as file:
            json.dump(self.documents, file)

    def query_index(self, query_text, top_n=5):
        # Get the embedding for the query text
        vector = openai.Embedding.create(input=[query_text], engine=embed_model)

        # Query the pinecone index
        result = self.index_instance.query(vector['data'][0]['embedding'], top_k=top_n,
                                           include_metadata=True)

        # Return the top n results
        return result
