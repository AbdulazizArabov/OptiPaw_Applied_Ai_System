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

# Load environment variables from gem.env explicitly
env_path = Path(__file__).parent / 'gem.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    logger.warning(f"gem.env not found at {env_path}")

# Verify API key is loaded
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    logger.error("GEMINI_API_KEY not found in environment variables. Please ensure gem.env exists and contains the key.")
else:
    logger.info("GEMINI_API_KEY loaded successfully")
    genai.configure(api_key=api_key)

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
            error_type = type(e).__name__
            error_msg = str(e).lower()

            # Don't retry on certain errors that won't be fixed by retrying
            if "not found" in error_msg or "notfound" in error_type or "404" in error_msg:
                logger.warning(f"Non-retryable error: {error_type} - {str(e)}")
                raise e
            elif "rate" in error_msg or "quota" in error_msg:
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
                    logger.warning(f"API error (attempt {attempt + 1}/{max_retries}): {error_type}. Waiting {wait_time}s before retry.")
                    time.sleep(wait_time)
                    continue
                else:
                    raise e

def get_rag_answer(query):
    """
    Performs Retrieval-Augmented Generation (RAG) by searching a local text file
    for relevant context and using it to generate an answer via LLM.

    Args:
        query (str): The user's question.

    Returns:
        str: The generated answer or a polite refusal if no relevant context.
    """
    logger.info(f"Processing query: {query}")

    # Validate API key
    if not api_key:
        logger.error("API key is not available")
        return "⚠️ AI Assistant Error: API key is not configured. Please check your gem.env file."

    if not genai:
        logger.error("google.generativeai module is not available")
        return "⚠️ AI Assistant Error: The AI module is not properly installed."

    # Validate query
    if not query or not query.strip():
        logger.warning("Empty query received")
        return "Please ask a question about pet care."

    query = query.strip()

    # Step 1: Load knowledge base
    try:
        study_notes_path = Path(__file__).parent / 'study_notes.txt'
        logger.info(f"Loading knowledge base from: {study_notes_path}")

        if not study_notes_path.exists():
            logger.error(f"Knowledge base not found at {study_notes_path}")
            return "⚠️ Knowledge base not found. Please ensure study_notes.txt exists."

        with open(study_notes_path, 'r', encoding='utf-8') as f:
            text = f.read()

        if not text:
            logger.error("Knowledge base is empty")
            return "⚠️ Knowledge base is empty."

        logger.info(f"Knowledge base loaded: {len(text)} characters")

    except FileNotFoundError:
        logger.error(f"study_notes.txt not found")
        return "⚠️ I don't have access to my knowledge base right now."
    except Exception as e:
        logger.error(f"Error reading knowledge base: {type(e).__name__}: {e}")
        return f"⚠️ Error accessing knowledge base: {str(e)}"

    # Step 2: Split text into chunks
    try:
        chunks = [chunk.strip() for chunk in text.split('\n\n') if chunk.strip()]
        if not chunks:
            logger.error("No chunks found after splitting")
            return "⚠️ Knowledge base could not be processed."
        logger.info(f"Created {len(chunks)} knowledge chunks")
    except Exception as e:
        logger.error(f"Error splitting text: {type(e).__name__}: {e}")
        return f"⚠️ Error processing knowledge base: {str(e)}"

    # Step 3: Perform TF-IDF vectorization and similarity search
    try:
        documents = chunks + [query]
        logger.debug(f"Total documents for vectorization: {len(documents)}")

        vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
        tfidf_matrix = vectorizer.fit_transform(documents)
        logger.debug(f"TF-IDF matrix shape: {tfidf_matrix.shape}")

        # Calculate cosine similarities
        query_vector = tfidf_matrix[-1]
        chunk_vectors = tfidf_matrix[:-1]
        similarities = cosine_similarity(query_vector, chunk_vectors)[0]

        # Find best match
        max_similarity = np.max(similarities)
        best_chunk_idx = np.argmax(similarities)
        logger.info(f"Best match similarity: {max_similarity:.4f}")

        # Set a reasonable threshold
        threshold = 0.05  # Lower threshold to be more helpful

        if max_similarity < threshold:
            logger.info(f"No relevant context found (similarity {max_similarity:.4f} < {threshold})")
            suggestions = "Try asking about: dog care, cat care, feeding, health, vaccinations, exercise, or emergencies."
            return f"I don't have specific information about that. {suggestions}"

        context = chunks[best_chunk_idx]
        logger.info(f"Selected context chunk: {context[:100]}...")

    except Exception as e:
        logger.error(f"Error in TF-IDF processing: {type(e).__name__}: {e}", exc_info=True)
        return f"⚠️ Error processing your question: {str(e)}"

    # Step 4: Generate answer using Gemini with rate limiting and retries
    try:
        logger.info("Calling Gemini API...")

        # Use gemini-flash-latest for better compatibility
        model = genai.GenerativeModel('gemini-flash-latest')

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
            answer = response.text.strip()
            logger.info(f"Generated answer: {len(answer)} characters")
            return answer
        else:
            logger.warning(f"Invalid response from Gemini: {response}")
            return "⚠️ I couldn't generate a proper answer. Please try rephrasing your question."

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        logger.error(f"Gemini API Error - {error_type}: {error_msg}", exc_info=True)

        # Provide specific error messages based on error type
        if "API_KEY" in error_msg.upper() or "AUTHENTICATION" in error_msg.upper():
            return "⚠️ API Key Error: The AI assistant is not properly authenticated."
        elif "RATE" in error_msg.upper() or "QUOTA" in error_msg.upper():
            return "⚠️ Rate Limit: Too many requests. Please wait a moment and try again."
        elif "NOT_FOUND" in error_type.upper() or "404" in error_msg:
            return "⚠️ Model Error: The AI model is currently unavailable. Please try again later."
        elif "RESOURCE" in error_msg.upper():
            return "⚠️ Service Unavailable: The AI service is temporarily unavailable."
        else:
            return f"⚠️ AI Error: {error_msg}"


