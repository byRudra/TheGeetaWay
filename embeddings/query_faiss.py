"""
Query FAISS index for relevant Bhagavad Gita verses
Converted from Jupyter notebook for use in Streamlit app
"""

import json
import os

# torch sizes its thread pool from the host's CPU count, not the container's
# cgroup quota. Inside Railway's CPU limit that oversubscription made a single
# MiniLM encode take ~22s instead of ~20ms. These must be set before torch is
# imported (directly or via sentence_transformers) for OpenMP to honour them.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

torch.set_num_threads(1)

# ========================================================================
# CONFIGURATION
# ========================================================================

# Determine paths relative to this file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)  # Parent directory

INDEX_PATH = os.path.join(PROJECT_ROOT, "faiss_index", "gita.index")
META_PATH = os.path.join(PROJECT_ROOT, "faiss_index", "metadata.json")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 12

# ========================================================================
# GLOBAL VARIABLES (loaded once)
# ========================================================================

_model = None
_index = None
_metadata = None

def load_resources():
    """Load model, index, and metadata (singleton pattern)"""
    global _model, _index, _metadata
    
    if _model is None:
        print("🔹 Loading embedding model...")
        _model = SentenceTransformer(MODEL_NAME)
    
    if _index is None:
        print("🔹 Loading FAISS index...")
        if not os.path.exists(INDEX_PATH):
            raise FileNotFoundError(f"FAISS index not found at: {INDEX_PATH}")
        _index = faiss.read_index(INDEX_PATH)
    
    if _metadata is None:
        print("🔹 Loading metadata...")
        if not os.path.exists(META_PATH):
            raise FileNotFoundError(f"Metadata not found at: {META_PATH}")
        with open(META_PATH, "r", encoding="utf-8") as f:
            _metadata = json.load(f)
        print(f"✅ Loaded {_index.ntotal} verses\n")
    
    return _model, _index, _metadata

# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def categorize_problem(query: str) -> dict:
    """Understand the type of problem to boost relevant themes"""
    query_lower = query.lower()
    
    problem_type = {
        'emotional': False,
        'decision': False,
        'relationship': False,
        'career': False,
        'existential': False
    }
    
    # Emotional distress
    if any(w in query_lower for w in [
        'afraid', 'fear', 'anxious', 'worried', 'stressed', 
        'overwhelmed', 'panic', 'nervous', 'scared'
    ]):
        problem_type['emotional'] = True
    
    # Decision-making
    if any(w in query_lower for w in [
        'should i', 'confused', 'don\'t know', 'uncertain', 
        'choice', 'decide', 'which', 'whether'
    ]):
        problem_type['decision'] = True
    
    # Relationships
    if any(w in query_lower for w in [
        'family', 'friend', 'colleague', 'relationship', 
        'conflict', 'argument', 'partner', 'spouse', 'parent'
    ]):
        problem_type['relationship'] = True
    
    # Career/purpose
    if any(w in query_lower for w in [
        'career', 'job', 'work', 'future', 'path', 
        'purpose', 'goal', 'profession', 'business'
    ]):
        problem_type['career'] = True
    
    # Existential
    if any(w in query_lower for w in [
        'meaning', 'why', 'life', 'death', 'purpose of', 
        'exist', 'point of'
    ]):
        problem_type['existential'] = True
    
    return problem_type


def enhance_query_contextual(query: str) -> str:
    """Add context based on problem type"""
    problem_type = categorize_problem(query)
    
    base = f"Practical life guidance: {query}"
    
    # Add relevant context
    contexts = []
    if problem_type['emotional']:
        contexts.append("managing fear and anxiety")
    if problem_type['decision']:
        contexts.append("making clear decisions")
    if problem_type['career']:
        contexts.append("finding purpose and direction")
    if problem_type['relationship']:
        contexts.append("handling interpersonal challenges")
    if problem_type['existential']:
        contexts.append("understanding life's meaning")
    
    if contexts:
        base += f". Focus on: {', '.join(contexts)}"
    
    return base


