"""
Dify Knowledge Base API Client Classes

This module provides classes for managing different aspects of Dify knowledge bases:
- DatasetManager: Manage datasets (knowledge bases)
- DocumentManager: Handle document operations
- SegmentManager: Manage document segments/chunks
- ModelManager: Handle embedding and retrieval models
- MetadataManager: Manage metadata and tags
"""

import json
import mimetypes
import os
from typing import Dict, List, Optional, Set, Tuple, Any
import requests


class DifyAPIError(Exception):
    """Custom exception for Dify API errors."""
    pass


class BaseAPIClient:
    """Base class for Dify API clients."""
    
    def __init__(self, api_base: str, api_key: str, timeout_seconds: int = 120):
        self.api_base = api_base.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout_seconds
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None, 
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """Make HTTP request to Dify API."""
        url = f"{self.api_base}{endpoint}"
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, params=params, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=request_headers, json=data, files=files, timeout=self.timeout)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=request_headers, json=data, timeout=self.timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=request_headers, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if 200 <= response.status_code < 300:
                try:
                    return True, response.json() if response.content else None
                except ValueError:
                    return True, None
            else:
                try:
                    return False, response.json()
                except ValueError:
                    return False, {"status_code": response.status_code, "text": response.text}
                    
        except requests.RequestException as e:
            return False, {"error": str(e)}


