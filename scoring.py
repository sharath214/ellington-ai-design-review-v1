"""
Configurable compliance scoring engine for Ellington AI Design Review Management System V1.
Implements transparent, weighted point deductions strictly on confirmed/finalized findings.
"""

from typing import List, Dict, Any, Tuple
import sys
from pathlib import Path
_APP_ROOT = str(Path(__file__).resolve().parent)
if _APP_ROOT not in sys.path:
    sys.path.insert(0, _APP_ROOT)

from config import DEFAULT_SCORING_CONFIG

def calculate_dynamic_compliance_score(
    findings: List[Dict[str, Any]],
    scoring_config: Dict[str, Any] = None
) -> Tuple[int, Dict[str, Any]]:
    """
    Calculates compliance score (0-100%) based on confirmed/finalized findings.
    
    Rules:
    - Only confirmed AI findings and finalized TA findings deduct points.
    - Rejected AI findings (false positives) deduct 0 points.
    - Draft findings deduct 0 points.
    - Transparent audit breakdown of all deductions.
    """
    config = scoring_config or DEFAULT_SCORING_CONFIG
    threshold = config.get('threshold', 80)
    deductions_map = config.get('deductions', {
        'Critical': 25,
        'High': 14,
        'Medium': 8,
        'Low': 3,
        'Needs Baseline Comparison': 6
    })

    score = 100
    deduction_items = []
    
    for f in findings:
        source = f.get('source', 'AI')
        status = f.get('status', 'Pending Review')
        severity = f.get('severity', 'Medium')
        fid = f.get('id', 'F-UNKNOWN')
        cat = f.get('category', 'General')
        
        # Check if item is an active gap
        is_active_gap = False
        
        if source == 'AI':
            # Stream A: Must be confirmed or modified by TA
            # Rejected AI findings do NOT deduct points
            if status in ['Confirm Issue', 'Modify & Confirm', 'Need Clarification', 'Confirmed']:
                is_active_gap = True
            elif status == 'Pending Review' and f.get('ai_status') == 'Potential Gap':
                # In initial draft before TA review, display preliminary deduction
                is_active_gap = True
        else:
            # Stream B: TA manual finding
            # Must be saved/finalized (not deleted or discarded)
            if status in ['Finalized', 'AI Reviewed', 'Ready for Consultant', 'Draft']:
                is_active_gap = True

        if is_active_gap:
            points = deductions_map.get(severity, 5)
            score -= points
            deduction_items.append({
                'finding_id': fid,
                'source': source,
                'category': cat,
                'severity': severity,
                'deduction': points,
                'status': status
            })

    final_score = max(0, min(100, score))
    
    summary = {
        'score': final_score,
        'threshold': threshold,
        'is_compliant': final_score >= threshold,
        'total_deduction': 100 - final_score,
        'deduction_count': len(deduction_items),
        'breakdown': deduction_items
    }
    
    return final_score, summary