# Test the module when run directly
if __name__ == "__main__":
    logger.info("Testing RAG Engine...")
    test_question = "How often should I feed my dog?"
    print(f"\nTest Question: {test_question}")
    print(f"Answer: {get_rag_answer(test_question)}")

def get_rag_answer(query):
    """
    Performs Retrieval-Augmented Generation (RAG) by searching a local text file
    for relevant context and using it to generate an answer via LLM.

    Args:
        query (str): The user's question.

    Returns:
        str: The generated answer or a polite refusal if no relevant context.
    """
    logger.info(f"Processing query: {query}")

    # Validate API key
    if not api_key:
        logger.error("API key is not available")
        return "⚠️ AI Assistant Error: API key is not configured. Please check your gem.env file."

    if not genai:
        logger.error("google.generativeai module is not available")
        return "⚠️ AI Assistant Error: The AI module is not properly installed."

    # Validate query
    if not query or not query.strip():
        logger.warning("Empty query received")
        return "Please ask a question about pet care."

    query = query.strip()

    # Step 1: Load knowledge base
    try:
        study_notes_path = Path(__file__).parent / 'study_notes.txt'
        logger.info(f"Loading knowledge base from: {study_notes_path}")

        if not study_notes_path.exists():
            logger.error(f"Knowledge base not found at {study_notes_path}")
            return "⚠️ Knowledge base not found. Please ensure study_notes.txt exists."

        with open(study_notes_path, 'r', encoding='utf-8') as f:
            text = f.read()

        if not text:
            logger.error("Knowledge base is empty")
            return "⚠️ Knowledge base is empty."

        logger.info(f"Knowledge base loaded: {len(text)} characters")

    except FileNotFoundError:
        logger.error(f"study_notes.txt not found")
        return "⚠️ I don't have access to my knowledge base right now."
    except Exception as e:
        logger.error(f"Error reading knowledge base: {type(e).__name__}: {e}")
        return f"⚠️ Error accessing knowledge base: {str(e)}"

    # Step 2: Split text into chunks
    try:
        chunks = [chunk.strip() for chunk in text.split('\n\n') if chunk.strip()]
        if not chunks:
            logger.error("No chunks found after splitting")
            return "⚠️ Knowledge base could not be processed."
        logger.info(f"Created {len(chunks)} knowledge chunks")
    except Exception as e:
        logger.error(f"Error splitting text: {type(e).__name__}: {e}")
        return f"⚠️ Error processing knowledge base: {str(e)}"

    # Step 3: Perform TF-IDF vectorization and similarity search
    try:
        documents = chunks + [query]
        logger.debug(f"Total documents for vectorization: {len(documents)}")

        vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
        tfidf_matrix = vectorizer.fit_transform(documents)
        logger.debug(f"TF-IDF matrix shape: {tfidf_matrix.shape}")

        # Calculate cosine similarities
        query_vector = tfidf_matrix[-1]
        chunk_vectors = tfidf_matrix[:-1]
        similarities = cosine_similarity(query_vector, chunk_vectors)[0]

        # Find best match
        max_similarity = np.max(similarities)
        best_chunk_idx = np.argmax(similarities)
        logger.info(f"Best match similarity: {max_similarity:.4f}")

        # Set a reasonable threshold
        threshold = 0.05  # Lower threshold to be more helpful

        if max_similarity < threshold:
            logger.info(f"No relevant context found (similarity {max_similarity:.4f} < {threshold})")
            suggestions = "Try asking about: dog care, cat care, feeding, health, vaccinations, exercise, or emergencies."
            return f"I don't have specific information about that. {suggestions}"

        context = chunks[best_chunk_idx]
        logger.info(f"Selected context chunk: {context[:100]}...")

    except Exception as e:
        logger.error(f"Error in TF-IDF processing: {type(e).__name__}: {e}", exc_info=True)
        return f"⚠️ Error processing your question: {str(e)}"

    # Step 4: Generate answer using Gemini
    try:
        logger.info("Calling Gemini API...")

        model = genai.GenerativeModel('gemini-flash-latest')

        prompt = f"""You are a friendly and knowledgeable pet care assistant. Your goal is to help pet owners with their questions.

Instructions:
1. Answer based ONLY on the provided context.
2. Be concise and helpful.
3. If the context doesn't have the answer, say so and suggest related topics you might know about.

Context: {context}

Question from user: {query}

Please provide a helpful answer:"""

        logger.debug(f"Prompt length: {len(prompt)} characters")

        # Call API without timeout parameter (it doesn't support it)
        response = model.generate_content(prompt)

        logger.debug(f"Response received, type: {type(response)}")

        # Extract text from response
        if response and hasattr(response, 'text') and response.text:
            answer = response.text.strip()
            logger.info(f"Generated answer: {len(answer)} characters")
            return answer
        else:
            logger.warning(f"Invalid response from Gemini: {response}")
            return "⚠️ I couldn't generate a proper answer. Please try rephrasing your question."

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        logger.error(f"Gemini API Error - {error_type}: {error_msg}", exc_info=True)

        # Provide specific error messages based on error type
        if "API_KEY" in error_msg.upper() or "AUTHENTICATION" in error_msg.upper():
            return "⚠️ API Key Error: The AI assistant is not properly authenticated."
        elif "RATE" in error_msg.upper():
            return "⚠️ Rate Limit: Too many requests. Please try again in a moment."
        elif "RESOURCE" in error_msg.upper():
            return "⚠️ Service Unavailable: The AI service is temporarily unavailable."
        else:
            return f"⚠️ AI Error: {error_msg}"


# Test the module when run directly
if __name__ == "__main__":
    logger.info("Testing RAG Engine...")
    test_question = "How often should I feed my dog?"
    print(f"\nTest Question: {test_question}")
    print(f"Answer: {get_rag_answer(test_question)}")