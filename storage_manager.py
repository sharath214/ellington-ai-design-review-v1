"""
Storage manager and persistence layer for Ellington AI Design Review Management System V1.
Handles JSON persistence for Stage History, Immutable Audit Trail, Review Cycles, and Attachment Storage.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import shutil
import uuid

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR
STAGE_HISTORY_FILE = DATA_DIR / 'stage_history.json'
AUDIT_TRAIL_FILE = DATA_DIR / 'audit_trail.json'
REVIEW_CYCLES_FILE = DATA_DIR / 'review_cycles.json'
UPLOADS_DIR = DATA_DIR / 'uploads'
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# Audit Trail Persistence
# ---------------------------------------------------------
def load_audit_trail() -> List[Dict[str, Any]]:
    if not AUDIT_TRAIL_FILE.exists():
        return []
    try:
        data = json.loads(AUDIT_TRAIL_FILE.read_text(encoding='utf-8'))
        return data if isinstance(data, list) else []
    except Exception:
        return []

def save_audit_trail(events: List[Dict[str, Any]]) -> None:
    try:
        AUDIT_TRAIL_FILE.write_text(json.dumps(events, indent=2), encoding='utf-8')
    except Exception as e:
        print(f"Error saving audit trail: {e}")

def log_audit_event(
    action: str,
    user: str = "Technical Architect",
    role: str = "Technical Architect",
    finding_id: str = "—",
    review_cycle: str = "Cycle 1",
    previous_value: str = "—",
    new_value: str = "—",
    details: str = ""
) -> Dict[str, Any]:
    events = load_audit_trail()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    event = {
        'event_id': f"EVT-{uuid.uuid4().hex[:8].upper()}",
        'timestamp': now_str,
        'user': user,
        'role': role,
        'action': action,
        'finding_id': finding_id,
        'review_cycle': review_cycle,
        'previous_value': str(previous_value),
        'new_value': str(new_value),
        'details': details
    }
    events.insert(0, event)  # newest first
    save_audit_trail(events)
    return event

# ---------------------------------------------------------
# Stage History Persistence
# ---------------------------------------------------------
def load_stage_history() -> List[Dict[str, Any]]:
    if not STAGE_HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(STAGE_HISTORY_FILE.read_text(encoding='utf-8'))
        return data if isinstance(data, list) else []
    except Exception:
        return []

def save_stage_history(records: List[Dict[str, Any]]) -> None:
    try:
        STAGE_HISTORY_FILE.write_text(json.dumps(records, indent=2), encoding='utf-8')
    except Exception as e:
        print(f"Error saving stage history: {e}")

def upsert_stage_status(
    project: str,
    stage: str,
    discipline: str,
    status: str,
    reviewer: str = "",
    note: str = "",
    review_cycle: str = "Cycle 1",
    compliance_score: Optional[int] = None,
    consultant_data: Optional[List[Dict[str, Any]]] = None,
    deferred_items: Optional[List[str]] = None
) -> None:
    records = load_stage_history()
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    match = None
    for rec in records:
        if rec.get('project') == project and rec.get('stage') == stage:
            match = rec
            break
            
    if match is None:
        match = {
            'project': project,
            'stage': stage,
            'discipline': discipline,
            'status': status,
            'reviewer': reviewer,
            'note': note,
            'review_cycle': review_cycle,
            'compliance_score': compliance_score if compliance_score is not None else 100,
            'updated_at': now,
            'completed_at': now if status.startswith('Completed') else '',
            'consultant_items': consultant_data or [],
            'deferred_items': deferred_items or []
        }
        records.append(match)
    else:
        match['status'] = status
        match['stage'] = stage
        match['discipline'] = discipline or match.get('discipline', '')
        match['reviewer'] = reviewer or match.get('reviewer', '')
        match['note'] = note or match.get('note', '')
        match['review_cycle'] = review_cycle or match.get('review_cycle', 'Cycle 1')
        if compliance_score is not None:
            match['compliance_score'] = compliance_score
        match['updated_at'] = now
        if status.startswith('Completed'):
            match['completed_at'] = now
        if consultant_data is not None:
            match['consultant_items'] = consultant_data
        if deferred_items is not None:
            match['deferred_items'] = deferred_items
            
    save_stage_history(records)

# ---------------------------------------------------------
# Review Cycles & Point-in-Time Freezing
# ---------------------------------------------------------
def load_review_cycles() -> List[Dict[str, Any]]:
    if not REVIEW_CYCLES_FILE.exists():
        return []
    try:
        data = json.loads(REVIEW_CYCLES_FILE.read_text(encoding='utf-8'))
        return data if isinstance(data, list) else []
    except Exception:
        return []

def save_review_cycles(cycles: List[Dict[str, Any]]) -> None:
    try:
        REVIEW_CYCLES_FILE.write_text(json.dumps(cycles, indent=2), encoding='utf-8')
    except Exception as e:
        print(f"Error saving review cycles: {e}")

def get_active_or_latest_cycle(project: str, stage: str) -> Optional[Dict[str, Any]]:
    cycles = load_review_cycles()
    matching = [c for c in cycles if c.get('project') == project and c.get('stage') == stage]
    if not matching:
        return None
    return matching[-1]

def lock_and_issue_cycle_package(
    project: str,
    stage: str,
    discipline: str,
    cycle_num: int,
    submittal_version: str,
    finalized_findings: List[Dict[str, Any]],
    compliance_score: int,
    issued_by: str = "Technical Architect"
) -> Dict[str, Any]:
    """
    Creates an immutable frozen snapshot of the review cycle.
    Separates internal audit data from consultant-visible payload.
    """
    cycles = load_review_cycles()
    cycle_id = f"CYCLE-{cycle_num}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Filter and format consultant visible items
    consultant_items = []
    for item in finalized_findings:
        # Filter attachments to consultant visible only
        raw_atts = item.get('attachments', [])
        cons_atts = [
            att for att in raw_atts 
            if att.get('visibility') == 'Consultant Visible'
        ]
        
        # Consultant-facing origin display
        source_label = "Design Review Finding" if item.get('source') == 'AI' else "Technical Architect Comment"
        
        consultant_items.append({
            'finding_id': item['id'],
            'drawing_ref': item.get('drawing_ref', 'AR-GENERAL'),
            'discipline': item.get('discipline', discipline),
            'category': item.get('category', 'General Compliance'),
            'reference_source': item.get('reference_source', 'Authority / DCR'),
            'clause': item.get('clause', '—'),
            'severity': item.get('severity', 'Medium'),
            'comment': item.get('consultant_comment') or item.get('finding_text', ''),
            'source_display': source_label,
            'source_internal': item.get('source', 'AI'),
            'attachments': cons_atts,
            'status': 'Issued - Action Required',
            'response': {
                'response_type': 'Pending Response',
                'response_note': '',
                'revised_drawing_ref': '',
                'attachments': []
            }
        })

    cycle_record = {
        'cycle_id': cycle_id,
        'cycle_number': cycle_num,
        'project': project,
        'stage': stage,
        'discipline': discipline,
        'submittal_version': submittal_version,
        'issued_at': now_str,
        'issued_by': issued_by,
        'is_locked': True,
        'compliance_score': compliance_score,
        'total_findings': len(finalized_findings),
        'frozen_findings_internal': finalized_findings,
        'consultant_package': consultant_items,
        'status': 'Issued to Consultant'
    }
    
    # Update or append cycle
    existing_idx = next(
        (i for i, c in enumerate(cycles) if c.get('project') == project and c.get('stage') == stage and c.get('cycle_id') == cycle_id),
        None
    )
    if existing_idx is not None:
        cycles[existing_idx] = cycle_record
    else:
        cycles.append(cycle_record)
        
    save_review_cycles(cycles)
    
    # Log audit event
    log_audit_event(
        action=f"Review Cycle {cycle_num} Finalized & Issued",
        user=issued_by,
        role="Technical Architect",
        review_cycle=cycle_id,
        previous_value="Draft Review Package",
        new_value=f"Locked Package ({len(consultant_items)} Items Issued)",
        details=f"Compliance Score: {compliance_score}%. Review cycle frozen against silent edits."
    )
    
    # Update stage status
    upsert_stage_status(
        project=project,
        stage=stage,
        discipline=discipline,
        status='Issued to Consultant',
        reviewer=issued_by,
        review_cycle=cycle_id,
        compliance_score=compliance_score,
        consultant_data=consultant_items
    )
    
    return cycle_record

# ---------------------------------------------------------
# Attachment Storage Handler
# ---------------------------------------------------------
def save_uploaded_file(uploaded_file, category: str, visibility: str, uploaded_by: str = "Technical Architect") -> Dict[str, Any]:
    att_id = f"ATT-{uuid.uuid4().hex[:8].upper()}"
    filename = uploaded_file.name
    dest_path = UPLOADS_DIR / f"{att_id}_{filename}"
    
    content = uploaded_file.read()
    uploaded_file.seek(0)
    dest_path.write_bytes(content)
    
    size_kb = len(content) / 1024
    size_display = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{(size_kb/1024):.2f} MB"
    
    att = {
        'id': att_id,
        'filename': filename,
        'file_type': category,
        'stored_path': str(dest_path),
        'uploaded_by': uploaded_by,
        'uploaded_role': "Technical Architect" if "Architect" in uploaded_by else "Consultant",
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'visibility': visibility,
        'size_display': size_display
    }
    return att
