"""Noir detective styling and CSS theme for MurderBox Streamlit application."""


def get_noir_css() -> str:
    """Returns custom CSS injecting a classic dark noir detective aesthetic."""
    return """
    <style>
    /* Main container and theme */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Georgia', serif;
    }
    
    /* Header typography */
    h1, h2, h3, h4 {
        font-family: 'Courier New', monospace;
        letter-spacing: 1px;
        color: #f0f6fc;
    }
    
    .noir-title {
        font-family: 'Courier New', monospace;
        font-size: 2.6rem;
        font-weight: 900;
        color: #d4af37;
        text-shadow: 2px 2px 4px #000000;
        border-bottom: 2px solid #8b0000;
        padding-bottom: 8px;
        margin-bottom: 4px;
    }
    
    .noir-subtitle {
        font-style: italic;
        color: #8b949e;
        font-size: 1.1rem;
        margin-bottom: 20px;
    }

    /* Cards and dossier blocks */
    .noir-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    
    .noir-card-critical {
        border-left: 4px solid #8b0000;
    }
    
    .noir-card-gold {
        border-left: 4px solid #d4af37;
    }

    /* Contradiction Alert Box */
    .contradiction-badge {
        background-color: #3d0c0c;
        border: 1px solid #ff4d4d;
        border-radius: 6px;
        padding: 12px;
        margin-top: 10px;
        margin-bottom: 10px;
        color: #ff9999;
        font-family: 'Courier New', monospace;
        font-size: 0.95rem;
    }

    /* Dialogue bubbles */
    .chat-bubble-detective {
        background-color: #1f2937;
        border-left: 4px solid #38bdf8;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 8px;
        color: #f1f5f9;
    }

    .chat-bubble-suspect {
        background-color: #272115;
        border-left: 4px solid #d4af37;
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 12px;
        color: #fef08a;
    }

    /* Evidence tag */
    .evidence-badge {
        display: inline-block;
        background-color: #8b0000;
        color: #ffffff;
        font-size: 0.75rem;
        font-weight: bold;
        padding: 2px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 6px 6px 0 0;
        color: #8b949e;
        padding: 10px 16px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #21262d !important;
        color: #d4af37 !important;
        font-weight: bold;
        border-bottom: 2px solid #d4af37 !important;
    }
    </style>
    """
