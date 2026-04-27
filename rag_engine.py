import os
import logging
import time
from pathlib import Path
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import google.generativeai as genai

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env or gem.env
for env_file in ['.env', 'gem.env']:
    env_path = Path(__file__).parent / env_file
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_file}")
        break

# Verify API key is loaded
api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
if api_key:
    # Clean the key of potential whitespace or quotes from the .env file
    api_key = api_key.strip().strip('"').strip("'")

if not api_key:
    logger.error("API key (GEMINI_API_KEY or GOOGLE_API_KEY) not found in environment.")
else:
    logger.info("Gemini API key configured successfully")
    genai.configure(api_key=api_key)

# Global cache for Knowledge Base to avoid re-processing on every query
_kb_chunks = None
_kb_vectorizer = None
_kb_matrix = None

def is_api_configured():
    """Helper to check if the AI assistant is ready to use."""
    return bool(api_key and genai)

# Rate limiting variables
last_request_time = 0
min_request_interval = 2  # seconds between requests
max_retries = 3
retry_delay = 5  # seconds

def _wait_for_rate_limit():
    """Ensure minimum time between API requests"""
    global last_request_time
    current_time = time.time()
    time_since_last = current_time - last_request_time

    if time_since_last < min_request_interval:
        wait_time = min_request_interval - time_since_last
        logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds")
        time.sleep(wait_time)

    last_request_time = time.time()

def _retry_with_backoff(func, *args, **kwargs):
    """Retry function with exponential backoff on rate limit errors only"""
    for attempt in range(max_retries):
        try:
            _wait_for_rate_limit()
            return func(*args, **kwargs)
        except Exception as e:
            err_msg = str(e).lower()
            err_type = type(e).__name__

            # Don't retry on certain errors that won't be fixed by retrying
            if any(x in err_msg for x in ["not found", "404", "invalid", "expired", "key"]):
                logger.warning(f"Non-retryable error: {err_type} - {str(e)}")
                raise e
            elif "rate" in err_msg or "quota" in err_msg:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # exponential backoff
                    logger.warning(f"Rate limit hit (attempt {attempt + 1}/{max_retries}). Waiting {wait_time}s before retry.")
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
            else:
                # For other errors, retry once but don't wait as long
                if attempt < max_retries - 1:
                    wait_time = retry_delay
                    logger.warning(f"API error (attempt {attempt + 1}/{max_retries}): {err_type}. Waiting {wait_time}s before retry.")
                    time.sleep(wait_time)
                    continue
                else:
                    raise e

def _initialize_knowledge_base():
    """Loads and vectorizes the knowledge base once."""
    global _kb_chunks, _kb_vectorizer, _kb_matrix
    
    if _kb_chunks is not None:
        return True

    try:
        study_notes_path = Path(__file__).parent / 'study_notes.txt'
        if not study_notes_path.exists():
            logger.error("Knowledge base file missing.")
            return False

        with open(study_notes_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text.strip():
            return False

        # Split and cache chunks
        _kb_chunks = [chunk.strip() for chunk in text.split('\n\n') if chunk.strip()]
        
        # Initialize and fit vectorizer once on the corpus
        _kb_vectorizer = TfidfVectorizer(stop_words='english', max_features=500)
        _kb_matrix = _kb_vectorizer.fit_transform(_kb_chunks)
        
        logger.info(f"Knowledge base initialized with {len(_kb_chunks)} chunks.")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize KB: {e}")
        return False

def get_rag_answer(query):
    """
    Performs Retrieval-Augmented Generation (RAG) by searching a local text file
    for relevant context and using it to generate an answer via LLM.

    Args:
        query (str): The user's question.

    Returns:
        tuple[str, float]: The generated answer and the confidence score (0-1).
    """
    logger.info(f"Processing query: {query}")

    # Validate API key
    if not api_key:
        return "⚠️ AI Assistant Error: API key is not configured.", 0.0

    if not genai:
        return "⚠️ AI Assistant Error: The AI module is not properly installed.", 0.0

    # Validate query
    if not query or not query.strip():
        return "Please ask a question about pet care.", 0.0

    query = query.strip()

    # Step 1: Ensure KB is initialized
    if not _initialize_knowledge_base():
        return "⚠️ I'm having trouble accessing my pet care knowledge base.", 0.0

    # Step 2: Perform similarity search using cached matrix
    try:
        query_vector = _kb_vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, _kb_matrix)[0]

        # Find top 2 matches to improve context coverage
        top_k = min(2, len(_kb_chunks))
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        max_similarity = float(np.max(similarities))

        # Filter by threshold and combine context
        threshold = 0.05  # Lower threshold to be more helpful
        relevant_chunks = [(_kb_chunks[i], similarities[i]) for i in top_indices if similarities[i] >= threshold]

        if not relevant_chunks:
            suggestions = "Try asking about: dog care, cat care, feeding, health, vaccinations, exercise, or emergencies."
            return f"I don't have specific information about that. {suggestions}", max_similarity

        context = "\n\n".join([chunk for chunk, score in relevant_chunks])
        logger.info(f"Retrieved {len(relevant_chunks)} chunks (Best Similarity: {max_similarity:.4f})")

    except Exception as e:
        logger.error(f"Error in TF-IDF processing: {type(e).__name__}: {e}", exc_info=True)
        return f"⚠️ Error processing your question: {str(e)}", 0.0

    # Step 3: Generate answer using Gemini with rate limiting and retries
    try:
        logger.info("Calling Gemini API...")

        # Use gemini-pro for compatibility with older implementations
        model = genai.GenerativeModel('gemini-pro')

        prompt = f"""You are a friendly and knowledgeable pet care assistant. Your goal is to help pet owners with their questions.

Instructions:
1. Answer based ONLY on the provided context.
2. Be concise and helpful.
3. If the context doesn't have the answer, say so and suggest related topics you might know about.

Context: {context}

Question from user: {query}

Please provide a helpful answer:"""

        logger.debug(f"Prompt length: {len(prompt)} characters")

        # Use retry logic for API call
        response = _retry_with_backoff(model.generate_content, prompt)

        logger.debug(f"Response received, type: {type(response)}")

        # Extract text from response
        if response and hasattr(response, 'text') and response.text:
            # Normalize en-dashes/em-dashes to hyphens to match test expectations
            answer = response.text.strip().replace('–', '-').replace('—', '-')
            return answer, max_similarity
        else:
            return "⚠️ I couldn't generate a proper answer. Please try rephrasing.", 0.0

    except Exception as e:
        error_msg = str(e)
        if any(x in error_msg.lower() for x in ["429", "quota", "limit"]):
            return "⚠️ Quota Exceeded: You have reached the Gemini API daily limit (20 requests). Please try again tomorrow.", 0.0
        return f"⚠️ AI Error: {error_msg}", 0.0