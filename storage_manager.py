"""
Storage manager and persistence layer for Ellington AI Design Review Management System V1.
Handles JSON persistence for Stage History, Immutable Audit Trail, Review Cycles, Attachment Storage,
and Ellington-formatted Comments Tracker HTML/CSV exports matching the client's spreadsheet.
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
    finding_id: str = "-",
    review_cycle: str = "Cycle 1",
    previous_value: str = "-",
    new_value: str = "-",
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
    events.insert(0, event)
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
    issued_by: str = "Technical Architect",
    submittal_text: str = "",
    submittal_filename: str = ""
) -> Dict[str, Any]:
    cycles = load_review_cycles()
    cycle_id = f"CYCLE-{cycle_num}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if not submittal_text:
        sample_path = BASE_DIR / "sample_schematic_arch.txt"
        if sample_path.exists():
            submittal_text = sample_path.read_text(encoding='utf-8')
            submittal_filename = submittal_filename or "015-24_Bukadra_Plot_6117262_Schematic_Architecture_V1.txt"

    consultant_items = []
    for item in finalized_findings:
        raw_atts = item.get('attachments', [])
        cons_atts = [
            att for att in raw_atts 
            if att.get('visibility') == 'Consultant Visible'
        ]
        
        source_label = "Design Review Finding" if item.get('source') == 'AI' else "Technical Architect Comment"
        
        # Action Key logic (Ellington spreadsheet standard)
        sev = item.get('severity', 'Medium')
        action_code = "1" if sev in ['Critical', 'High'] else ("2" if sev == 'Medium' else "3")
        action_label = "1 - OPEN (Correction required before acceptance)" if action_code == "1" else ("2 - PENDING (Resolve during next design stage)" if action_code == "2" else "3 - CLOSED (Record comment / Accepted)")

        consultant_items.append({
            'finding_id': item['id'],
            'drawing_ref': item.get('drawing_ref', 'AR-GENERAL'),
            'discipline': item.get('discipline', discipline),
            'category': item.get('category', 'General Compliance'),
            'reference_source': item.get('reference_source', 'Authority / DCR'),
            'clause': item.get('clause', '-'),
            'severity': sev,
            'action_key': action_label,
            'action_code': action_code,
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
        'submittal_filename': submittal_filename or "Submittal_Drawing_Package_V1.txt",
        'submittal_text': submittal_text,
        'issued_at': now_str,
        'issued_by': issued_by,
        'is_locked': True,
        'compliance_score': compliance_score,
        'total_findings': len(finalized_findings),
        'frozen_findings_internal': finalized_findings,
        'consultant_package': consultant_items,
        'status': 'Issued to Consultant'
    }
    
    existing_idx = next(
        (i for i, c in enumerate(cycles) if c.get('project') == project and c.get('stage') == stage and c.get('cycle_id') == cycle_id),
        None
    )
    if existing_idx is not None:
        cycles[existing_idx] = cycle_record
    else:
        cycles.append(cycle_record)
        
    save_review_cycles(cycles)
    
    log_audit_event(
        action=f"Review Cycle {cycle_num} Finalized & Issued",
        user=issued_by,
        role="Technical Architect",
        review_cycle=cycle_id,
        previous_value="Draft Review Package",
        new_value=f"Locked Package ({len(consultant_items)} Items Issued)",
        details=f"Compliance Score: {compliance_score}%. Review cycle frozen against silent edits."
    )
    
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

# ---------------------------------------------------------
# Ellington Spreadsheet-Formatted Comments Tracker HTML Export
# ---------------------------------------------------------
def build_ellington_spreadsheet_tracker_html(cycle_rec: Dict[str, Any]) -> str:
    """
    Renders an HTML export that directly mirrors Ellington Properties'
    official Design Review / Comment Tracker Excel spreadsheet.
    """
    items = cycle_rec.get('consultant_package', [])
    now_date = datetime.now().strftime('%d.%m.%Y')

    rows_html = ""
    for idx, it in enumerate(items):
        act_code = it.get('action_code', '1')
        if act_code == "1":
            act_badge = "<span style='background:#DC2626; color:white; padding:4px 10px; border-radius:4px; font-weight:bold;'>1</span>"
        elif act_code == "2":
            act_badge = "<span style='background:#F59E0B; color:white; padding:4px 10px; border-radius:4px; font-weight:bold;'>2</span>"
        else:
            act_badge = "<span style='background:#10B981; color:white; padding:4px 10px; border-radius:4px; font-weight:bold;'>3</span>"

        resp_obj = it.get('response', {})
        resp_note = resp_obj.get('response_note', 'Pending consultant review.')
        rev_dwg = resp_obj.get('revised_drawing_ref', '')

        rows_html += f"""
        <tr>
            <td style='text-align:center; font-weight:bold;'>{idx+1}</td>
            <td style='font-weight:600;'>{it.get('discipline', 'Architecture')}</td>
            <td><b>{it.get('category', 'General')}</b><br><small style='color:#64748B;'>{it.get('finding_id', '')}</small></td>
            <td style='font-family:monospace; font-size:11px;'>{it.get('drawing_ref', 'AR-GENERAL')}</td>
            <td>
                <div style='color:#0F172A; margin-bottom:4px;'>{it.get('comment', '')}</div>
                <div style='font-size:11px; color:#0369A1;'><b>Authority / Clause:</b> {it.get('clause', '-')} ({it.get('reference_source', '')})</div>
            </td>
            <td style='text-align:center;'>{act_badge}</td>
            <td style='background:#FAF5FF;'>
                <div style='color:#4C1D95; font-size:12px;'><b>{resp_note}</b></div>
                {f"<div style='font-size:11px; color:#6B21A8; margin-top:2px;'>Revised Sheet: <code>{rev_dwg}</code></div>" if rev_dwg else ""}
            </td>
        </tr>
        """

    return f"""<!doctype html>
