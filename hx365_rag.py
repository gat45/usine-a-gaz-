"""
HX365 Command Center - RAG Engine Module
==========================================

Advanced RAG system with USearch vector database and BGE embeddings.
Includes smart chunking, context management, and sliding window functionality.
"""

import asyncio
import os
import hashlib
import logging
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import re

import numpy as np
from usearch.index import Index
from transformers import AutoTokenizer, AutoModel
import torch
import nltk
from nltk.tokenize import sent_tokenize

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HX365-RAG")

# Configuration
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))
MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "4096"))
INDEX_FILE = Path(os.getenv("INDEX_FILE", "hx365_vector_index.us"))

@dataclass
class DocumentChunk:
    """Represents a chunk of a document"""
    id: str
    content: str
    document_id: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class RetrievedResult:
    """Represents a retrieved result from RAG"""
    content: str
    score: float
    document_id: str
    chunk_id: str
    metadata: Dict[str, Any]

class SmartChunker:
    """
    Intelligent document chunker that respects document structure
    """
    
    def __init__(self, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str, document_id: str) -> List[DocumentChunk]:
        """
        Split text into chunks respecting sentence boundaries and document structure
        """
        chunks = []
        
        # Split into sentences first
        sentences = sent_tokenize(text)
        
        current_chunk = ""
        current_sentences = []
        
        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(test_chunk) <= self.chunk_size:
                current_chunk = test_chunk
                current_sentences.append(sentence)
            else:
                # Save current chunk
                if current_sentences:
                    chunk_id = f"{document_id}_chunk_{len(chunks)}"
                    chunk = DocumentChunk(
                        id=chunk_id,
                        content=current_chunk.strip(),
                        document_id=document_id,
                        metadata={"sentence_count": len(current_sentences)}
                    )
                    chunks.append(chunk)
                
                # Start new chunk with overlap
                if self.overlap > 0:
                    # Take last few sentences from previous chunk as overlap
                    overlap_sentences = current_sentences[-2:] if len(current_sentences) >= 2 else current_sentences
                    overlap_text = " ".join(overlap_sentences)
                    current_chunk = overlap_text + " " + sentence
                    current_sentences = overlap_sentences + [sentence]
                else:
                    current_chunk = sentence
                    current_sentences = [sentence]
        
        # Add the last chunk if it has content
        if current_sentences:
            chunk_id = f"{document_id}_chunk_{len(chunks)}"
            chunk = DocumentChunk(
                id=chunk_id,
                content=current_chunk.strip(),
                document_id=document_id,
                metadata={"sentence_count": len(current_sentences)}
            )
            chunks.append(chunk)
        
        return chunks
    
    def chunk_code(self, code: str, document_id: str) -> List[DocumentChunk]:
        """
        Specialized chunker for code that respects function/class boundaries
        """
        chunks = []
        
        # Try to split by functions/classes if it's a programming language
        lines = code.split('\n')
        
        # Patterns for different languages
        func_patterns = [
            r'^\s*(def|class|function|public|private|protected|fn)\s+\w+',  # Python, JS, Java, Rust
            r'^\s*(if|for|while|switch)\s*\(',  # Control structures
            r'^\s*#\s+',  # Comments
        ]
        
        current_chunk = []
        chunk_start_line = 0
        
        for i, line in enumerate(lines):
            # Check if this line starts a new logical unit
            is_new_unit = any(re.match(pattern, line) for pattern in func_patterns)
            
            if is_new_unit and len(current_chunk) > 0:
                # Save current chunk
                chunk_content = '\n'.join(current_chunk)
                if len(chunk_content.strip()) > 0:  # Only save non-empty chunks
                    chunk_id = f"{document_id}_code_chunk_{len(chunks)}"
                    chunk = DocumentChunk(
                        id=chunk_id,
                        content=chunk_content,
                        document_id=document_id,
                        metadata={
                            "start_line": chunk_start_line,
                            "end_line": i-1,
                            "language": self._detect_language(code)
                        }
                    )
                    chunks.append(chunk)
                
                # Start new chunk with overlap
                if self.overlap > 0:
                    # Add previous lines as context
                    overlap_start = max(0, i - self.overlap)
                    current_chunk = lines[overlap_start:i+1]
                    chunk_start_line = overlap_start
                else:
                    current_chunk = [line]
                    chunk_start_line = i
            else:
                current_chunk.append(line)
        
        # Add the last chunk
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            if len(chunk_content.strip()) > 0:
                chunk_id = f"{document_id}_code_chunk_{len(chunks)}"
                chunk = DocumentChunk(
                    id=chunk_id,
                    content=chunk_content,
                    document_id=document_id,
                    metadata={
                        "start_line": chunk_start_line,
                        "end_line": len(lines)-1,
                        "language": self._detect_language(code)
                    }
                )
                chunks.append(chunk)
        
        return chunks
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language from code"""
        first_few_lines = '\n'.join(code.split('\n')[:10]).lower()
        
        if 'import torch' in first_few_lines or 'import tensorflow' in first_few_lines:
            return 'python_ml'
        elif 'def ' in first_few_lines and 'import ' in first_few_lines:
            return 'python'
        elif 'function ' in first_few_lines or 'const ' in first_few_lines:
            return 'javascript'
        elif 'public class' in first_few_lines or 'private void' in first_few_lines:
            return 'java'
        elif '#include' in first_few_lines:
            return 'cpp'
        elif 'func ' in first_few_lines:
            return 'go'
        elif 'fn ' in first_few_lines and '->' in first_few_lines:
            return 'rust'
        else:
            return 'unknown'

class BGEEncoder:
    """
    BGE (BAAI General Embedding) encoder for generating embeddings
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_model()
    
    def _load_model(self):
        """Load the BGE model"""
        try:
            logger.info(f"Loading BGE model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info("BGE model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load BGE model: {e}")
            # Fallback to a simpler approach
            logger.info("Using fallback embedding method")
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts
        """
        if self.model is None:
            # Fallback embedding using simple hashing
            return self._fallback_encode(texts)
        
        try:
            # Tokenize the texts
            encoded = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                return_tensors='pt',
                max_length=512
            ).to(self.device)
            
            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**encoded)
                # Use the CLS token for sentence embedding
                embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            return embeddings.astype(np.float32)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            # Fallback to simple method
            return self._fallback_encode(texts)
    
    def _fallback_encode(self, texts: List[str]) -> np.ndarray:
        """
        Fallback embedding method using hashing
        """
        embeddings = []
        for text in texts:
            # Simple hash-based embedding
            text_hash = hashlib.md5(text.encode()).hexdigest()
            embedding = np.zeros(EMBEDDING_DIM, dtype=np.float32)
            
            # Fill the embedding with values derived from the hash
            for i in range(min(len(text_hash), EMBEDDING_DIM)):
                embedding[i] = int(text_hash[i % len(text_hash)], 16) / 15.0  # Normalize to [0, 1]
            
            embeddings.append(embedding)
        
        return np.array(embeddings, dtype=np.float32)

class USearchIndex:
    """
    USearch vector index for efficient similarity search
    """
    
    def __init__(self, index_file: Path, embedding_dim: int = EMBEDDING_DIM):
        self.index_file = index_file
        self.embedding_dim = embedding_dim
        self.index = Index(
            ndim=self.embedding_dim,
            metric="cos",
            dtype="f32"
        )
        self.document_chunks: Dict[str, DocumentChunk] = {}
        
        # Load existing index if it exists
        if self.index_file.exists():
            try:
                self.index.load(str(self.index_file))
                logger.info(f"Loaded existing index from {self.index_file}")
                
                # Load associated document chunks
                chunks_file = self.index_file.with_suffix(".chunks.json")
                if chunks_file.exists():
                    import json
                    with open(chunks_file, 'r', encoding='utf-8') as f:
                        chunks_data = json.load(f)
                        for chunk_data in chunks_data:
                            chunk = DocumentChunk(**chunk_data)
                            chunk.created_at = datetime.fromisoformat(chunk.created_at)
                            self.document_chunks[chunk.id] = chunk
            except Exception as e:
                logger.error(f"Failed to load existing index: {e}")
    
    def add_chunk(self, chunk: DocumentChunk, embedding: np.ndarray):
        """
        Add a chunk to the index
        """
        # Generate a unique ID for the index (using hash of content to ensure uniqueness)
        chunk_id_hash = int(hashlib.md5(chunk.id.encode()).hexdigest()[:16], 16)
        
        # Add to USearch index
        self.index.add(chunk_id_hash, embedding)
        
        # Store the chunk metadata separately
        self.document_chunks[chunk.id] = chunk
        
        # Save the index and chunks
        self.save()
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[str, float]]:
        """
        Search for similar chunks
        """
        if len(self.index) == 0:
            return []
        
        # Perform search
        result_keys, distances, _ = self.index.search(query_embedding, k=k)
        
        # Map back to chunk IDs and scores
        results = []
        for key, distance in zip(result_keys, distances):
            # Find the chunk ID that corresponds to this key
            chunk_id = None
            for cid, chunk in self.document_chunks.items():
                if int(hashlib.md5(cid.encode()).hexdigest()[:16], 16) == key:
                    chunk_id = cid
                    break
            
            if chunk_id:
                # Convert distance to similarity score (cosine similarity)
                # Distance is Euclidean, so we convert to similarity
                similarity = 1 / (1 + distance)  # Simple transformation
                results.append((chunk_id, similarity))
        
        return results
    
    def save(self):
        """
        Save the index and document chunks to disk
        """
        try:
            # Save the USearch index
            self.index.save(str(self.index_file))
            
            # Save document chunks separately
            chunks_file = self.index_file.with_suffix(".chunks.json")
            import json
            chunks_data = []
            for chunk in self.document_chunks.values():
                chunk_dict = {
                    'id': chunk.id,
                    'content': chunk.content,
                    'document_id': chunk.document_id,
                    'metadata': chunk.metadata,
                    'created_at': chunk.created_at.isoformat()
                }
                chunks_data.append(chunk_dict)
            
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(chunks_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Index saved to {self.index_file}")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")

class ContextManager:
    """
    Manages conversation context with sliding window functionality
    """
    
    def __init__(self, max_tokens: int = MAX_CONTEXT_TOKENS):
        self.max_tokens = max_tokens
        self.tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5") if os.path.exists("BAAI/bge-small-en-v1.5") else None
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text (approximation if tokenizer not available)
        """
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Rough approximation: 1 token ≈ 4 characters
            return len(text) // 4
    
    def truncate_context(self, messages: List[Dict[str, str]], retrieved_chunks: List[RetrievedResult] = None) -> List[Dict[str, str]]:
        """
        Truncate context using sliding window approach
        """
        if not messages:
            return messages
        
        # Calculate total tokens with retrieved context if provided
        total_content = ""
        for msg in messages:
            total_content += msg.get("content", "") + "\n"
        
        if retrieved_chunks:
            for chunk in retrieved_chunks:
                total_content += chunk.content + "\n"
        
        total_tokens = self.count_tokens(total_content)
        
        if total_tokens <= self.max_tokens:
            return messages
        
        # Need to truncate - keep system message if present, then recent messages
        truncated_messages = []
        current_tokens = 0
        
        # Always keep system message if it exists
        system_msg = None
        for msg in messages:
            if msg.get("role") == "system":
                system_msg = msg
                system_tokens = self.count_tokens(msg.get("content", ""))
                current_tokens += system_tokens
                break
        
        if system_msg:
            truncated_messages.append(system_msg)
            remaining_messages = [msg for msg in messages if msg != system_msg]
        else:
            remaining_messages = messages[:]
        
        # Add messages from the end (most recent) until we reach the limit
        for msg in reversed(remaining_messages):
            msg_tokens = self.count_tokens(msg.get("content", ""))
            if current_tokens + msg_tokens <= self.max_tokens:
                truncated_messages.insert(1, msg)  # Insert after system message
                current_tokens += msg_tokens
            else:
                break
        
        # Reverse to restore chronological order
        if system_msg:
            # Keep system message first, then reverse the rest
            non_system = [msg for msg in truncated_messages if msg != system_msg]
            non_system.reverse()
            return [system_msg] + non_system
        else:
            truncated_messages.reverse()
            return truncated_messages

class RAGEngine:
    """
    Main RAG engine that combines all components
    """
    
    def __init__(self):
        self.chunker = SmartChunker()
        self.encoder = BGEEncoder()
        self.vector_index = USearchIndex(INDEX_FILE)
        self.context_manager = ContextManager()
        self.documents: Dict[str, str] = {}  # Store full documents
    
    def ingest_document(self, content: str, doc_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Ingest a document into the RAG system
        """
        if doc_id is None:
            doc_id = f"doc_{hashlib.md5(content.encode()).hexdigest()[:12]}"
        
        # Store the full document
        self.documents[doc_id] = content
        
        # Determine if it's code or text
        if self._is_code(content):
            chunks = self.chunker.chunk_code(content, doc_id)
        else:
            chunks = self.chunker.chunk_text(content, doc_id)
        
        # Generate embeddings for all chunks
        chunk_contents = [chunk.content for chunk in chunks]
        embeddings = self.encoder.encode(chunk_contents)
        
        # Add chunks to index
        for chunk, embedding in zip(chunks, embeddings):
            self.vector_index.add_chunk(chunk, embedding)
        
        logger.info(f"Ingested document '{doc_id}' with {len(chunks)} chunks")
        return doc_id
    
    def _is_code(self, text: str) -> bool:
        """
        Simple heuristic to determine if text is code
        """
        code_indicators = [
            'def ', 'class ', 'import ', 'from ', 'function ',
            '{', '}', 'var ', 'let ', 'const ', 'public ', 'private ',
            '#include', 'int main', 'void ', 'struct ', 'enum '
        ]
        
        lines = text.split('\n')[:10]  # Check first 10 lines
        code_lines = 0
        
        for line in lines:
            if any(indicator in line for indicator in code_indicators):
                code_lines += 1
        
        # If more than 30% of the first lines contain code indicators, treat as code
        return code_lines / max(len(lines), 1) > 0.3
    
    async def retrieve(self, query: str, k: int = 5) -> List[RetrievedResult]:
        """
        Retrieve relevant chunks for a query
        """
        # Encode the query
        query_embeddings = self.encoder.encode([query])
        query_embedding = query_embeddings[0]
        
        # Search in the vector index
        search_results = self.vector_index.search(query_embedding, k=k)
        
        # Get the actual chunks and create results
        retrieved_results = []
        for chunk_id, similarity in search_results:
            if chunk_id in self.vector_index.document_chunks:
                chunk = self.vector_index.document_chunks[chunk_id]
                result = RetrievedResult(
                    content=chunk.content,
                    score=similarity,
                    document_id=chunk.document_id,
                    chunk_id=chunk.id,
                    metadata=chunk.metadata
                )
                retrieved_results.append(result)
        
        # Sort by score (descending)
        retrieved_results.sort(key=lambda x: x.score, reverse=True)
        
        return retrieved_results
    
    def augment_query_with_context(self, query: str, retrieved_results: List[RetrievedResult]) -> str:
        """
        Augment a query with retrieved context
        """
        if not retrieved_results:
            return query
        
        context_parts = ["Contexte récupéré:"]
        for result in retrieved_results:
            context_parts.append(f"Document: {result.document_id}")
            context_parts.append(f"Contenu: {result.content}")
            context_parts.append("---")
        
        augmented_query = "\n".join(context_parts) + f"\n\nQuestion originale: {query}"
        return augmented_query
    
    def get_document_summary(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get summary information about a document
        """
        if doc_id not in self.documents:
            return None
        
        content = self.documents[doc_id]
        chunks = [chunk for chunk in self.vector_index.document_chunks.values() if chunk.document_id == doc_id]
        
        return {
            "id": doc_id,
            "length": len(content),
            "chunk_count": len(chunks),
            "first_chunk_preview": chunks[0].content[:100] + "..." if chunks else "",
            "ingested_at": chunks[0].created_at.isoformat() if chunks else None
        }

# Global instance
rag_engine = RAGEngine()