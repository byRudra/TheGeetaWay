from groq import Groq
import os
from functools import lru_cache
import hashlib

# ========================================================================
# GROQ CLIENT INITIALIZATION
# ========================================================================

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Groq retires models periodically - keep this overridable without a code change.
# Current list: https://console.groq.com/docs/models
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def detect_verse_context(verse_text: str) -> dict:
    """Detect if verse has specific context that might need translation"""
    text_lower = verse_text.lower()
    
    context = {
        'is_battlefield': False,
        'is_death_focused': False,
        'is_devotional': False,
        'is_cosmic': False,
        'is_universal': True  # Default to universal
    }
    
    # Battlefield/warrior context
    battlefield_keywords = [
        'battlefield', 'warrior', 'general', 'army', 'combat', 
        'fight', 'weapon', 'arjun', 'fled', 'respect for you'
    ]
    context['is_battlefield'] = any(kw in text_lower for kw in battlefield_keywords)
    
    # Death/rebirth focus
    death_keywords = [
        'death is certain', 'rebirth is inevitable', 'born and die',
        'imperishable', 'unborn', 'eternal soul'
    ]
    context['is_death_focused'] = any(kw in text_lower for kw in death_keywords)
    
    # Devotional/surrender
    devotional_keywords = [
        'surrender unto me', 'devotees', 'divine love', 'worship',
        'absorbed in me', 'refuge in me'
    ]
    context['is_devotional'] = any(kw in text_lower for kw in devotional_keywords)
    
    # Cosmic/mystical
    cosmic_keywords = [
        'cosmic form', 'universes', 'divine form', 'celestial',
        'creation and dissolution', 'brahma'
    ]
    context['is_cosmic'] = any(kw in text_lower for kw in cosmic_keywords)
    
    # Universal applicability (practical action-oriented verses)
    universal_keywords = [
        'one who', 'one whose', 'therefore', 'thus', 'should',
        'must', 'control', 'practice', 'perform', 'abandon'
    ]
    if any(kw in text_lower for kw in universal_keywords):
        context['is_universal'] = True
    
    return context


def create_translation_guide(verse_context: dict) -> str:
    """Create context-specific translation guide for metaphorical verses"""
    
    if not any([
        verse_context['is_battlefield'],
        verse_context['is_death_focused'],
        verse_context['is_devotional']
    ]):
        return ""  # No translation needed for universal verses
    
    guide = "\n**Translation Guide:**"
    
    if verse_context['is_battlefield']:
        guide += """
- "Battlefield" → Your current challenging situation
- "Warrior/Arjun" → You, facing your challenge
- "Fleeing/Retreating" → Avoiding or giving up on what matters
- "Generals/Respect" → Your self-respect and integrity
- "Fighting" → Courageously facing your responsibilities
- "Duty" → Your authentic path and responsibilities"""
    
    if verse_context['is_death_focused']:
        guide += """
- "Death/Rebirth" → Life transitions and change
- "Imperishable soul" → Your core values and essence
- "Temporary body" → External circumstances and conditions
- "Inevitable" → Acceptance of life's natural cycles"""
    
    if verse_context['is_devotional']:
        guide += """
- "Surrender to Me" → Let go of ego and trust the process
- "Divine" → Higher purpose or universal principles
- "Devotion" → Commitment to your values and growth"""
    
    return guide


def rank_verses_by_suitability(verses: list, user_problem: str) -> list:
    """Re-rank verses based on context suitability for the user's problem"""
    
    problem_lower = user_problem.lower()
    
    # Detect if problem is about literal death/loss
    is_grief_query = any(word in problem_lower for word in [
        'died', 'death', 'lost someone', 'grief', 'mourning', 'passed away'
    ])
    
    # Detect if problem is about confronting challenges
    is_confrontation_query = any(word in problem_lower for word in [
        'confront', 'face', 'stand up', 'courage', 'brave', 'difficult situation'
    ])
    
    ranked = []
    for verse in verses:
        context = detect_verse_context(verse['english'])
        suitability_score = verse.get('relevance_adjusted', verse['score'])
        
        # Boost scores for appropriate contexts
        if context['is_death_focused'] and is_grief_query:
            suitability_score *= 1.2  # Boost for grief queries
        elif context['is_death_focused'] and not is_grief_query:
            suitability_score *= 0.7  # Reduce for non-grief queries
        
        if context['is_battlefield'] and is_confrontation_query:
            suitability_score *= 1.1  # Slight boost for confrontation
        elif context['is_battlefield']:
            suitability_score *= 0.8  # Slight reduction for other queries
        
        if context['is_universal']:
            suitability_score *= 1.1  # Boost universal verses
        
        verse['suitability_score'] = suitability_score
        verse['context'] = context
        ranked.append(verse)
    
    # Sort by suitability
    ranked.sort(key=lambda x: x['suitability_score'], reverse=True)
    
    return ranked


# ========================================================================
# MAIN REASONING FUNCTION
# ========================================================================

