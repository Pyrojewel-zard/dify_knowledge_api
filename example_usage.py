#!/usr/bin/env python3
"""
Example usage of DifyKnowledgeAPI classes

This file demonstrates how to use the various managers for different operations.
"""

import os
from dify_knowledge_api import DifyKnowledgeAPI


def main():
    # Initialize the API client
            api_base = os.getenv("DIFY_API_BASE", "https://your-dify-instance.com/v1")
    api_key = os.getenv("DIFY_API_KEY")
    dataset_id = os.getenv("DIFY_DATASET_ID")
    
    if not api_key:
        print("Please set DIFY_API_KEY environment variable")
        return
    
    if not dataset_id:
        print("Please set DIFY_DATASET_ID environment variable")
        return
    
    # Create API client
    client = DifyKnowledgeAPI(api_base=api_base, api_key=api_key)
    
    print("=== Dify Knowledge Base API Example ===\n")
    
    # 1. Dataset Management Examples
    print("1. Dataset Management:")
    print("-" * 30)
    
    # List datasets
    ok, datasets = client.datasets.list_datasets(page=1, limit=5)
    if ok and datasets:
        print(f"Found {len(datasets.get('data', []))} datasets")
        for dataset in datasets.get('data', [])[:3]:  # Show first 3
            print(f"  - {dataset.get('name', 'Unknown')} (ID: {dataset.get('id', 'Unknown')})")
    else:
        print("Failed to list datasets or no datasets found")
    
    # Get specific dataset
    ok, dataset = client.datasets.get_dataset(dataset_id)
    if ok and dataset:
        print(f"Current dataset: {dataset.get('name', 'Unknown')}")
        print(f"  Description: {dataset.get('description', 'No description')}")
        print(f"  Document count: {dataset.get('document_count', 0)}")
        print(f"  Word count: {dataset.get('word_count', 0)}")
    else:
        print("Failed to get dataset details")
    
    print()
    
    # 2. Document Management Examples
    print("2. Document Management:")
    print("-" * 30)
    
    # List documents in the dataset
    ok, documents = client.documents.list_documents(dataset_id, page=1, limit=5)
    if ok and documents:
        doc_list = documents.get('data', [])
        print(f"Found {len(doc_list)} documents in dataset")
        for doc in doc_list[:3]:  # Show first 3
            print(f"  - {doc.get('name', 'Unknown')} (Status: {doc.get('indexing_status', 'Unknown')})")
    else:
        print("Failed to list documents or no documents found")
    
    print()
    
    # 3. Model Management Examples
    print("3. Model Management:")
    print("-" * 30)
    
    # Get available embedding models
    ok, models = client.models.get_available_embedding_models()
    if ok and models:
        model_data = models.get('data', [])
        print(f"Found {len(model_data)} model providers")
        for provider in model_data[:2]:  # Show first 2 providers
            provider_name = provider.get('provider', 'Unknown')
            model_count = len(provider.get('models', []))
            print(f"  - {provider_name}: {model_count} models available")
    else:
        print("Failed to get available models")
    
    print()
    
    # 4. Metadata and Tags Examples
    print("4. Metadata and Tags:")
    print("-" * 30)
    
    # List available tags
    ok, tags = client.metadata.list_tags()
    if ok and tags:
        print(f"Found {len(tags)} available tags")
        for tag in tags[:3]:  # Show first 3 tags
            print(f"  - {tag.get('name', 'Unknown')} (ID: {tag.get('id', 'Unknown')})")
    else:
        print("Failed to list tags or no tags found")
    
    # Get tags bound to current dataset
    ok, dataset_tags = client.metadata.get_dataset_tags(dataset_id)
    if ok and dataset_tags:
        tag_data = dataset_tags.get('data', [])
        print(f"Dataset has {len(tag_data)} bound tags")
        for tag in tag_data:
            print(f"  - {tag.get('name', 'Unknown')}")
    else:
        print("Failed to get dataset tags or no tags bound")
    
    print()
    
    # 5. Search Example
    print("5. Knowledge Base Search:")
    print("-" * 30)
    
    # Search the knowledge base
    query = "example search query"
    ok, search_results = client.search_knowledge_base(dataset_id, query, top_k=3)
    if ok and search_results:
        records = search_results.get('records', [])
        print(f"Search query: '{query}'")
        print(f"Found {len(records)} relevant segments")
        for i, record in enumerate(records[:2], 1):  # Show first 2 results
            segment = record.get('segment', {})
            score = record.get('score', 0)
            content = segment.get('content', 'No content')[:100] + "..." if len(segment.get('content', '')) > 100 else segment.get('content', 'No content')
            print(f"  {i}. Score: {score:.3f}")
            print(f"     Content: {content}")
    else:
        print("Search failed or no results found")
    
    print("\n=== Example completed ===")


if __name__ == "__main__":
    main()
