"""High-fidelity deterministic mock LLM provider for offline gameplay and automated test suites."""

from typing import List, Optional
from murderbox.models.case import SuspectProfile, EvidenceItem


class MockProvider:
    """Generates context-aware, deterministic dialogue responses for suspects without external API calls."""

    def generate_response(
        self,
        suspect: SuspectProfile,
        user_query: str,
        presented_evidence: Optional[List[EvidenceItem]] = None,
        dialogue_history: Optional[str] = None,
    ) -> str:
        """Determines the suspect's realistic dialogue based on role, question intent, and presented clues."""
        q_lower = user_query.lower()
        presented_ids = [e.id for e in (presented_evidence or [])]

        # 1. Culprit (Dr. Julian Croft) responses
        if suspect.id == "dr_croft":
            # Confession condition: confronted with both medical_bag and audit_dossier
            if "medical_bag" in presented_ids and "audit_dossier" in presented_ids:
                return (
                    "Enough... put the papers down! You found the audit dossier and the missing ampoule from my bag. "
                    "Arthur was a tyrant! He spent thirty years profiting from other men's brilliance, and when one trial went "
                    "wrong, he was ready to hand me to the prosecutor to save his stock price! "
                    "I slipped the compound through the silicone stopper seal... it was supposed to look like natural heart failure. "
                    "God help me."
                )

            # Confronted with medical kit alone
            if "medical_bag" in presented_ids:
                return (
                    "My medical bag? Detective, thousands of physicians carry emergency cardiovascular sedatives. "
                    "That ampoule was expended three days ago on a patient in the city. The fact that the needle sheath is "
                    "unsealed proves nothing except standard clinical hygiene."
                )

            # Confronted with scotch decanter
            if "scotch_decanter" in presented_ids:
                return (
                    "Microscopic needle punctures on the stopper? That is absurd. The decanter is an antique crystal set; "
                    "any imperfections are decades old. I never touched Arthur's decanter tonight."
                )

            # Confronted with muddy footprints
            if "muddy_footprints" in presented_ids:
                return (
                    "Bespoke brogues? Many gentlemen in Arthur's social circle wear bespoke English shoes. "
                    "I tell you, I was in my guest suite from 9:15 PM organizing my clinical journals. I never went outside."
                )

            # Confronted with audit dossier alone
            if "audit_dossier" in presented_ids:
                return (
                    "Arthur was deeply confused about those clinical logs. He lacked the scientific background to interpret "
                    "Phase II trial data. We were going to discuss the discrepancies over breakfast, not with malice."
                )

            # Alibi inquiry
            if any(w in q_lower for w in ["where were you", "alibi", "what time", "9:00", "9:15", "9:30", "9:45"]):
                return (
                    "As I told the constable, I retired to my guest suite at 9:15 PM sharp to review clinical trials "
                    "and organize my medicine kits. I never set foot in Arthur's study after dinner."
                )

            # Relationship / motive inquiry
            if any(w in q_lower for w in ["kill", "murder", "poison", "audit", "fraud", "why"]):
                return (
                    "Arthur Vance was not merely a patient; he was a benefactor of my research clinic. "
                    "His sudden cardiovascular collapse is a tragedy, but accusing his personal physician is preposterous."
                )

            return "As Arthur's physician, I can assure you his arterial tension was precarious. Look for natural causes, detective."

        # 2. Elena Vance responses
        elif suspect.id == "elena_vance":
            if "divorce_correspondence" in presented_ids:
                return (
                    "Yes, the divorce settlement was punitive. Arthur took pleasure in humiliating anyone who dared resist him. "
                    "I had my lawyers drafting injunctions, but I would never stoop to physical violence. My dignity is worth more than his estate."
                )
            if any(w in q_lower for w in ["where were you", "alibi", "time"]):
                return (
                    "I remained in the drawing room by the fire from 9:00 PM until the commotion began. "
                    "The storm was raging against the windows; I had no reason to leave the hearth."
                )
            if any(w in q_lower for w in ["money", "inherit", "will", "80m", "divorce"]):
                return (
                    "Arthur thought money was a leash to control people. Our marriage was dead years ago, "
                    "but I fight my battles in courtrooms, detective, not in the dark."
                )
            return "Arthur made enemies everywhere he went. If you want his killer, examine his shady business partners, not his wife."

        # 3. Marcus Sterling responses
        elif suspect.id == "marcus_sterling":
            if "confidential_memos" in presented_ids:
                return (
                    "All right, fine! I was looking for the quarterly audit files in the library. Arthur was threatening "
                    "to freeze my equity over accounting discrepancies. But I didn't lay a hand on him! Ask Croft or the groundskeeper."
                )
            if any(w in q_lower for w in ["where were you", "alibi", "terrace"]):
                return (
                    "I was on the covered terrace having a scotch and smoking cigars from 9:30 PM until after 10:30 PM. "
                    "You can check the terrace ashtray if you don't believe me."
                )
            if any(w in q_lower for w in ["embezzle", "steal", "money", "books"]):
                return (
                    "Vance Biometrics has complex offshore structures. Arthur was paranoid and saw conspiracies everywhere. "
                    "That doesn't mean I poisoned his nightcap!"
                )
            return "Arthur was screaming at everyone tonight. Don't look at me just because I stood up to him in the boardroom."

        # 4. Clara Dupont responses
        elif suspect.id == "clara_dupont":
            if "kitchen_order_slip" in presented_ids:
                return (
                    "That is my handwriting on the service slip. At 9:30 PM, I delivered the freshly uncorked decanter to Mr. Vance's desk. "
                    "Dr. Croft was lingering outside the door in the hallway. He told me he had an urgent medical consultation with Mr. Vance."
                )
            if any(w in q_lower for w in ["decanter", "scotch", "drink", "kitchen"]):
                return (
                    "I washed the crystal decanter myself and poured the 25-year scotch at 9:15 PM. "
                    "When I brought it into the study at 9:30 PM, it was pure. But Dr. Croft was waiting right outside the door."
                )
            if any(w in q_lower for w in ["where were you", "alibi", "nephew"]):
                return (
                    "I was in the butler's pantry washing glasses and preparing tomorrow's breakfast menus from 9:30 PM onward. "
                    "Mr. Vance was harsh with my nephew, yes, but vengeance belongs to the Lord."
                )
            return "I have served this house for over twenty years, detective. What I saw, I have told you faithfully."

        # 5. Vincent Reed responses
        elif suspect.id == "vincent_reed":
            if "compound_v7_vial" in presented_ids or "torn_chemistry_notebook" in presented_ids:
                return (
                    "Yes, that's Compound V-7 from my greenhouse bench! I developed the botanical extraction process myself, "
                    "and Arthur stole the patent! But two nights ago, someone broke the padlock on my refrigeration unit and stole that vial! "
                    "Whoever took it had a key or surgical tools!"
                )
            if any(w in q_lower for w in ["where were you", "alibi", "garden"]):
                return (
                    "I was outside in the south rose garden from 9:45 PM onward. The thunderstorm clears my head. "
                    "If you think I poisoned him, look at Croft—he's the one who understands sedative dosing and syringes."
                )
            return "Arthur Vance stole everything I ever invented, but I wouldn't dirty my hands by murdering him in his own study."

        # 6. Evelyn Cross responses
        elif suspect.id == "evelyn_cross":
            if "confidential_memos" in presented_ids:
                return (
                    "I... I leaked those memos to protect my own future. Arthur was going to liquidate the research subsidiary and fire us all! "
                    "Please, detective, I'm not a murderer. I saw what happened outside the study!"
                )
            if any(w in q_lower for w in ["see", "saw", "patio", "door", "corridor", "9:55"]):
                return (
                    "At 9:55 PM, I looked through the glass gallery toward the study patio. "
                    "I saw someone slipping out through the French doors into the pouring rain with their trench coat collar pulled up. "
                    "It was Dr. Croft! He had that hurried, frantic stride of his and muddy shoes."
                )
            if any(w in q_lower for w in ["where were you", "alibi", "library"]):
                return (
                    "I was in the library organizing the patent correspondence until 10:30 PM. "
                    "The library corridor gives a direct view of the east garden path."
                )
            return "There was dark business happening in Arthur's study tonight. You need to look at Dr. Croft's movements."

        # Default fallback
        return f"{suspect.name} regards you coldly: 'I have answered your questions, detective. Let the facts speak for themselves.'"
