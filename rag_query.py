from langchain.vectorstores import Chroma # type: ignore[import]
from langchain.embeddings import HuggingFaceEmbeddings # type: ignore[import]
from sklearn.metrics.pairwise import cosine_similarity
from langchain.llms import HuggingFaceHub # type: ignore[import]
from dotenv import load_dotenv # type: ignore[import]
from mistralai import Mistral # type: ignore[import]
import os

load_dotenv()
api_key = os.environ["MISTRAL_API_KEY"]

def search_products(query: str, top_k: int = 3):
    embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en")
    vectordb = Chroma(
        embedding_function=embedding_model,
        persist_directory="./chroma_db",
        collection_name="puma_sale_products" #Change this collection name after refreshing the data
    )

    query_embedding = embedding_model.embed_query(query)
    initial_results = vectordb.similarity_search(query, k=10)

    result_texts = [doc.page_content for doc in initial_results]
    result_embeddings = embedding_model.embed_documents(result_texts)
    cos_sim = cosine_similarity([query_embedding], result_embeddings)[0]

    scored_results = list(zip(initial_results, cos_sim))
    scored_results.sort(key=lambda x: x[1], reverse=True)

    seen_links = set()
    unique_top_k = []
    for doc, score in scored_results:
        link = doc.metadata.get("Link")
        if link and link not in seen_links:
            seen_links.add(link)
            unique_top_k.append((doc, score))
        if len(unique_top_k) == top_k:
            break

    return [
        {
            "text": doc.page_content,
            "metadata": doc.metadata,
            "score": float(score)
        }
        for doc, score in unique_top_k
    ]


def build_prompt(command_type: str, query: str, context: str) -> str:
    base_intro = f"User query: '{query}'\n\nYou are PromoSensei, an intelligent shopping assistant that helps users find the best Puma product deals.\n\n"
    product_section = (
        "Below are details of three matched products from the Puma deals database:\n\n"
        f"{context}\n\n"
    )
    
    common_table_task = (
        "1. Present a comparison of these products in a **Markdown table** with the following columns:\n"
        "   - Title\n"
        "   - Description(Overview)\n"
        "   - Promotion\n"
        "   - Category\n"
        "   - Sizes Available\n"
        "   - Actual Price\n"
        "   - Discounted Price\n"
        "   - Discount Percentage\n"
        "   - Product Link\n\n"
    )

    recommendation_task = (
        "2. Recommend the **best product** based on relevance to the query, value for money, and features.\n"
        "3. Justify the recommendation in bullet points.\n"
    )

    summary_task = (
        "Provide a **brief summary** of the top Puma deals currently available. Mention any ongoing promotions, best discount rates, and popular product categories.\n"
        "You do **not** need to include a comparison table or recommendation in this case.\n"
    )

    if command_type == "search":
        return (
            base_intro +
            product_section +
            common_table_task +
            recommendation_task
        )

    elif command_type == "summary":
        return base_intro + summary_task

    else:
        return (
            base_intro +
            product_section +
            common_table_task +
            recommendation_task
        )

    
def llm_response(command_type: str,query: str, top_k: int = 3):
    results = search_products(query, top_k)
    context = "\n\n".join(
    f"""{i+1}. {r['text']}
    Promotion: {r['metadata'].get('Promotion')}
    Category: {r['metadata'].get('Category')}
    Sizes: {r['metadata'].get('Sizes')}
    Actual Price: ₹{r['metadata'].get('Actual Price')}
    Discounted Price: ₹{r['metadata'].get('Discounted Price')}
    Link: {r['metadata'].get('Link')}"""
    for i, r in enumerate(results)
    )

    
    prompt = build_prompt(command_type, query, context)


    llm = Mistral(api_key=api_key)
    llm_response = llm.chat.complete(
        model="mistral-large-latest",
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ]
    )
    return {
        "Query": query,
        "Response": llm_response.choices[0].message.content
    }

# if __name__ == "__main__":
#     command_type = str(input("Enter command type (search/summary): "))
#     query = str(input("Enter your query: "))
#     llm_response_result = llm_response(command_type,query)
#     print("LLM Response: ", llm_response_result["Response"])
    

    