<html>
<head>
<meta charset='utf-8'>
<title>Ellington Properties - Design Review Comments Tracker</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 30px; color: #0F172A; background: #F8FAFC; }}
    .header-box {{ background: #0A192F; color: white; padding: 20px 24px; border-radius: 8px; border-bottom: 4px solid #D4AF37; display: flex; justify-content: space-between; align-items: center; }}
    .meta-table {{ width: 100%; border-collapse: collapse; margin-top: 16px; background: white; border: 1px solid #CBD5E1; border-radius: 6px; overflow: hidden; }}
    .meta-table td {{ padding: 8px 12px; border: 1px solid #E2E8F0; font-size: 12px; }}
    .meta-label {{ background: #F1F5F9; color: #475569; font-weight: 700; width: 18%; text-transform: uppercase; font-size: 11px; }}
    .legend-box {{ background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 12px 16px; margin: 16px 0; display: flex; gap: 20px; align-items: center; font-size: 12px; }}
    .table-main {{ width: 100%; border-collapse: collapse; margin-top: 14px; background: white; border-radius: 6px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
    .table-main th {{ background: #0B315E; color: white; padding: 10px 12px; font-size: 11px; text-transform: uppercase; border: 1px solid #0E2A47; text-align: left; }}
    .table-main td {{ padding: 10px 12px; border: 1px solid #E2E8F0; font-size: 12px; vertical-align: top; }}
</style>
</head>
<body>
<div class='header-box'>
    <div>
        <h1 style='margin:0; font-size:22px; color:#FFFFFF;'>ELLINGTON PROPERTIES</h1>
        <p style='margin:4px 0 0 0; color:#D4AF37; font-size:13px; font-weight:600;'>AI Design Review Management System - Official Comment Tracker</p>
    </div>
    <div style='text-align:right; font-size:12px; color:#94A3B8;'>
        <div><b>Review Cycle:</b> <span style='color:#FFFFFF;'>{cycle_rec.get('cycle_id', 'CYCLE-1')}</span></div>
        <div><b>Issued Date:</b> {cycle_rec.get('issued_at', now_date)}</div>
    </div>
</div>

<table class='meta-table'>
    <tr>
        <td class='meta-label'>Project Name:</td><td><b>{cycle_rec.get('project', 'Ellington Bukadra Tower')}</b></td>
        <td class='meta-label'>Lead Consultant:</td><td><b>Lead Architectural & Engineering Consultant</b></td>
    </tr>
    <tr>
        <td class='meta-label'>Design Stage:</td><td><b>{cycle_rec.get('stage', 'Schematic Design')}</b></td>
        <td class='meta-label'>Discipline:</td><td><b>{cycle_rec.get('discipline', 'Architecture & Planning')}</b></td>
    </tr>
    <tr>
        <td class='meta-label'>Submission Ref:</td><td><b>{cycle_rec.get('submittal_version', 'V1.0')}</b> ({cycle_rec.get('submittal_filename', '')})</td>
        <td class='meta-label'>Reviewer / Auth:</td><td><b>{cycle_rec.get('issued_by', 'Technical Architect')}</b></td>
    </tr>
</table>

<div class='legend-box'>
    <b>Action Key:</b>
    <div><span style='background:#DC2626; color:white; padding:3px 8px; border-radius:4px; font-weight:bold; font-size:11px;'>1 - OPEN</span> Requires response and/or correction before acceptance</div>
    <div><span style='background:#F59E0B; color:white; padding:3px 8px; border-radius:4px; font-weight:bold; font-size:11px;'>2 - PENDING</span> Requires response during next design stage</div>
    <div><span style='background:#10B981; color:white; padding:3px 8px; border-radius:4px; font-weight:bold; font-size:11px;'>3 - CLOSED</span> Record comment - accepted as noted</div>
</div>

<table class='table-main'>
    <thead>
        <tr>
            <th style='width:3%; text-align:center;'>No.</th>
            <th style='width:12%;'>Discipline</th>
            <th style='width:15%;'>Category / Submittal Item</th>
            <th style='width:12%;'>Drawing Ref</th>
            <th style='width:32%;'>Review Comments Details & Applicable Clause</th>
            <th style='width:6%; text-align:center;'>Action</th>
            <th style='width:20%;'>Consultant Response (Date-Stamped)</th>
        </tr>
    </thead>
    <tbody>
        {rows_html}
    </tbody>
</table>
</body>
</html>"""

# ---------------------------------------------------------
# Project Data Reset / Start Fresh
# ---------------------------------------------------------
def clear_all_project_data(keep_audit_init: bool = True) -> None:
    """Clears all review cycles, stage history records, and audit events so the user can start fresh with a new project."""
    save_review_cycles([])
    save_stage_history([])
    if keep_audit_init:
        init_event = [{
            'event_id': f"EVT-{uuid.uuid4().hex[:8].upper()}",
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'user': "Technical Architect",
            'role': "Technical Architect",
            'action': "Workspace Reset / Cleared",
            'finding_id': "-",
            'review_cycle': "Cycle 1",
            'previous_value': "All Previous Projects",
            'new_value': "Clean Workspace",
            'details': "All previous project records, review cycles, and stage history were cleared to start fresh."
        }]
        save_audit_trail(init_event)
    else:
        save_audit_trail([])
        
    if UPLOADS_DIR.exists():
        for item in UPLOADS_DIR.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception:
                pass

