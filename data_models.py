"""
Data models and entity schemas for Ellington AI Design Review Management System V1.
Provides typed definitions for Findings, Attachments, Review Cycles, Consultant Responses, and Audit Events.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

@dataclass
class FindingAttachment:
    id: str = field(default_factory=lambda: f"ATT-{uuid.uuid4().hex[:8].upper()}")
    filename: str = ""
    file_type: str = "Drawing Excerpt"  # Reference Document, Screenshot, Drawing Excerpt, Hand-drawn Sketch, Marked-up Drawing
    stored_path: str = ""
    uploaded_by: str = "Technical Architect"
    uploaded_role: str = "Technical Architect"
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    visibility: str = "Consultant Visible"  # Internal Only or Consultant Visible
    file_size_display: str = "0 KB"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FindingAttachment":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AIReviewFeedback:
    has_feedback: bool = False
    reference_validation: str = ""      # e.g., "Potentially related to DCR Clause 4.2."
    evidence_check: str = ""            # e.g., "The submitted drawing shows approximately 4.5m vs 6.0m required."
    duplicate_detection: str = ""       # e.g., "No duplicate found" or "Similar to DCR-SETBACK-001"
    is_duplicate: bool = False
    duplicate_of_id: str = ""
    missing_information: str = ""       # e.g., "Finding references fire-doors, but no schedule included."
    contradiction_detection: str = ""   # e.g., "Sheet A-102 already includes a parking schedule."
    suggested_severity: str = ""        # e.g., "High"
    suggested_consultant_wording: str = "" # Formal contractual wording
    classification: str = "Technical Architect Observation"
    confidence: str = "88%"
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIReviewFeedback":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class BaseFinding:
    id: str
    source: str = "AI"                 # "AI" or "Technical Architect"
    drawing_ref: str = "AR-GENERAL"
    discipline: str = "Architecture & Planning"
    category: str = "General Compliance"
    location_area: str = ""            # Optional: Drawing Area / Zone
    page_sheet_num: str = ""           # Optional: Sheet / Page
    reference_source: str = ""         # Authority or DCR (optional for subjective comments)
    clause: str = ""                   # Clause number (optional for subjective comments)
    finding_text: str = ""             # The actual finding/issue description
    evidence_text: str = ""            # Evidence found or missing
    severity: str = "Medium"           # Critical, High, Medium, Low, Info
    ai_confidence: str = "—"           # e.g. "94%" for AI, "—" for manual until AI review
    consultant_comment: str = ""       # Consultant-facing action required
    internal_note: str = ""            # Private note for Ellington team
    recommended_action: str = ""
    status: str = "Pending Review"     # Stream A: Pending Review, Confirm Issue, Reject as False Positive, Modify & Confirm, Need Clarification
                                       # Stream B: Draft, Pending AI Review, AI Reviewed, Finalized
    is_finalized_for_issue: bool = False
    cost_delta: float = 0.0
    schedule_delta: str = "0 wks"
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    ai_feedback: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    updated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseFinding":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ConsultantResponseItem:
    finding_id: str
    response_type: str = "Pending Response"  # Accept / Will Rectify, Clarification Requested, Contest Finding, Exception Requested
    response_note: str = ""
    revised_drawing_ref: str = ""
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    responded_by: str = "Lead Design Consultant"
    responded_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditEvent:
    event_id: str = field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:8].upper()}")
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    user: str = "Technical Architect"
    role: str = "Technical Architect"
    action: str = ""
    finding_id: str = "—"
    review_cycle: str = "Cycle 1"
    previous_value: str = "—"
    new_value: str = "—"
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
