import streamlit as st
import requests
import os
from dotenv import load_dotenv

# ========================================================================
# ENV SETUP
# ========================================================================

load_dotenv()

# Support both os.getenv (local) and st.secrets (Streamlit Cloud)
def get_secret(key, default=""):
    # Try st.secrets first (Streamlit Cloud)
    try:
        return st.secrets.get(key, default)
    except:
        pass
    # Fallback to environment variable
    return os.getenv(key, default)

API_BASE_URL = get_secret("API_BASE_URL", "http://localhost:8000")
API_KEY = get_secret("API_KEY", "")

if not API_KEY:
    st.error("API_KEY not found in environment variables.")
    st.stop()

# ========================================================================
# PAGE CONFIG
# ========================================================================

st.set_page_config(
    page_title="TheGeetaWay - Cosmic Wisdom Portal",
    page_icon="🪔",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ========================================================================
# HELPERS
# ========================================================================

# A cold Railway container has to warm the embedding model before it can answer,
# so the first search after an idle period is far slower than a warm one.
API_TIMEOUT = 120


def call_api(endpoint: str, method: str = "GET", data: dict = None):
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        if method == "POST":
            res = requests.post(
                f"{API_BASE_URL}{endpoint}",
                json=data,
                headers=headers,
                timeout=API_TIMEOUT
            )
        else:
            res = requests.get(
                f"{API_BASE_URL}{endpoint}",
                headers=headers,
                timeout=API_TIMEOUT
            )

        res.raise_for_status()
        return res.json(), None

    except Exception as e:
        return None, str(e)


def normalize_audio_url(audio_url: str):
    """Fix zero-padded chapter/verse issue"""
    try:
        parts = audio_url.split("/")
        chap = int(parts[-2].replace("CHAP", ""))
        verse = int(parts[-1].replace(".MP3", "").split("-")[1])
        parts[-2] = f"CHAP{chap}"
        parts[-1] = f"{chap}-{verse}.MP3"
        return "/".join(parts)
    except Exception:
        return audio_url

# ========================================================================
# COSMIC ANIMATED THEME
# ========================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Noto+Sans+Devanagari:wght@400;600;700&display=swap');

    /* ============================================
       COSMIC BASE - DEEP SPACE BACKGROUND
    ============================================ */
    
    * {
        font-family: 'Space Grotesk', sans-serif;
    }
    
    .stApp {
        background: #000000;
        overflow-x: hidden;
    }
    @keyframes starTwinkle {
        0%, 100% { opacity: 0.3; filter: drop-shadow(0 0 2px rgba(255,255,255,0.4)); }
        50% { opacity: 1; filter: drop-shadow(0 0 8px rgba(255,255,255,0.8)); }
    }

    /* Animated Starfield Layer 1 - Far stars */
    .stApp::before {
    content: "";
    position: fixed;
    inset: -20%;
    z-index: 0;

    background:
        radial-gradient(1px 1px at 25px 25px, rgba(255,255,255,1), transparent),
        radial-gradient(1px 1px at 75px 75px, rgba(255,255,255,0.9), transparent),
        radial-gradient(1px 1px at 125px 45px, rgba(255,255,255,0.95), transparent),
        radial-gradient(1px 1px at 45px 125px, rgba(255,255,255,0.85), transparent);

    background-size: 150px 150px;

    animation:
        starsMove 260s linear infinite,
        starTwinkle 6s ease-in-out infinite;

    filter: drop-shadow(0 0 4px rgba(255,255,255,0.6));
    opacity: 0.6;
    pointer-events: none;
}

    /* Animated Starfield Layer 2 - Close stars */
    .stApp::after {
    content: "";
    position: fixed;
    inset: -20%;
    z-index: 0;

    background:
        radial-gradient(2px 2px at 40px 60px, rgba(139,92,246,1), transparent),
        radial-gradient(2px 2px at 90px 20px, rgba(250,204,21,1), transparent),
        radial-gradient(2px 2px at 120px 100px, rgba(96,165,250,1), transparent),
        radial-gradient(1.5px 1.5px at 20px 110px, rgba(236,72,153,0.9), transparent);

    background-size: 180px 180px;

    animation:
        starsMoveFast 140s linear infinite,
        starTwinkle 4s ease-in-out infinite;

    filter: drop-shadow(0 0 8px rgba(250,204,21,0.8));
    opacity: 0.9;
    pointer-events: none;
}
            
.star-glow {
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    background:
        radial-gradient(circle, rgba(255,255,255,0.9) 1px, transparent 2px),
        radial-gradient(circle, rgba(250,204,21,0.8) 1px, transparent 2px);
    background-size: 200px 200px, 300px 300px;
    animation: starTwinkle 8s ease-in-out infinite;
    opacity: 0.3;
}

    
    @keyframes starsMove {
        0% { transform: translateY(0) translateX(0); }
        100% { transform: translateY(-100vh) translateX(-30vw); }
    }
    
    @keyframes starsMoveFast {
        0% { transform: translateY(0) translateX(0); }
        100% { transform: translateY(-50vh) translateX(20vw); }
    }
    
    /* Nebula Glow Effects */
    .main {
        position: relative;
        z-index: 1;
        padding: 1rem 2rem;
        background: 
            radial-gradient(ellipse 1200px 800px at 30% 20%, rgba(139, 92, 246, 0.08), transparent),
            radial-gradient(ellipse 1000px 600px at 70% 80%, rgba(250, 204, 21, 0.06), transparent),
            radial-gradient(ellipse 800px 800px at 50% 50%, rgba(236, 72, 153, 0.05), transparent);
        animation: nebulaFloat 20s ease-in-out infinite;
    }
    
    @keyframes nebulaFloat {
        0%, 100% { filter: brightness(1); }
        50% { filter: brightness(1.15); }
    }
    
    /* Cosmic Particles */
    .cosmic-particles {
        position: fixed;
        inset: 0;
        z-index: 0;
        pointer-events: none;
        background-image: 
            radial-gradient(circle, rgba(139, 92, 246, 0.4) 1px, transparent 1px),
            radial-gradient(circle, rgba(250, 204, 21, 0.3) 1px, transparent 1px);
        background-size: 50px 50px, 80px 80px;
        background-position: 0 0, 40px 40px;
        animation: particleDrift 60s linear infinite;
        opacity: 0.2;
    }
    
    @keyframes particleDrift {
        0% { transform: translateY(0) rotate(0deg); }
        100% { transform: translateY(-100vh) rotate(360deg); }
    }
    
    /* ============================================
       HEADER - COSMIC TITLE
    ============================================ */
    
    .cosmic-header {
        text-align: center;
        padding: 1.5rem 0;
        position: relative;
        margin-bottom: 1.5rem;
    }
    
   .cosmic-title {
    font-size: 4.2rem;
    font-weight: 600;
    letter-spacing: 3px;

    background: linear-gradient(180deg, #fcd34d, #f59e0b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;

    text-shadow: 0 8px 40px rgba(251,191,36,0.35);
    animation: none;
}

    
    @keyframes cosmicShimmer {
        0% { background-position: 0% center; }
        100% { background-position: 200% center; }
    }
    
    @keyframes titleFloat {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    .cosmic-subtitle {
    font-size: 1.05rem;
    color: #a78bfa;
    letter-spacing: 5px;
    opacity: 0.85;
    text-transform: uppercase;
    animation: none;
}
.main {
    max-width: 1100px;
    margin: 0 auto;
}

    
    .cosmic-tagline {
        font-size: 1.1rem;
        color: #cbd5e1;
        margin-top: 1rem;
        font-weight: 300;
        letter-spacing: 2px;
        opacity: 0.8;
    }
    
    @keyframes glowPulse {
        0%, 100% { text-shadow: 0 0 20px rgba(167, 139, 250, 0.6); }
        50% { text-shadow: 0 0 40px rgba(167, 139, 250, 0.9), 0 0 60px rgba(167, 139, 250, 0.6); }
    }
    
    /* Cosmic Divider */
    .cosmic-divider {
    height: 2px;
    width: 100%;
    margin: 1.5rem 0;

    background: linear-gradient(
        90deg,
        transparent,
        #8b5cf6,
        #fbbf24,
        #ec4899,
        #8b5cf6,
        transparent
    );
    background-size: 300% 100%;

    opacity: 0.75;
    filter: blur(0.2px);

    animation: dividerColorShift 22s ease-in-out infinite;
}

@keyframes dividerColorShift {
    0% {
        background-position: 0% 50%;
    }
    50% {
        background-position: 100% 50%;
    }
    100% {
        background-position: 0% 50%;
    }
}
.center-button {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: 2.5rem;
}

    
    /* ============================================
       CONTENT CARDS - GLASS MORPHISM
    ============================================ */
    
    .cosmic-card {
        background: linear-gradient(135deg, 
            rgba(15, 23, 42, 0.8) 0%, 
            rgba(30, 41, 59, 0.6) 100%
        );
        backdrop-filter: blur(20px);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 24px;
        padding: 2rem;
        margin: 1rem 0;
        position: relative;
        overflow: hidden;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.1),
            0 0 80px rgba(139, 92, 246, 0.1);
        animation: cardFloat 0.8s ease-out, cardGlow 6s ease-in-out infinite;
    }
    
    @keyframes cardFloat {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes cardGlow {
        0%, 100% { box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 80px rgba(139, 92, 246, 0.1); }
        50% { box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 100px rgba(139, 92, 246, 0.2); }
    }
    
    /* Cosmic Border Animation */
    .cosmic-card::before {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 24px;
        padding: 2px;
        background: linear-gradient(135deg, 
            rgba(139, 92, 246, 0.6), 
            rgba(250, 204, 21, 0.6), 
            rgba(236, 72, 153, 0.6),
            rgba(139, 92, 246, 0.6)
        );
        background-size: 300% 300%;
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        animation: borderRotate 8s linear infinite;
        opacity: 0.4;
    }
    
    @keyframes borderRotate {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Verse Header */
    .verse-header {
        font-size: 1.8rem;
        font-weight: 600;
        background: linear-gradient(135deg, #fbbf24, #f59e0b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
        animation: headerPulse 4s ease-in-out infinite;
    }
    
    @keyframes headerPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* ============================================
       AUDIO PLAYER - COSMIC STYLE
    ============================================ */
    
    /* ===== SACRED AUDIO PLAYER - MODERN DESIGN ===== */

/* Audio section wrapper - creates the visual container */
.audio-section {
    position: relative;
    margin: 2rem 0;
    padding: 2.5rem 2rem;
    background: linear-gradient(
        135deg,
        rgba(139, 92, 246, 0.15),
        rgba(250, 204, 21, 0.08)
    );
    border-radius: 24px;
    border: 1px solid rgba(139, 92, 246, 0.3);
    box-shadow:
        0 20px 60px rgba(0, 0, 0, 0.4),
        0 0 80px rgba(139, 92, 246, 0.15),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(12px);
}

.audio-section::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 24px;
    padding: 1px;
    background: linear-gradient(135deg, 
        rgba(139, 92, 246, 0.5), 
        rgba(250, 204, 21, 0.4), 
        rgba(139, 92, 246, 0.3)
    );
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
}

.audio-header {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
    color: #fbbf24;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
}

.audio-icon {
    font-size: 1.5rem;
    filter: drop-shadow(0 0 12px rgba(251, 191, 36, 0.8));
    animation: iconPulse 3s ease-in-out infinite;
}

@keyframes iconPulse {
    0%, 100% { transform: scale(1); filter: drop-shadow(0 0 12px rgba(251, 191, 36, 0.8)); }
    50% { transform: scale(1.1); filter: drop-shadow(0 0 20px rgba(251, 191, 36, 1)); }
}

.audio-title {
    background: linear-gradient(135deg, #fcd34d, #f59e0b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
}

.audio-caption {
    margin-top: 1.5rem;
    text-align: center;
    font-size: 0.85rem;
    color: #a78bfa;
    opacity: 0.9;
    letter-spacing: 1.5px;
    font-style: italic;
}

/* Modern Audio Player Styling */
.audio-section audio,
.audio-section .stAudio audio {
    width: 100% !important;
    max-width: 100% !important;
    height: 56px !important;
    border-radius: 16px !important;
    background: linear-gradient(180deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.9)) !important;
    border: 1px solid rgba(139, 92, 246, 0.25) !important;
    box-shadow: 
        0 4px 20px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

/* Streamlit audio wrapper */
.stAudio {
    width: 100% !important;
}

.stAudio > div {
    width: 100% !important;
}

/* Audio element inside Streamlit wrapper */
.stAudio audio {
    width: 100% !important;
    border-radius: 16px !important;
    accent-color: #fbbf24 !important;
    filter: brightness(1.1) saturate(1.2) !important;
    opacity: 0.75;
    letter-spacing: 1px;
}

    /* ============================================
       TEXT BLOCKS - SANSKRIT & ENGLISH
    ============================================ */
    
    .sanskrit-container {
        background: rgba(251, 191, 36, 0.08);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        position: relative;
        overflow: hidden;
        animation: textReveal 1s ease-out;
    }
    
    @keyframes textReveal {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .sanskrit-container::before {
        content: "॥";
        position: absolute;
        top: 10px;
        right: 20px;
        font-size: 4rem;
        color: rgba(251, 191, 36, 0.1);
        font-family: 'Noto Sans Devanagari', serif;
    }
    
    .text-label {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 1rem;
        color: #fbbf24;
    }
    
    .sanskrit-text {
        font-family: 'Noto Sans Devanagari', serif;
        font-size: 1.6rem;
        line-height: 2.4;
        color: #fde68a;
        font-weight: 500;
        text-shadow: 0 2px 10px rgba(251, 191, 36, 0.3);
    }
    
    .english-container {
        background: rgba(96, 165, 250, 0.08);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        animation: textReveal 1.2s ease-out;
    }
    
    .english-text {
        font-size: 1.2rem;
        line-height: 2;
        color: #e0e7ff;
        font-weight: 300;
        text-shadow: 0 1px 5px rgba(96, 165, 250, 0.2);
    }
    
    /* ============================================
       GUIDANCE BOX - PROFESSIONAL DARK
    ============================================ */
    
    .guidance-container {
        background: linear-gradient(135deg, 
            rgba(15, 23, 42, 0.95) 0%, 
            rgba(30, 41, 59, 0.9) 100%
        );
        border-radius: 20px;
        padding: 2.5rem;
        margin: 2rem 0;
        border: 1px solid rgba(139, 92, 246, 0.3);
        box-shadow: 
            0 16px 48px rgba(0, 0, 0, 0.4),
            0 0 60px rgba(139, 92, 246, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
        animation: guidanceReveal 0.8s ease-out;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(12px);
    }
    
    .guidance-container::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(
            90deg,
            transparent,
            #8b5cf6,
            #fbbf24,
            #ec4899,
            #8b5cf6,
            transparent
        );
        background-size: 300% 100%;
        border-radius: 20px 20px 0 0;
        animation: guidanceBorderShift 22s ease-in-out infinite;
    }
    
    @keyframes guidanceBorderShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes guidanceReveal {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .guidance-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #fbbf24;
        margin-bottom: 1.5rem;
        letter-spacing: 1px;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(139, 92, 246, 0.2);
    }
    
    .guidance-text {
        font-size: 1.05rem;
        line-height: 1.9;
        color: #e2e8f0;
        font-weight: 400;
    }
    
    .guidance-text strong {
        color: #fbbf24;
        font-weight: 600;
    }
    
    .guidance-section {
        margin-bottom: 1.25rem;
        padding-left: 1rem;
        border-left: 2px solid rgba(139, 92, 246, 0.3);
    }
    
    .guidance-section-title {
        color: #a78bfa;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    /* ============================================
       INPUT & BUTTON - COSMIC CONTROLS
    ============================================ */
    
    .stTextArea textarea {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
        border-radius: 16px !important;
        color: #e0e7ff !important;
        font-size: 1.1rem !important;
        padding: 1.5rem !important;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: rgba(139, 92, 246, 0.6) !important;
        box-shadow: 0 0 30px rgba(139, 92, 246, 0.3) !important;
    }
    
    .stSelectbox > div > div {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
        border-radius: 12px !important;
        color: #cbd5e1 !important;
        backdrop-filter: blur(10px);
    }
    
    /* =========================
   COSMIC CTA BUTTON
========================= */

.stButton > button {
    max-width: 420px;
    margin: 0 auto;

    background: linear-gradient(180deg, #fcd34d, #f59e0b);
    color: #1f2937;

    font-size: 1.05rem;
    font-weight: 600;
    letter-spacing: 2px;

    padding: 0.9rem 2rem;
    border-radius: 999px;

    box-shadow:
        0 8px 30px rgba(251,191,36,0.35);

    transition: all 0.25s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow:
        0 14px 45px rgba(251,191,36,0.45);
}

/* Hover – subtle lift + glow */
.stButton > button:hover {
    transform: translateY(-4px) scale(1.03) !important;
    box-shadow:
        0 14px 55px rgba(251, 191, 36, 0.6),
        0 0 90px rgba(251, 191, 36, 0.4) !important;
}

/* Active (click) */
.stButton > button:active {
    transform: translateY(0) scale(0.98) !important;
    box-shadow:
        0 6px 25px rgba(251, 191, 36, 0.4) !important;
}
.button-halo {
    position: relative;
    margin-top: 2rem;
}

.button-halo::before {
    content: "";
    position: absolute;
    inset: -20px;
    background: radial-gradient(
        circle,
        rgba(251,191,36,0.25),
        transparent 70%
    );
    z-index: -1;
    filter: blur(20px);
}

    
    @keyframes buttonGlow {
        0%, 100% { box-shadow: 0 8px 32px rgba(251, 191, 36, 0.4); }
        50% { box-shadow: 0 8px 48px rgba(251, 191, 36, 0.6), 0 0 60px rgba(251, 191, 36, 0.3); }
    }
    
    .stButton > button:hover {
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 0 12px 48px rgba(251, 191, 36, 0.6) !important;
    }
    
    /* ============================================
       LOADING SPINNER - COSMIC
    ============================================ */
    
    .stSpinner > div {
        border-top-color: #fbbf24 !important;
        animation: spinnerRotate 1s linear infinite, spinnerGlow 2s ease-in-out infinite !important;
    }
    
    @keyframes spinnerGlow {
        0%, 100% { filter: drop-shadow(0 0 10px rgba(251, 191, 36, 0.5)); }
        50% { filter: drop-shadow(0 0 20px rgba(251, 191, 36, 0.8)); }
    }
    
    /* ============================================
       FOOTER - COSMIC SIGNATURE
    ============================================ */
    
    .cosmic-footer {
        text-align: center;
        margin-top: 5rem;
        padding: 3rem 0;
        border-top: 1px solid rgba(139, 92, 246, 0.2);
        color: #94a3b8;
        font-size: 0.95rem;
        animation: footerFade 2s ease-in;
    }
    
    @keyframes footerFade {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .cosmic-footer .brand {
        font-size: 1.3rem;
        font-weight: 600;
        background: linear-gradient(90deg, #fbbf24, #f59e0b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    /* ============================================
       THEME BADGES
    ============================================ */
    
    .theme-badges-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin: 1.5rem 0;
    }
    
    .theme-badge {
        display: inline-block;
        background: rgba(139, 92, 246, 0.2);
        border: 1px solid rgba(139, 92, 246, 0.4);
        color: #c4b5fd;
        padding: 0.5rem 1.2rem;
        border-radius: 20px;
        font-size: 0.85rem;
        white-space: nowrap;
        animation: badgeFloat 3s ease-in-out infinite;
        transition: all 0.3s ease;
    }
    
    .theme-badge:hover {
        background: rgba(139, 92, 246, 0.35);
        border-color: rgba(139, 92, 246, 0.6);
        box-shadow: 0 0 12px rgba(139, 92, 246, 0.3);
    }
    
    @keyframes badgeFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-3px); }
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* Cinematic vignette to focus attention */
.stApp::marker { display: none; }


#result-anchor {
    scroll-behavior: smooth;
}


</style>

<!-- Cosmic Particles Layer -->
<div class="cosmic-particles"></div>    
            <div class="star-glow"></div>
            <div class="deep-stars"></div>
""", unsafe_allow_html=True)

# ========================================================================
# HEADER
# ========================================================================

st.markdown("""
<div class="cosmic-header">
    <div class="cosmic-title">The Geeta Way</div>
    <div class="cosmic-subtitle">Cosmic Wisdom Portal</div>
    <div class="cosmic-tagline">Journey Through Ancient Knowledge • Connect with Universal Truth</div>
</div>
<div class="cosmic-divider"></div>
""", unsafe_allow_html=True)

# ========================================================================
# INPUT
# ========================================================================

st.markdown("### 🌌 What guidance do you seek from the cosmos?")

examples = [
    "",
    "I feel confused and anxious about my future",
    "I struggle with anger and resentment",
    "How do I deal with failure and setbacks?",
    "I feel lost and without purpose in life",
    "How do I stay disciplined and focused?",
    "How can I find inner peace?",
    "I'm afraid of making the wrong decision"
]

example = st.selectbox("✨ Example cosmic queries", examples)
question = st.text_area("Your question to the universe", value=example, height=120, label_visibility="collapsed")

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    search = st.button("Cosmic Guidance", use_container_width=True)



# ========================================================================
# SEARCH & DISPLAY
# ========================================================================

if search and question.strip():

    with st.spinner("✨ Channeling wisdom from the cosmic consciousness..."):
        payload = {
            "question": question,
            "top_k": 5,
            "include_guidance": True
        }
        result, error = call_api("/api/v1/search", method="POST", data=payload)

    if error:
        st.error(f"🌠 Cosmic interference detected: {error}")
        st.stop()

    if not result or not result.get("verses"):
        st.warning("🌌 The cosmos returned no verses. Try rephrasing your query.")
        st.stop()

    verse = result["verses"][0]

    # Scroll anchor and Verse Card
    st.markdown('<div id="result-anchor"></div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="cosmic-card">
        <div class="verse-header">
            📖 Chapter {verse['chapter']}, Verse {verse['verse']}
            <span style="margin-left: 1rem; font-size: 0.9rem; opacity: 0.7;">Relevance: {verse['score']:.2f}</span>
        </div>
    """, unsafe_allow_html=True)

    # Theme badges with flexbox layout
    if verse.get('themes'):
        badges_html = '<div class="theme-badges-container">'
        for theme in verse['themes'][:4]:
            badges_html += f'<span class="theme-badge">✨ {theme}</span>'
        badges_html += '</div>'
        st.markdown(badges_html, unsafe_allow_html=True)
    
    # Auto-scroll JavaScript
    st.markdown("""
<script>
    setTimeout(() => {
        const anchor = document.getElementById("result-anchor");
        if (anchor) {
            anchor.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }, 300);
</script>
""", unsafe_allow_html=True)


    # Audio Section - Modern Design
    audio_url = normalize_audio_url(verse["audio_url"])

    # Create a styled container using columns
    st.markdown("""
    <style>
    [data-testid="stVerticalBlock"] > div:has(> .audio-section-marker) {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(250, 204, 21, 0.08));
        border-radius: 24px;
        border: 1px solid rgba(139, 92, 246, 0.3);
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 80px rgba(139, 92, 246, 0.15);
        backdrop-filter: blur(12px);
    }
    </style>
    <div class="audio-section-marker"></div>
    """, unsafe_allow_html=True)
    
    # Audio header
    st.markdown(
        '<div class="audio-header"><span class="audio-icon">🕉</span><span class="audio-title">Sacred Sanskrit Recitation</span></div>',
        unsafe_allow_html=True
    )
    
    # Audio player - full width modern style
    st.audio(audio_url, format="audio/mpeg")
    
    # Audio caption
    st.markdown(
        '<div class="audio-caption">Listen with attention • Let the sound guide the mind</div>',
        unsafe_allow_html=True
    )



    # Sanskrit
    st.markdown(f"""
    <div class="sanskrit-container">
        <div class="text-label">📜 संस्कृत • Original Sanskrit</div>
        <div class="sanskrit-text">{verse['sanskrit']}</div>
    </div>
    """, unsafe_allow_html=True)

    # English
    st.markdown(f"""
    <div class="english-container">
        <div class="text-label" style="color: #60a5fa;">🌍 English Translation</div>
        <div class="english-text">{verse['english']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Guidance
    if result.get("guidance"):
        guidance_text = result['guidance']['guidance_text']
        # Convert markdown bold to HTML and format sections
        import re
        guidance_text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', guidance_text)
        guidance_text = guidance_text.replace('\n', '<br>')
        st.markdown(f"""
        <div class="guidance-container">
            <div class="guidance-title">Your Personalized Guidance</div>
            <div class="guidance-text">{guidance_text}</div>
        </div>
        """, unsafe_allow_html=True)

    # Other verses
    if len(result["verses"]) > 1:
        st.markdown('<div class="cosmic-divider"></div>', unsafe_allow_html=True)
        st.markdown("### 🌠 Additional Cosmic Insights")
        
        with st.expander("🔭 Explore more universal wisdom"):
            for i, v in enumerate(result["verses"][1:], 2):
                st.markdown(f"""
                <div class="cosmic-card" style="margin: 1.5rem 0; padding: 1.5rem;">
                    <h4 style="color: #fbbf24; margin-bottom: 1rem;">
                        Insight {i} • Chapter {v['chapter']}, Verse {v['verse']} • Score: {v['score']:.2f}
                    </h4>
                """, unsafe_allow_html=True)
                
                if v.get('themes'):
                    for theme in v['themes'][:3]:
                        st.markdown(f'<span class="theme-badge" style="font-size: 0.75rem;">{theme}</span>', unsafe_allow_html=True)
                
                st.audio(normalize_audio_url(v["audio_url"]))
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**📜 Sanskrit:**")
                    st.markdown(f'<div style="color: #fde68a; font-family: \'Noto Sans Devanagari\', serif; font-size: 1.1rem; line-height: 1.8;">{v["sanskrit"]}</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"**🌍 English:**")
                    st.markdown(f'<div style="color: #e0e7ff; font-size: 0.95rem; line-height: 1.6;">{v["english"]}</div>', unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
