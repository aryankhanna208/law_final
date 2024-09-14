import json
from langchain_core.documents import Document
from data.mm import it_acts_doc
docms=it_acts_doc
def convert(documents, filename):
    json_docs = []
    for doc in documents:
        json_docs.append({
            "page_content": doc.page_content.strip(),
            "metadata": {
                "law": doc.metadata["law"],
                "content": doc.metadata["content"],
                "category": doc.metadata["category"]
            }
        })
    
    with open(filename, 'w') as file:
        json.dump(json_docs, file, indent=4)

convert(docms,"lala1.json")
