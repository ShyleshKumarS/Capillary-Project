import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from langchain.embeddings import HuggingFaceEmbeddings #type: ignore[import]
from langchain.vectorstores import Chroma #type: ignore[import]

def ingestion():

    df = pd.read_csv('puma_sale_products.csv')
    df = df.dropna().drop_duplicates(subset=["Title", "Description", "Product Link"])

    texts = (df['Title'].fillna('') + ". " + df['Description'].fillna('')).tolist()

    metadatas = []
    for _, row in df.iterrows():
        metadata = {
            'Promotion': row['Promotion'] if pd.notna(row['Promotion']) else "",
            'Actual Price': float(str(row.get("Actual Price", "0")).replace("₹", "").replace(",", "").strip() or 0),
            'Discounted Price': float(str(row.get("Discounted Price", "0")).replace("₹", "").replace(",", "").strip() or 0),
            'Category': row['Category'] if pd.notna(row['Category']) else "",
            'Sizes': ', '.join(row['Sizes'].split(',')) if pd.notna(row['Sizes']) else "",
            'Link': row['Product Link'] if pd.notna(row['Product Link']) else ""
        }
        metadatas.append(metadata)

    embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en")
    persist_directory = './chroma_db'


    vectordb = Chroma.from_texts(texts, embedding_model, metadatas=metadatas, persist_directory=persist_directory, collection_name="puma_sale_products")
    vectordb.persist()

    print("Data inserted into Chroma DB")

# query = "PUMA men's running shoes with good discount"
# query_embedding = embedding_model.embed_query(query)


# initial_results = vectordb.similarity_search(query, k=10)


# result_texts = [doc.page_content for doc in initial_results]
# result_embeddings = embedding_model.embed_documents(result_texts)

# cos_sim = cosine_similarity([query_embedding], result_embeddings)[0]

# scored_results = list(zip(initial_results, cos_sim))
# scored_results.sort(key=lambda x: x[1], reverse=True)

# seen_links = set()
# unique_top_k = []
# for doc, score in scored_results:
#     link = doc.metadata.get("Link")
#     if link and link not in seen_links:
#         seen_links.add(link)
#         unique_top_k.append((doc, score))
#     if len(unique_top_k) == 3:
#         break

# for i, (doc, score) in enumerate(unique_top_k, 1):
#     print(f"Result {i} - Score: {score:.4f}")
#     print("Text:", doc.page_content)
#     print("Metadata:", doc.metadata)
#     print("-----")