def reason_over_verses(user_problem: str, retrieved_verses: list) -> str:
    """
    Generate spiritual guidance using a Groq-hosted LLM (see GROQ_MODEL)
    
    Args:
        user_problem: User's question or situation
        retrieved_verses: List of verse dictionaries from FAISS search
    
    Returns:
        Formatted guidance string with verse selection and advice
    """
    
    # Filter by minimum score threshold
    good_verses = [v for v in retrieved_verses if v.get('score', 0) > 0.30]
    
    if not good_verses:
        return """❌ No highly relevant verses found for your query.

💡 **Try being more specific:**
- Instead of: "I need help"
  Try: "I feel anxious about an upcoming job interview"

- Instead of: "Life is hard"
  Try: "I'm struggling to balance work and family responsibilities"

**Example questions:**
- "How do I handle conflict with a difficult colleague?"
- "I'm afraid of making the wrong career decision"
- "I feel stuck and unmotivated in my daily routine"
"""
    
    # Re-rank verses by suitability for this specific problem
    ranked_verses = rank_verses_by_suitability(good_verses, user_problem)
    
    # Select top 3 most suitable verses
    top_verses = ranked_verses[:3]
    
    # Format verses for the prompt
    verses_text = ""
    for i, v in enumerate(top_verses, 1):
        themes = ", ".join(v.get('themes', [])[:2]) if v.get('themes') else ""
        context = v.get('context', {})
        
        # Add context indicators
        context_tags = []
        if context.get('is_battlefield'):
            context_tags.append("Uses battlefield metaphor")
        if context.get('is_death_focused'):
            context_tags.append("Discusses impermanence")
        if context.get('is_devotional'):
            context_tags.append("Devotional teaching")
        if context.get('is_universal'):
            context_tags.append("Universal wisdom")
        
        context_tag_str = f" [{', '.join(context_tags)}]" if context_tags else ""
        
        verses_text += f"""
**Verse {i}** {'⭐ HIGHEST MATCH' if i == 1 else ''}
Chapter {v['chapter']}, Verse {v['verse']} | Suitability: {v.get('suitability_score', v['score']):.3f}
{f"Addresses: {themes}" if themes else ""}{context_tag_str}

"{v['english']}"
"""
        
        # Add translation guide if needed
        translation = create_translation_guide(context)
        if translation:
            verses_text += translation + "\n"
    
    # ========================================================================
    # SYSTEM PROMPT
    # ========================================================================
    
    system_prompt = """You are a compassionate life coach and spiritual guide who helps people apply timeless Bhagavad Gita wisdom to modern life challenges.

**Core Principles:**
- Be warm, empathetic, and non-judgmental
- Focus on practical, actionable guidance over philosophy
- Translate ancient metaphors to contemporary contexts
- Avoid being preachy or overly religious
- Speak in clear, accessible language
- Prioritize the verse marked ⭐ HIGHEST MATCH unless it's clearly inappropriate

**When handling metaphorical verses:**
- Battlefield metaphors → Modern challenges and difficult decisions
- Death/rebirth → Life transitions, change, letting go
- Devotion/surrender → Trusting the process, releasing ego
- Always ground advice in the user's real-world situation"""

    # ========================================================================
    # USER PROMPT
    # ========================================================================
    
    user_prompt = f"""A person is seeking guidance for their life situation:

**Their Situation:**
"{user_problem}"

**Top Matching Verses from Bhagavad Gita:**
{verses_text}

**Your Task:**

1. **Select the most appropriate verse** - Usually Verse 1 (⭐ HIGHEST MATCH), but use your judgment:
   - Avoid verses about death/rebirth for everyday problems (unless about grief/loss)
   - Avoid battlefield metaphors unless about confronting challenges
   - Prefer universal, practical wisdom for general life questions

2. **Explain the connection** (2-3 sentences):
   - Use the person's own words from their situation
   - Show specifically how this verse addresses their exact concern
   - If verse uses metaphor, translate it to their context

3. **Give actionable guidance** (4-5 sentences):
   - Provide concrete steps they can take TODAY
   - Be specific and practical, not abstract
   - Reference their situation directly
   - Build on the verse's wisdom in modern terms

**Response Format:**

📖 **Selected Verse:** Chapter X, Verse Y

💡 **Why This Resonates:**
[Connect the verse teaching directly to their specific problem. Use their words. If metaphorical, translate clearly.]

🪔 **Practical Steps:**
[Give specific, actionable guidance. What should they do today? This week? Focus on real-world application.]

**Word limit:** 180 words total. Be concise, warm, and specific."""

    # ========================================================================
    # GROQ API CALL
    # ========================================================================
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            model=GROQ_MODEL,
            temperature=0.68,      # Balanced between creativity and consistency
            max_tokens=1500,       # Headroom: reasoning models spend tokens before answering
            top_p=0.92,            # Nucleus sampling for quality
            extra_body={"reasoning_effort": "low"},
        )

        content = (chat_completion.choices[0].message.content or "").strip()

        if not content:
            return "🌌 The guidance came back empty. Please try rephrasing your question."

        return content

    except Exception as e:
        error_msg = str(e)
        lowered = error_msg.lower()

        # Provide specific error guidance - always return a string, never None,
        # because the API layer requires guidance_text to be present.
        if "api_key" in lowered or "authentication" in lowered or "401" in error_msg:
            return """❌ **API Key Error**

Your Groq API key is missing or invalid. Please check your `.env` file to ensure the `GROQ_API_KEY` is set correctly."""

        if "model_not_found" in lowered or "does not exist" in lowered:
            return f"""❌ **Model Unavailable**

The configured Groq model (`{GROQ_MODEL}`) is no longer available on this API key.
Set the `GROQ_MODEL` environment variable to a current model from https://console.groq.com/docs/models."""

        if "rate limit" in lowered or "429" in error_msg:
            return "⏳ **Rate limit reached.** The guidance service is busy - please try again in a moment."

        return f"❌ **Guidance is unavailable right now.** ({error_msg[:200]})"
