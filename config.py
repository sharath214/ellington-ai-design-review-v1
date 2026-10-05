"""
Configuration and constants for Ellington AI Design Review Management System V1.
Centralized scoring weights, role permissions, stage workflows, and UI tokens.
Incorporates Ellington Properties' official 3-Tier Action Key & review standards.
"""

from typing import Dict, Any

# ---------------------------------------------------------
# User Roles & Permissions
# ---------------------------------------------------------
ROLE_TECHNICAL_ARCHITECT = "Technical Architect"
ROLE_CONSULTANT = "Lead Design Consultant"

ROLES = [ROLE_TECHNICAL_ARCHITECT, ROLE_CONSULTANT]

ROLE_DESCRIPTIONS = {
    ROLE_TECHNICAL_ARCHITECT: "Authorizing Design Authority: Reviews AI findings, authors manual findings, requests AI validation, locks & issues review packages, approves stages.",
    ROLE_CONSULTANT: "External Design Team: Reviews issued comments, submits responses/contestations, and submits revised drawing packages (V2.0+)."
}

# ---------------------------------------------------------
# Ellington Official Action Key & Status Model (Spreadsheet Standard)
# ---------------------------------------------------------
ACTION_KEY_1_OPEN = "1 - OPEN (Correction required before acceptance)"
ACTION_KEY_2_PENDING = "2 - PENDING (Resolve during next design stage)"
ACTION_KEY_3_CLOSED = "3 - CLOSED (Record comment / Accepted)"

ELLINGTON_ACTION_KEYS = [
    ACTION_KEY_1_OPEN,
    ACTION_KEY_2_PENDING,
    ACTION_KEY_3_CLOSED
]

ACTION_KEY_COLORS = {
    ACTION_KEY_1_OPEN: {"bg": "#FEF2F2", "fg": "#991B1B", "border": "#EF4444", "short": "1 - OPEN"},
    ACTION_KEY_2_PENDING: {"bg": "#FFFBEB", "fg": "#92400E", "border": "#F59E0B", "short": "2 - PENDING"},
    ACTION_KEY_3_CLOSED: {"bg": "#F0FDF4", "fg": "#065F46", "border": "#10B981", "short": "3 - CLOSED"}
}

# ---------------------------------------------------------
# Design Stage Definitions
# ---------------------------------------------------------
STAGE_ORDER = [
    'Concept Design',
    'Schematic Design',
    'Detailed Design',
    'Tender Package'
]

STAGE_STATUSES = [
    'Not Started',
    'Submission Received',
    'AI Review Complete',
    'Technical Architect Review',
    'Human Findings Under AI Review',
    'Final Review',
    'Review Finalized',
    'Issued to Consultant',
    'Consultant Response Received',
    'Resubmission Received',
    'Delta Review',
    'Final Human Review',
    'Completed',
    'Completed with Outstanding Items'
]

# ---------------------------------------------------------
# Central Configurable Compliance Scoring Model
# ---------------------------------------------------------
DEFAULT_SCORING_CONFIG: Dict[str, Any] = {
    'threshold': 80,
    'deductions': {
        'Critical': 25,
        'High': 14,
        'Medium': 8,
        'Low': 3,
        'Needs Baseline Comparison': 6
    }
}

# ---------------------------------------------------------
# Attachment Types & Visibility
# ---------------------------------------------------------
ATTACHMENT_TYPES = [
    "Reference Document",
    "Screenshot",
    "Drawing Excerpt",
    "Hand-drawn Sketch",
    "Marked-up Drawing"
]

VISIBILITY_INTERNAL_ONLY = "Internal Only"
VISIBILITY_CONSULTANT_VISIBLE = "Consultant Visible"

ATTACHMENT_VISIBILITY_OPTIONS = [
    VISIBILITY_INTERNAL_ONLY,
    VISIBILITY_CONSULTANT_VISIBLE
]

# ---------------------------------------------------------
# Finding Categories & Severities
# ---------------------------------------------------------
FINDING_CATEGORIES = [
    "Design Judgment / Technical Architect Observation",
    "Boundary Setbacks",
    "Plot Coverage & Footprint",
    "Building Height & Storeys",
    "FAR / GFA Compliance",
    "Fire & Life Safety Egress",
    "Staircase Pressurization & Fire Doors",
    "Parking Ratios & Allocation",
    "Accessibility & Universal Design",
    "DEWA Substation & Clearances",
    "Thermal Performance & Glazing",
    "Signature Arrival & Double-Height Lobby",
    "Signature Material Palette & Façade",
    "Balcony Depth & Outdoor Living",
    "Resort-Style Amenities & Pool Deck",
    "External Staircase / Landscape Consistency",
    "Column Grid & Transfer Alignment",
    "Acoustic Partition & Noise Criteria",
    "MEP Shaft & Ceiling Void Coordination",
    "Spatial Circulation & User Experience"
]

SEVERITIES = ["Critical", "High", "Medium", "Low", "Info"]

# ---------------------------------------------------------
# Reviewer Decisions on Stream A (AI Findings)
# ---------------------------------------------------------
TA_AI_DECISIONS = [
    "Pending Review",
    "Confirm Issue",
    "Reject as False Positive",
    "Modify & Confirm",
    "Need Clarification"
]

# ---------------------------------------------------------
# Consultant Action Responses
# ---------------------------------------------------------
CONSULTANT_RESPONSE_OPTIONS = [
    "Pending Response",
    "Accept / Will Rectify",
    "Clarification Requested",
    "Contest Finding",
    "Exception Requested"
]

# ---------------------------------------------------------
# Delta Review Proposed Statuses
# ---------------------------------------------------------
DELTA_STATUS_RESOLVED = "Resolved"
DELTA_STATUS_PARTIAL = "Partially Resolved"
DELTA_STATUS_OPEN = "Still Open"
DELTA_STATUS_CLARIFY = "Clarification Required"
DELTA_STATUS_NEW = "New Issue Detected"
