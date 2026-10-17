"""SQLite-backed persistent memory manager for interrogation history and factual claims."""

import sqlite3
import json
import time
from typing import List, Optional, Dict, Any
from murderbox.models.dialogue import (
    InterrogationTurn,
    StatementClaim,
    ContradictionResult,
    ContradictionType,
    ContradictionSeverity,
)


class MemoryManager:
    """Manages SQLite storage and retrieval for interrogation dialogue and claims."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        # For in-memory databases, SQLite requires keeping the connection open
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return self._conn

    def _init_db(self) -> None:
        """Creates the required tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interrogation_turns (
                    turn_id TEXT PRIMARY KEY,
                    suspect_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    presented_evidence_json TEXT NOT NULL,
                    response TEXT NOT NULL,
                    contradictions_json TEXT NOT NULL,
                    model_name TEXT,
                    is_fallback INTEGER NOT NULL DEFAULT 0,
                    timestamp REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statement_claims (
                    claim_id TEXT PRIMARY KEY,
                    suspect_id TEXT NOT NULL,
                    turn_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    entity TEXT,
                    claimed_time TEXT,
                    claimed_location TEXT,
                    claim_type TEXT NOT NULL,
                    is_contradiction INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (turn_id) REFERENCES interrogation_turns(turn_id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_turns_suspect ON interrogation_turns(suspect_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_claims_suspect ON statement_claims(suspect_id)")
            conn.commit()

    def save_turn(self, turn: InterrogationTurn) -> None:
        """Persists an interrogation turn and its extracted claims."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            presented_json = json.dumps(turn.presented_evidence_ids)
            contradictions_json = json.dumps([c.model_dump() for c in turn.contradictions_found])

            cursor.execute(
                """
                INSERT OR REPLACE INTO interrogation_turns 
                (turn_id, suspect_id, question, presented_evidence_json, response, contradictions_json, model_name, is_fallback, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    turn.turn_id,
                    turn.suspect_id,
                    turn.question,
                    presented_json,
                    turn.response,
                    contradictions_json,
                    turn.model_name or "mock",
                    1 if turn.is_fallback else 0,
                    turn.timestamp,
                ),
            )

            for claim in turn.claims:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO statement_claims
                    (claim_id, suspect_id, turn_id, text, entity, claimed_time, claimed_location, claim_type, is_contradiction)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        claim.claim_id,
                        claim.suspect_id,
                        claim.turn_id,
                        claim.text,
                        claim.entity,
                        claim.claimed_time,
                        claim.claimed_location,
                        claim.claim_type,
                        1 if claim.is_contradiction else 0,
                    ),
                )
            conn.commit()

    def get_suspect_turns(self, suspect_id: str) -> List[InterrogationTurn]:
        """Retrieves all historical interrogation turns for a specific suspect."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM interrogation_turns WHERE suspect_id = ? ORDER BY timestamp ASC",
                (suspect_id,),
            )
            rows = cursor.fetchall()
            turns = []
            for r in rows:
                contradictions_raw = json.loads(r["contradictions_json"])
                contradictions = [ContradictionResult.model_validate(c) for c in contradictions_raw]
                turns.append(
                    InterrogationTurn(
                        turn_id=r["turn_id"],
                        suspect_id=r["suspect_id"],
                        question=r["question"],
                        presented_evidence_ids=json.loads(r["presented_evidence_json"]),
                        response=r["response"],
                        claims=self.get_claims_by_turn(r["turn_id"]),
                        contradictions_found=contradictions,
                        model_name=r["model_name"],
                        is_fallback=bool(r["is_fallback"]),
                        timestamp=r["timestamp"],
                    )
                )
            return turns

    def get_all_turns(self) -> List[InterrogationTurn]:
        """Retrieves all turns across all suspects."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM interrogation_turns ORDER BY timestamp ASC")
            rows = cursor.fetchall()
            turns = []
            for r in rows:
                contradictions_raw = json.loads(r["contradictions_json"])
                contradictions = [ContradictionResult.model_validate(c) for c in contradictions_raw]
                turns.append(
                    InterrogationTurn(
                        turn_id=r["turn_id"],
                        suspect_id=r["suspect_id"],
                        question=r["question"],
                        presented_evidence_ids=json.loads(r["presented_evidence_json"]),
                        response=r["response"],
                        claims=self.get_claims_by_turn(r["turn_id"]),
                        contradictions_found=contradictions,
                        model_name=r["model_name"],
                        is_fallback=bool(r["is_fallback"]),
                        timestamp=r["timestamp"],
                    )
                )
            return turns

    def get_claims_by_turn(self, turn_id: str) -> List[StatementClaim]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM statement_claims WHERE turn_id = ?", (turn_id,))
            rows = cursor.fetchall()
            return [
                StatementClaim(
                    claim_id=r["claim_id"],
                    suspect_id=r["suspect_id"],
                    turn_id=r["turn_id"],
                    text=r["text"],
                    entity=r["entity"],
                    claimed_time=r["claimed_time"],
                    claimed_location=r["claimed_location"],
                    claim_type=r["claim_type"],
                    is_contradiction=bool(r["is_contradiction"]),
                )
                for r in rows
            ]

    def get_claims_by_suspect(self, suspect_id: str) -> List[StatementClaim]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM statement_claims WHERE suspect_id = ?", (suspect_id,))
            rows = cursor.fetchall()
            return [
                StatementClaim(
                    claim_id=r["claim_id"],
                    suspect_id=r["suspect_id"],
                    turn_id=r["turn_id"],
                    text=r["text"],
                    entity=r["entity"],
                    claimed_time=r["claimed_time"],
                    claimed_location=r["claimed_location"],
                    claim_type=r["claim_type"],
                    is_contradiction=bool(r["is_contradiction"]),
                )
                for r in rows
            ]

    def get_all_claims(self) -> List[StatementClaim]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM statement_claims")
            rows = cursor.fetchall()
            return [
                StatementClaim(
                    claim_id=r["claim_id"],
                    suspect_id=r["suspect_id"],
                    turn_id=r["turn_id"],
                    text=r["text"],
                    entity=r["entity"],
                    claimed_time=r["claimed_time"],
                    claimed_location=r["claimed_location"],
                    claim_type=r["claim_type"],
                    is_contradiction=bool(r["is_contradiction"]),
                )
                for r in rows
            ]

    def get_formatted_dialogue_context(self, suspect_id: str, limit: int = 5) -> str:
        """Formats the last N turns with this suspect as dialogue history for prompt injection."""
        turns = self.get_suspect_turns(suspect_id)
        if not turns:
            return "No previous interrogation history with this suspect."

        recent = turns[-limit:]
        history_lines = []
        for i, t in enumerate(recent, 1):
            history_lines.append(f"Turn {i}:")
            history_lines.append(f"Detective: {t.question}")
            if t.presented_evidence_ids:
                history_lines.append(f"[Presented Clues: {', '.join(t.presented_evidence_ids)}]")
            history_lines.append(f"Suspect Response: {t.response}")
        return "\n".join(history_lines)

    def clear(self) -> None:
        """Wipes all saved turns and claims."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM statement_claims")
            cursor.execute("DELETE FROM interrogation_turns")
            conn.commit()