class DatasetManager(BaseAPIClient):
    """Manage datasets (knowledge bases)."""
    
    def create_dataset(
        self, 
        name: str, 
        description: Optional[str] = None,
        indexing_technique: str = "high_quality",
        permission: str = "only_me",
        provider: str = "vendor",
        embedding_model: Optional[str] = None,
        embedding_model_provider: Optional[str] = None,
        retrieval_model: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """Create a new dataset."""
        data = {
            "name": name,
            "indexing_technique": indexing_technique,
            "permission": permission,
            "provider": provider
        }
        
        if description:
            data["description"] = description
        if embedding_model:
            data["embedding_model"] = embedding_model
        if embedding_model_provider:
            data["embedding_model_provider"] = embedding_model_provider
        if retrieval_model:
            data["retrieval_model"] = retrieval_model
            
        return self._make_request("POST", "/datasets", data=data)
    
    def list_datasets(
        self, 
        keyword: Optional[str] = None,
        tag_ids: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 20,
        include_all: bool = False
    ) -> Tuple[bool, Optional[Dict]]:
        """List datasets with optional filtering."""
        params = {
            "page": page,
            "limit": limit,
            "include_all": include_all
        }
        
        if keyword:
            params["keyword"] = keyword
        if tag_ids:
            params["tag_ids"] = tag_ids
            
        return self._make_request("GET", "/datasets", params=params)
    
    def get_dataset(self, dataset_id: str) -> Tuple[bool, Optional[Dict]]:
        """Get dataset details."""
        return self._make_request("GET", f"/datasets/{dataset_id}")
    
    def update_dataset(
        self, 
        dataset_id: str, 
        name: Optional[str] = None,
        description: Optional[str] = None,
        indexing_technique: Optional[str] = None,
        permission: Optional[str] = None,
        embedding_model: Optional[str] = None,
        embedding_model_provider: Optional[str] = None,
        retrieval_model: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """Update dataset."""
        data = {}
        
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if indexing_technique is not None:
            data["indexing_technique"] = indexing_technique
        if permission is not None:
            data["permission"] = permission
        if embedding_model is not None:
            data["embedding_model"] = embedding_model
        if embedding_model_provider is not None:
            data["embedding_model_provider"] = embedding_model_provider
        if retrieval_model is not None:
            data["retrieval_model"] = retrieval_model
            
        return self._make_request("PATCH", f"/datasets/{dataset_id}", data=data)
    
    def delete_dataset(self, dataset_id: str) -> Tuple[bool, Optional[Dict]]:
        """Delete dataset."""
        return self._make_request("DELETE", f"/datasets/{dataset_id}")
    
    def retrieve_segments(
        self, 
        dataset_id: str, 
        query: str,
        retrieval_model: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """Retrieve segments from dataset."""
        data = {"query": query}
        if retrieval_model:
            data["retrieval_model"] = retrieval_model
            
        return self._make_request("POST", f"/datasets/{dataset_id}/retrieve", data=data)


class DocumentManager(BaseAPIClient):
    """Manage documents within datasets."""
    
    def create_document_from_text(
        self,
        dataset_id: str,
        name: str,
        text: str,
        indexing_technique: str = "high_quality",
        doc_form: str = "text_model",
        doc_language: Optional[str] = None,
        process_rule: Optional[Dict] = None,
        retrieval_model: Optional[Dict] = None,
        embedding_model: Optional[str] = None,
        embedding_model_provider: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """Create document from text content."""
        data = {
            "name": name,
            "text": text,
            "indexing_technique": indexing_technique,
            "doc_form": doc_form
        }
        
        if doc_language:
            data["doc_language"] = doc_language
        if process_rule:
            data["process_rule"] = process_rule
        if retrieval_model:
            data["retrieval_model"] = retrieval_model
        if embedding_model:
            data["embedding_model"] = embedding_model
        if embedding_model_provider:
            data["embedding_model_provider"] = embedding_model_provider
            
        return self._make_request("POST", f"/datasets/{dataset_id}/document/create-by-text", data=data)
    
    def create_document_from_file(
        self,
        dataset_id: str,
        file_path: str,
        indexing_technique: str = "high_quality",
        doc_form: str = "text_model",
        doc_language: Optional[str] = None,
        process_rule: Optional[Dict] = None,
        retrieval_model: Optional[Dict] = None,
        embedding_model: Optional[str] = None,
        embedding_model_provider: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """Create document from file upload."""
        if not os.path.exists(file_path):
            return False, {"error": f"File not found: {file_path}"}
        
        # Prepare form data
        form_data = {
            "indexing_technique": indexing_technique,
            "doc_form": doc_form
        }
        
        if doc_language:
            form_data["doc_language"] = doc_language
        if process_rule:
            form_data["process_rule"] = process_rule
        if retrieval_model:
            form_data["retrieval_model"] = retrieval_model
        if embedding_model:
            form_data["embedding_model"] = embedding_model
        if embedding_model_provider:
            form_data["embedding_model_provider"] = embedding_model_provider
        
        # Convert to JSON string for multipart form
        data_part = json.dumps(form_data, ensure_ascii=False)
        
        # Prepare file upload
        guessed_mime, _ = mimetypes.guess_type(file_path)
        file_mime_type = guessed_mime or "application/octet-stream"
        
        with open(file_path, "rb") as file_handle:
            files = {
                "file": (os.path.basename(file_path), file_handle, file_mime_type)
            }
            form_fields = {"data": data_part}
            
            # Override headers for multipart form
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            return self._make_request(
                "POST", 
                f"/datasets/{dataset_id}/document/create-by-file",
                data=form_fields,
                files=files,
                headers=headers
            )
    
    def update_document_by_text(
        self,
        dataset_id: str,
        document_id: str,
        name: Optional[str] = None,
        text: Optional[str] = None,
        process_rule: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """Update document with text content."""
        data = {}
        
        if name is not None:
            data["name"] = name
        if text is not None:
            data["text"] = text
        if process_rule is not None:
            data["process_rule"] = process_rule
            
        return self._make_request("POST", f"/datasets/{dataset_id}/documents/{document_id}/update-by-text", data=data)
    
    def update_document_by_file(
        self,
        dataset_id: str,
        document_id: str,
        file_path: str,
        name: Optional[str] = None,
        process_rule: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """Update document with new file."""
        if not os.path.exists(file_path):
            return False, {"error": f"File not found: {file_path}"}
        
        # Prepare form data
        form_data = {}
        
        if name is not None:
            form_data["name"] = name
        if process_rule is not None:
            form_data["process_rule"] = process_rule
        
        # Convert to JSON string for multipart form
        data_part = json.dumps(form_data, ensure_ascii=False)
        
        # Prepare file upload
        guessed_mime, _ = mimetypes.guess_type(file_path)
        file_mime_type = guessed_mime or "application/octet-stream"
        
        with open(file_path, "rb") as file_handle:
            files = {
                "file": (os.path.basename(file_path), file_handle, file_mime_type)
            }
            form_fields = {"data": data_part}
            
            # Override headers for multipart form
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            return self._make_request(
                "POST", 
                f"/datasets/{dataset_id}/documents/{document_id}/update-by-file",
                data=form_fields,
                files=files,
                headers=headers
            )
    
    def get_document(self, dataset_id: str, document_id: str, metadata: str = "all") -> Tuple[bool, Optional[Dict]]:
        """Get document details."""
        params = {"metadata": metadata}
        return self._make_request("GET", f"/datasets/{dataset_id}/documents/{document_id}", params=params)
    
    def list_documents(
        self, 
        dataset_id: str, 
        keyword: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[bool, Optional[Dict]]:
        """List documents in dataset."""
        params = {"page": page, "limit": limit}
        if keyword:
            params["keyword"] = keyword
            
        return self._make_request("GET", f"/datasets/{dataset_id}/documents", params=params)
    
    def delete_document(self, dataset_id: str, document_id: str) -> Tuple[bool, Optional[Dict]]:
        """Delete document."""
        return self._make_request("DELETE", f"/datasets/{dataset_id}/documents/{document_id}")
    
    def get_indexing_status(self, dataset_id: str, batch_id: str) -> Tuple[bool, Optional[Dict]]:
        """Get document indexing status."""
        return self._make_request("GET", f"/datasets/{dataset_id}/documents/{batch_id}/indexing-status")
    
    def batch_update_document_status(
        self, 
        dataset_id: str, 
        action: str, 
        document_ids: List[str]
    ) -> Tuple[bool, Optional[Dict]]:
        """Batch update document status (enable, disable, archive, un_archive)."""
        data = {"document_ids": document_ids}
        return self._make_request("PATCH", f"/datasets/{dataset_id}/documents/status/{action}", data=data)
    
    def get_upload_file(self, dataset_id: str, document_id: str) -> Tuple[bool, Optional[Dict]]:
        """Get uploaded file information."""
        return self._make_request("GET", f"/datasets/{dataset_id}/documents/{document_id}/upload-file")


class SegmentManager(BaseAPIClient):
    """Manage document segments/chunks."""
    
    def create_segments(
        self,
        dataset_id: str,
        document_id: str,
        segments: List[Dict]
    ) -> Tuple[bool, Optional[Dict]]:
        """Create segments for a document."""
        data = {"segments": segments}
        return self._make_request("POST", f"/datasets/{dataset_id}/documents/{document_id}/segments", data=data)
    
    def list_segments(
        self,
        dataset_id: str,
        document_id: str,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[bool, Optional[Dict]]:
        """List segments in a document."""
        params = {"page": page, "limit": limit}
        if keyword:
            params["keyword"] = keyword
        if status:
            params["status"] = status
            
        return self._make_request("GET", f"/datasets/{dataset_id}/documents/{document_id}/segments", params=params)
    
    def get_segment(self, dataset_id: str, document_id: str, segment_id: str) -> Tuple[bool, Optional[Dict]]:
        """Get segment details."""
        return self._make_request("GET", f"/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}")
    
    def update_segment(
        self,
        dataset_id: str,
        document_id: str,
        segment_id: str,
        content: Optional[str] = None,
        answer: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        enabled: Optional[bool] = None,
        regenerate_child_chunks: Optional[bool] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """Update segment."""
        segment_data = {}
        
        if content is not None:
            segment_data["content"] = content
        if answer is not None:
            segment_data["answer"] = answer
        if keywords is not None:
            segment_data["keywords"] = keywords
        if enabled is not None:
            segment_data["enabled"] = enabled
        if regenerate_child_chunks is not None:
            segment_data["regenerate_child_chunks"] = regenerate_child_chunks
            
        data = {"segment": segment_data}
        return self._make_request("POST", f"/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}", data=data)
    
    def delete_segment(self, dataset_id: str, document_id: str, segment_id: str) -> Tuple[bool, Optional[Dict]]:
        """Delete segment."""
        return self._make_request("DELETE", f"/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}")
    
    def create_child_chunk(
        self,
        dataset_id: str,
        document_id: str,
        segment_id: str,
        content: str
    ) -> Tuple[bool, Optional[Dict]]:
        """Create child chunk for hierarchical segmentation."""
        data = {"content": content}
        return self._make_request("POST", f"/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks", data=data)
    
    def list_child_chunks(
        self,
        dataset_id: str,
        document_id: str,
        segment_id: str,
        keyword: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[bool, Optional[Dict]]:
        """List child chunks of a segment."""
        params = {"page": page, "limit": limit}
        if keyword:
            params["keyword"] = keyword
            
        return self._make_request("GET", f"/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks", params=params)
    
    def update_child_chunk(
        self,
        dataset_id: str,
        document_id: str,
        segment_id: str,
        child_chunk_id: str,
        content: str
    ) -> Tuple[bool, Optional[Dict]]:
        """Update child chunk."""
        data = {"content": content}
        return self._make_request("PATCH", f"/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks/{child_chunk_id}", data=data)
    
    def delete_child_chunk(
        self,
        dataset_id: str,
        document_id: str,
        segment_id: str,
        child_chunk_id: str
    ) -> Tuple[bool, Optional[Dict]]:
        """Delete child chunk."""
        return self._make_request("DELETE", f"/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks/{child_chunk_id}")


class ModelManager(BaseAPIClient):
    """Manage embedding and retrieval models."""
    
    def get_available_embedding_models(self) -> Tuple[bool, Optional[Dict]]:
        """Get available embedding models."""
        return self._make_request("GET", "/workspaces/current/models/model-types/text-embedding")


class MetadataManager(BaseAPIClient):
    """Manage metadata and tags."""
    
    def create_tag(self, name: str) -> Tuple[bool, Optional[Dict]]:
        """Create a new knowledge base tag."""
        data = {"name": name}
        return self._make_request("POST", "/datasets/tags", data=data)
    
    def list_tags(self) -> Tuple[bool, Optional[Dict]]:
        """List all available knowledge base tags."""
        return self._make_request("GET", "/datasets/tags")
    
    def update_tag(self, tag_id: str, name: str) -> Tuple[bool, Optional[Dict]]:
        """Update tag name."""
        data = {"tag_id": tag_id, "name": name}
        return self._make_request("PATCH", "/datasets/tags", data=data)
    
    def delete_tag(self, tag_id: str) -> Tuple[bool, Optional[Dict]]:
        """Delete tag."""
        data = {"tag_id": tag_id}
        return self._make_request("DELETE", "/datasets/tags", data=data)
    
    def bind_tags_to_dataset(self, dataset_id: str, tag_ids: List[str]) -> Tuple[bool, Optional[Dict]]:
        """Bind tags to dataset."""
        data = {"target_id": dataset_id, "tag_ids": tag_ids}
        return self._make_request("POST", "/datasets/tags/binding", data=data)
    
    def unbind_tag_from_dataset(self, dataset_id: str, tag_id: str) -> Tuple[bool, Optional[Dict]]:
        """Unbind tag from dataset."""
        data = {"target_id": dataset_id, "tag_id": tag_id}
        return self._make_request("POST", "/datasets/tags/unbinding", data=data)
    
    def get_dataset_tags(self, dataset_id: str) -> Tuple[bool, Optional[Dict]]:
        """Get tags bound to a dataset."""
        return self._make_request("POST", f"/datasets/{dataset_id}/tags")


class DifyKnowledgeAPI:
    """Main class that provides access to all knowledge base operations."""
    
    def __init__(self, api_base: str, api_key: str, timeout_seconds: int = 120):
        self.datasets = DatasetManager(api_base, api_key, timeout_seconds)
        self.documents = DocumentManager(api_base, api_key, timeout_seconds)
        self.segments = SegmentManager(api_base, api_key, timeout_seconds)
        self.models = ModelManager(api_base, api_key, timeout_seconds)
        self.metadata = MetadataManager(api_base, api_key, timeout_seconds)
        
        # Store common configuration
        self.api_base = api_base
        self.api_key = api_key
        self.timeout = timeout_seconds
    
    def get_available_models(self) -> Tuple[bool, Optional[Dict]]:
        """Get available models for convenience."""
        return self.models.get_available_embedding_models()
    
    def create_knowledge_base(
        self, 
        name: str, 
        description: Optional[str] = None,
        indexing_technique: str = "high_quality"
    ) -> Tuple[bool, Optional[Dict]]:
        """Create a new knowledge base with default settings."""
        return self.datasets.create_dataset(
            name=name,
            description=description,
            indexing_technique=indexing_technique
        )
    
    def upload_document(
        self, 
        dataset_id: str, 
        file_path: str,
        indexing_technique: str = "high_quality"
    ) -> Tuple[bool, Optional[Dict]]:
        """Upload a document to a knowledge base."""
        return self.documents.create_document_from_file(
            dataset_id=dataset_id,
            file_path=file_path,
            indexing_technique=indexing_technique
        )
    
    def search_knowledge_base(
        self, 
        dataset_id: str, 
        query: str,
        top_k: int = 10
    ) -> Tuple[bool, Optional[Dict]]:
        """Search a knowledge base."""
        retrieval_model = {"top_k": top_k}
        return self.datasets.retrieve_segments(
            dataset_id=dataset_id,
            query=query,
            retrieval_model=retrieval_model
        )