def filter_context_specific_verses(results, user_problem):
    """Filter out verses too context-specific unless problem matches"""
    
    query_lower = user_problem.lower()
    
    # Check if user's problem is about reputation/honor/social judgment
    is_social_concern = any(word in query_lower for word in [
        'reputation', 'respect', 'judged', 'what people think', 
        'embarrassed', 'ashamed', 'honor', 'image'
    ])
    
    # Check if about facing difficult challenges
    is_confrontation = any(word in query_lower for word in [
        'confront', 'face', 'stand up', 'challenge', 'difficult situation'
    ])
    
    filtered = []
    for verse in results:
        text_lower = verse['english'].lower()
        
        # Flag battlefield/war-specific verses
        is_battlefield = any(word in text_lower for word in [
            'battlefield', 'warrior', 'general', 'war', 'combat', 
            'army', 'weapon', 'fight', 'battle'
        ])
        
        # Flag death/rebirth focused verses
        is_death_focused = any(phrase in text_lower for phrase in [
            'death is certain', 'rebirth is inevitable', 
            'born and die', 'dissolution'
        ])
        
        # Adjust relevance based on context
        if is_battlefield and not (is_social_concern or is_confrontation):
            verse['context_warning'] = 'battlefield'
            verse['relevance_adjusted'] = verse['score'] * 0.75
        elif is_death_focused and not categorize_problem(user_problem)['existential']:
            verse['context_warning'] = 'death_rebirth'
            verse['relevance_adjusted'] = verse['score'] * 0.80
        else:
            verse['context_warning'] = None
            verse['relevance_adjusted'] = verse['score']
        
        filtered.append(verse)
    
    # Re-sort by adjusted relevance
    filtered.sort(key=lambda x: x['relevance_adjusted'], reverse=True)
    
    return filtered


# ========================================================================
# MAIN SEARCH FUNCTION
# ========================================================================

def search_gita(query: str, top_k: int = TOP_K, filter_practical: bool = True):
    """
    Search for relevant Gita verses with intelligent filtering
    
    Args:
        query: User's question or problem
        top_k: Number of initial results to fetch
        filter_practical: Whether to prioritize practical verses
    
    Returns:
        List of top 5 most relevant verses with metadata
    """
    
    # Load resources (lazy loading)
    model, index, metadata = load_resources()
    
    # Enhance query with contextual information
    enhanced_query = enhance_query_contextual(query)
    
    # Encode the enhanced query
    query_embedding = model.encode(
        [enhanced_query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    
    # Search FAISS index
    distances, indices = index.search(query_embedding, top_k)
    
    # Build results list
    results = []
    for idx, score in zip(indices[0], distances[0]):
        if idx >= len(metadata):  # Safety check
            continue
            
        verse = metadata[idx]
        results.append({
            "score": float(score),
            "chapter": verse["chapter"],
            "verse": verse["verse"],
            "sanskrit": verse["sanskrit"],
            "english": verse["english"],
            "themes": verse.get("themes", []),
            "is_practical": verse.get("is_practical", False)
        })
    
    # Apply context-aware filtering
    results = filter_context_specific_verses(results, query)
    
    # Filter for practical verses if requested
    if filter_practical:
        # Prioritize practical verses without context warnings
        ideal_verses = [
            r for r in results 
            if r['is_practical'] and not r.get('context_warning')
        ]
        
        if len(ideal_verses) >= 5:
            results = ideal_verses[:5]
        else:
            # Mix ideal verses with others
            results = ideal_verses + [
                r for r in results 
                if r not in ideal_verses
            ]
            results = results[:5]
    else:
        results = results[:5]
    
    # Final sort by adjusted relevance
    results.sort(key=lambda x: x.get('relevance_adjusted', x['score']), reverse=True)
    
    return results


# ========================================================================
# TESTING (only when run directly)
# ========================================================================

if __name__ == "__main__":
    # Test the search function
    test_query = "I feel confused and afraid about my future"
    print(f"Testing query: {test_query}\n")
    
    results = search_gita(test_query)
    
    print(f"Found {len(results)} verses:\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. Chapter {r['chapter']}, Verse {r['verse']}")
        print(f"   Score: {r['score']:.4f}")
        print(f"   {r['english'][:100]}...")
        print()