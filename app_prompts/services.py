"""
Service layer for prompt processing, embedding generation, and similarity search.
Provides clean separation between AI logic and REST API views.
"""
import hashlib
import logging
import numpy as np
import faiss
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

# Global FAISS index - in-memory, rebuilt on server restart
EMBEDDING_DIMENSION = 384
_faiss_index = None
_prompt_id_map = {}  # Maps FAISS index position to prompt ID


def initialize_index():
    """
    Initialize the FAISS index for similarity search.
    Loads all existing embeddings from the database.
    """
    global _faiss_index, _prompt_id_map
    
    # Create L2 distance index
    _faiss_index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
    _prompt_id_map = {}
    
    # Import here to avoid circular imports
    from .models import Prompt
    
    prompts_with_embeddings = Prompt.objects.filter(
        embedding__isnull=False
    ).values_list('id', 'embedding')
    
    for prompt_id, embedding in prompts_with_embeddings:
        if embedding and len(embedding) == EMBEDDING_DIMENSION:
            embedding_array = np.array([embedding], dtype=np.float32)
            position = _faiss_index.ntotal
            _faiss_index.add(embedding_array)
            _prompt_id_map[position] = prompt_id
    
    logger.info(f"FAISS index initialized with {_faiss_index.ntotal} embeddings")


def get_faiss_index():
    """Get or initialize the FAISS index."""
    global _faiss_index
    if _faiss_index is None:
        initialize_index()
    return _faiss_index


def generate_response(prompt_text: str) -> str:
    """
    Generate a simulated LLM response for a given prompt.
    In production, this would call an actual LLM API.
    
    Args:
        prompt_text: The user's prompt
        
    Returns:
        A simulated response string
    """
    logger.info(f"Generating LLM response for prompt (length={len(prompt_text)} chars)")
    
    # Simulate different response types based on prompt content
    prompt_lower = prompt_text.lower()
    
    if any(word in prompt_lower for word in ['hello', 'hi', 'hey']):
        return f"Hello! You said: '{prompt_text}'. How can I assist you today?"
    elif any(word in prompt_lower for word in ['what', 'how', 'why', 'when', 'where', 'who']):
        return f"That's an interesting question about: '{prompt_text}'. Let me help you with that. Based on my analysis, here's what I can tell you..."
    elif any(word in prompt_lower for word in ['explain', 'describe', 'tell me']):
        return f"I'd be happy to explain. Regarding '{prompt_text}', here's a comprehensive overview of the topic..."
    elif any(word in prompt_lower for word in ['help', 'assist', 'support']):
        return f"I'm here to help with '{prompt_text}'. Let me provide you with some guidance on this matter..."
    else:
        return f"Thank you for your input: '{prompt_text}'. I've processed your request and here's my response. This is a simulated answer that demonstrates the system's capability to generate contextual responses."


def get_embedding(text: str) -> List[float]:
    """
    Generate a deterministic 384-dimensional embedding vector for the given text.
    Uses a simple hashing-based approach for consistent results.
    In production, this would use a real embedding model.
    
    Args:
        text: The text to embed
        
    Returns:
        A list of 384 float values representing the embedding
    """
    logger.info(f"Computing embedding vector (dimension={EMBEDDING_DIMENSION}) for text (length={len(text)} chars)")
    
    # Use multiple hash functions to generate diverse vector components
    embedding = []
    
    # Normalize text for consistent embeddings
    text_normalized = text.lower().strip()
    
    # Generate 384 dimensions using multiple hash seeds
    for i in range(EMBEDDING_DIMENSION):
        # Create a unique hash for each dimension
        hash_input = f"{text_normalized}_{i}".encode('utf-8')
        hash_value = hashlib.sha256(hash_input).hexdigest()
        
        # Convert hex to float in range [-1, 1]
        int_value = int(hash_value[:8], 16)
        float_value = (int_value / (16**8)) * 2 - 1
        embedding.append(float_value)
    
    # Normalize the vector to unit length (L2 normalization)
    embedding_array = np.array(embedding, dtype=np.float32)
    norm = np.linalg.norm(embedding_array)
    if norm > 0:
        embedding_array = embedding_array / norm
    
    return embedding_array.tolist()


def add_to_index(prompt_id: int, embedding: List[float]) -> None:
    """
    Add a prompt's embedding to the FAISS index.
    
    Args:
        prompt_id: The database ID of the prompt
        embedding: The 384-dimensional embedding vector
    """
    global _prompt_id_map
    
    if len(embedding) != EMBEDDING_DIMENSION:
        logger.error(f"Invalid embedding dimension: {len(embedding)}, expected {EMBEDDING_DIMENSION}")
        return
    
    index = get_faiss_index()
    embedding_array = np.array([embedding], dtype=np.float32)
    
    position = index.ntotal
    index.add(embedding_array)
    _prompt_id_map[position] = prompt_id
    
    logger.info(f"Added prompt ID {prompt_id} to FAISS index at position {position}")


def find_similar(embedding: List[float], top_k: int = 5) -> List[Tuple[int, float]]:
    """
    Find the most similar prompts to the given embedding.
    
    Args:
        embedding: The query embedding vector
        top_k: Number of similar results to return
        
    Returns:
        List of (prompt_id, distance) tuples, sorted by similarity (lowest distance first)
    """
    index = get_faiss_index()
    
    if index.ntotal == 0:
        logger.info("FAISS index is empty, no similar prompts found")
        return []
    
    if len(embedding) != EMBEDDING_DIMENSION:
        logger.error(f"Invalid embedding dimension: {len(embedding)}, expected {EMBEDDING_DIMENSION}")
        return []
    
    # Limit top_k to available entries
    k = min(top_k, index.ntotal)
    
    logger.info(f"Performing FAISS similarity search (top_k={k}, index_size={index.ntotal})")
    
    embedding_array = np.array([embedding], dtype=np.float32)
    distances, indices = index.search(embedding_array, k)
    
    # Convert to list of (prompt_id, distance) tuples
    results = []
    for idx, distance in zip(indices[0], distances[0]):
        if idx in _prompt_id_map:
            prompt_id = _prompt_id_map[idx]
            results.append((prompt_id, float(distance)))
    
    logger.info(f"FAISS search completed, found {len(results)} similar prompts")
    return results


