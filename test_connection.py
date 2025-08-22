#!/usr/bin/env python3
"""
Test Dify API connection

This script tests the basic connection to Dify API using the configured parameters.
"""

import os
import sys
from dify_knowledge_api import DifyKnowledgeAPI


def test_connection():
    """Test basic connection to Dify API."""
    
    # Get configuration from environment variables
    api_base = os.getenv("DIFY_API_BASE")
    api_key = os.getenv("DIFY_API_KEY")
    dataset_id = os.getenv("DIFY_DATASET_ID")
    
    print("=== Dify API Connection Test ===\n")
    
    # Check required environment variables
    if not api_base:
        print("[ERROR] DIFY_API_BASE environment variable not set")
        print("Please set it in accessapiprivate.ps1 or export it manually")
        return False
    
    if not api_key:
        print("[ERROR] DIFY_API_KEY environment variable not set")
        print("Please set it in accessapiprivate.ps1 or export it manually")
        return False
    
    if not dataset_id:
        print("[ERROR] DIFY_DATASET_ID environment variable not set")
        print("Please set it in accessapiprivate.ps1 or export it manually")
        return False
    
    print(f"API Base: {api_base}")
    print(f"Dataset ID: {dataset_id}")
    print(f"API Key: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else '***'}")
    print()
    
    try:
        # Initialize API client
        print("Initializing API client...")
        client = DifyKnowledgeAPI(api_base=api_base, api_key=api_key)
        print("✓ API client initialized successfully")
        
        # Test dataset access
        print("\nTesting dataset access...")
        ok, dataset = client.datasets.get_dataset(dataset_id)
        if ok and dataset:
            print(f"✓ Dataset access successful")
            print(f"  Name: {dataset.get('name', 'Unknown')}")
            print(f"  Description: {dataset.get('description', 'No description')}")
            print(f"  Document count: {dataset.get('document_count', 0)}")
            print(f"  Word count: {dataset.get('word_count', 0)}")
        else:
            print(f"✗ Dataset access failed: {dataset}")
            return False
        
        # Test document listing
        print("\nTesting document listing...")
        ok, documents = client.documents.list_documents(dataset_id, page=1, limit=5)
        if ok and documents:
            doc_list = documents.get('data', [])
            print(f"✓ Document listing successful")
            print(f"  Found {len(doc_list)} documents")
            if doc_list:
                print("  Sample documents:")
                for i, doc in enumerate(doc_list[:3], 1):
                    print(f"    {i}. {doc.get('name', 'Unknown')} (Status: {doc.get('indexing_status', 'Unknown')})")
        else:
            print(f"✗ Document listing failed: {documents}")
            return False
        
        # Test available models
        print("\nTesting model access...")
        ok, models = client.models.get_available_embedding_models()
        if ok and models:
            model_data = models.get('data', [])
            print(f"✓ Model access successful")
            print(f"  Found {len(model_data)} model providers")
        else:
            print(f"✗ Model access failed: {models}")
            # This is not critical, so we don't return False
        
        print("\n=== Connection Test Completed Successfully ===")
        return True
        
    except Exception as e:
        print(f"\n✗ Connection test failed with exception: {e}")
        return False


def main():
    """Main function."""
    success = test_connection()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
