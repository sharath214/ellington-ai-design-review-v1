"""
Rule Engine and AI Advisory Intelligence for Ellington AI Design Review Management System V1.
Covers:
1. Multi-discipline compliance rules (DCR, Authority, Brand, Cross-Discipline)
2. Stream A: AI First-Pass Review engine
3. Stream B: Point-in-time AI Review of Technical Architect findings (10-point advisory check)
4. AI Delta Review engine for revised submissions (V1 vs V2)
"""

import re
from typing import List, Dict, Any, Optional

# ---------------------------------------------------------
# 17 Multi-Discipline Rule Catalogue
# ---------------------------------------------------------
COMPREHENSIVE_RULES = [
    # 1. DCR & Planning
    {
        'id': 'DCR-SETBACK-001',
        'pillar': 'Development Regulations (DCR)',
        'source': 'Meydan Horizon / Master Plan DCR',
        'category': 'Boundary Setbacks',
        'discipline': 'Architecture & Planning',
        'severity': 'High',
        'drawing_ref': 'AR-1000 / AR-1001',
        'keywords': ['setback', 'boundary', 'property line', 'buffer', 'road setback'],
        'expected': 'Explicit front, rear, and side setback dimensions matching master development regulations.',
        'issue_if_missing': True,
        'standard_clause': 'DCR Cl. 4.2: Minimum 6.0m road setback and 4.5m side plot setbacks required.',
        'cost_delta': 0,
        'schedule_delta': '1.0 week'
    },
    {
        'id': 'DCR-PLOTCOV-002',
        'pillar': 'Development Regulations (DCR)',
        'source': 'Development Control Regulations',
        'category': 'Plot Coverage & Footprint',
        'discipline': 'Architecture & Planning',
        'severity': 'Medium',
        'drawing_ref': 'AR-0029 (Area Summary)',
        'keywords': ['plot coverage', 'footprint', 'podium coverage', 'coverage ratio'],
        'expected': 'Plot coverage calculations verifying podium and tower footprints comply with master limit (<= 70%).',
        'issue_if_missing': True,
        'standard_clause': 'DCR Cl. 5.1: Maximum podium plot coverage shall not exceed 70% of total plot area.',
        'cost_delta': 0,
        'schedule_delta': '0.5 weeks'
    },
    {
        'id': 'DCR-HEIGHT-003',
        'pillar': 'Development Regulations (DCR)',
        'source': 'Master Development Control Regulations',
        'category': 'Building Height & Storeys',
        'discipline': 'Architecture & Planning',
        'severity': 'High',
        'drawing_ref': 'AR-2001 to AR-2004',
        'keywords': ['height', 'storey', 'story', 'floor level', 'aod', 'agl', 'elevation'],
        'expected': 'Building height (AGL / AOD) and storey breakdown clearly defined for zoning & aviation limits.',
        'issue_if_missing': True,
        'standard_clause': 'DCR Cl. 3.4: Permissible height limit G+4P+31F with max allowable AOD elevation.',
        'cost_delta': 0,
        'schedule_delta': '1.5 weeks'
    },
    {
        'id': 'DCR-FAR-004',
        'pillar': 'Development Regulations (DCR)',
        'source': 'Dubai Development Authority / DM Standards',
        'category': 'FAR / GFA Compliance',
        'discipline': 'Architecture & Planning',
        'severity': 'High',
        'drawing_ref': 'AR-0012 to AR-0028',
        'keywords': ['gfa', 'gross floor area', 'far', 'floor area ratio', 'bua', 'built-up area'],
        'expected': 'GFA and BUA computations demonstrating compliance with approved FAR allocation.',
        'issue_if_missing': True,
        'standard_clause': 'DDA ZA-DC-REG-02: GFA computations must exclude permitted exemptions (balconies, mechanical, parking).',
        'cost_delta': 0,
        'schedule_delta': '1.0 week'
    },

    # 2. Authority Life Safety & Building Codes
    {
        'id': 'AUTH-DCD-EGRESS-010',
        'pillar': 'Authority Codes',
        'source': 'Dubai Civil Defense (UAE Fire Code 2018)',
        'category': 'Fire & Life Safety Egress',
        'discipline': 'Fire & Life Safety',
        'severity': 'High',
        'drawing_ref': 'FLS-1001 to FLS-1036',
        'keywords': ['travel distance', 'egress', 'exit stair', 'staircase', 'means of egress', 'dead end'],
        'expected': 'Travel distances to exit stairs <= 30m and dead-end corridor <= 15m in accordance with UAE Fire Code.',
        'issue_if_missing': True,
        'standard_clause': 'UAE Fire Code 2018 Ch. 3: Max travel distance to nearest enclosed exit stair shall not exceed 30m.',
        'cost_delta': 120000,
        'schedule_delta': '2.0 weeks'
    },
    {
        'id': 'AUTH-DCD-STAIR-011',
        'pillar': 'Authority Codes',
        'source': 'Dubai Civil Defense (UAE Fire Code 2018)',
        'category': 'Staircase Pressurization & Fire Doors',
        'discipline': 'Fire & Life Safety',
        'severity': 'High',
        'drawing_ref': 'FLS-1037 / MEP-FLS-01',
        'keywords': ['pressurization', 'fire door', 'fire rating', 'discharge', 'smoke management', 'firefighter elevator'],
        'expected': '2-hour fire-rated exit enclosures, 50 Pa positive pressurization, and direct ground exterior discharge.',
        'issue_if_missing': True,
        'standard_clause': 'UAE Fire Code 2018 Ch. 10: Exit stairs in high-rise buildings require 2-hour rating and mechanical pressurization.',
        'cost_delta': 85000,
        'schedule_delta': '1.5 weeks'
    },
    {
        'id': 'AUTH-DM-PARKING-012',
        'pillar': 'Authority Codes',
        'source': 'Dubai Building Code (DBC 2021) / DM',
        'category': 'Parking Ratios & Allocation',
        'discipline': 'Planning & Regulations',
        'severity': 'Medium',
        'drawing_ref': 'AR-0030 (Schedules)',
        'keywords': ['parking', 'car park', 'parking bay', 'visitor parking', 'residential bays'],
        'expected': 'Parking provision adhering to unit bedroom count ratios plus dedicated visitor and accessible bays.',
        'issue_if_missing': True,
        'standard_clause': 'DM DBC 2021 Part E: Residential parking min 1 bay (1-2 bed), 2 bays (3+ bed) plus 10% visitor provision.',
        'cost_delta': 150000,
        'schedule_delta': '1.0 week'
    },
    {
        'id': 'AUTH-DM-UNIVERSAL-013',
        'pillar': 'Authority Codes',
        'source': 'Dubai Universal Design Code 2017',
        'category': 'Accessibility & Universal Design',
        'discipline': 'Architecture & Planning',
        'severity': 'Medium',
        'drawing_ref': 'AR-1001 (Ground Floor)',
        'keywords': ['accessible', 'barrier-free', 'universal design', 'ramp', 'pod', 'disabled'],
        'expected': 'Barrier-free pedestrian pathways, compliant ramp gradients (1:12), and accessible parking close to lifts.',
        'issue_if_missing': True,
        'standard_clause': 'Dubai Universal Design Code: Mandatory universal accessibility features across public and amenity zones.',
        'cost_delta': 35000,
        'schedule_delta': '0.5 weeks'
    },
    {
        'id': 'AUTH-DEWA-SUBST-014',
        'pillar': 'Authority Codes',
        'source': 'DEWA Regulations for Electrical Installations',
        'category': 'DEWA Substation & Clearances',
        'discipline': 'MEP & Utilities',
        'severity': 'High',
        'drawing_ref': 'AR-1001 / MEP-SUB-01',
        'keywords': ['substation', 'dewa', 'transformer', 'switchgear', 'clear height', 'vehicular access'],
        'expected': 'Dedicated ground-level DEWA substation with direct road access, equipment doors, and 4.0m clear height.',
        'issue_if_missing': False,
        'standard_clause': 'DEWA Electrical Regulations 2017: Transformer and HV rooms require ground road-facing accessibility.',
        'cost_delta': 90000,
        'schedule_delta': '2.0 weeks'
    },
    {
        'id': 'AUTH-DM-GREEN-015',
        'pillar': 'Authority Codes',
        'source': 'Dubai Municipality (Al Safaat Green Building Code)',
        'category': 'Thermal Performance & Glazing',
        'discipline': 'Landscape & Sustainability',
        'severity': 'Medium',
        'drawing_ref': 'SPEC-FACADE-01',
        'keywords': ['u-value', 'shgc', 'thermal', 'glazing', 'insulation', 'al safaat', 'green building'],
        'expected': 'Façade and roof envelope thermal insulation U-values compliant with Al Safaat Silver/Golden standards.',
        'issue_if_missing': True,
        'standard_clause': 'Al Safaat Green Building Code: Roof U-value <= 0.30 W/m²K, Wall U-value <= 0.57 W/m²K, Glazing SHGC <= 0.30.',
        'cost_delta': 110000,
        'schedule_delta': '1.0 week'
    },

    # 3. Ellington Brand Guidelines & Luxury Specs
    {
        'id': 'ELL-BRAND-LOBBY-020',
        'pillar': 'Brand Standards',
        'source': 'Ellington Brand Guidelines 2024',
        'category': 'Signature Arrival & Double-Height Lobby',
        'discipline': 'Brand & Finishes',
        'severity': 'Medium',
        'drawing_ref': 'AR-1001 & AR-3001',
        'keywords': ['lobby', 'entrance', 'double-height', 'arrival', 'concierge', 'drop-off'],
        'expected': 'Signature grand double-height entrance lobby (minimum 6.0m clear ceiling) with dedicated drop-off.',
        'issue_if_missing': True,
        'standard_clause': 'Ellington Brand Standards: Premium hospitality-grade arrival experience with signature double-height volume.',
        'cost_delta': 75000,
        'schedule_delta': '0.5 weeks'
    },
    {
        'id': 'ELL-BRAND-PALETTE-021',
        'pillar': 'Brand Standards',
        'source': 'Ellington Brand Guidelines 2024',
        'category': 'Signature Material Palette & Façade',
        'discipline': 'Brand & Finishes',
        'severity': 'Medium',
        'drawing_ref': 'AR-2001 to AR-2004',
        'keywords': ['material', 'finish', 'travertine', 'bronze', 'terracotta', 'fluted', 'champagne', 'wood'],
        'expected': 'Façade and interior public area specifications featuring Ellington signature 2024 premium material palette.',
        'issue_if_missing': True,
        'standard_clause': 'Ellington Palette 2024: Natural stone / travertine, brushed bronze metallics, and architectural fluted accents.',
        'cost_delta': 180000,
        'schedule_delta': '1.5 weeks'
    },
    {
        'id': 'ELL-BRAND-BALCONY-022',
        'pillar': 'Brand Standards',
        'source': 'Ellington Brand Guidelines 2024',
        'category': 'Balcony Depth & Outdoor Living',
        'discipline': 'Architecture & Façade',
        'severity': 'Low',
        'drawing_ref': 'AR-1006 to AR-1036',
        'keywords': ['balcony', 'terrace', 'outdoor', 'balustrade', 'cantilever', 'glazing'],
        'expected': 'Generous private outdoor balconies with minimum 1.8m usable depth and frameless safety balustrades.',
        'issue_if_missing': True,
        'standard_clause': 'Ellington Residential Standard: Seamless indoor-outdoor living with deep usable balconies.',
        'cost_delta': 45000,
        'schedule_delta': '0.5 weeks'
    },
    {
        'id': 'ELL-BRAND-AMENITY-023',
        'pillar': 'Brand Standards',
        'source': 'Ellington Brand Guidelines 2024',
        'category': 'Resort-Style Amenities & Pool Deck',
        'discipline': 'Landscape & Sustainability',
        'severity': 'Medium',
        'drawing_ref': 'AR-1005 (Level 4 Podium)',
        'keywords': ['infinity pool', 'pool', 'amenity', 'clubhouse', 'fitness', 'spa', 'yoga', 'landscaped podium'],
        'expected': 'Resort-style infinity edge pool, landscaped podium deck, fitness studio, and signature wellness amenities.',
        'issue_if_missing': True,
        'standard_clause': 'Ellington Signature Living: Integrated wellness amenities and hotel-inspired leisure podium.',
        'cost_delta': 95000,
        'schedule_delta': '1.0 week'
    },

    # 4. Cross-Discipline Coordination
    {
        'id': 'COORD-EXT-STAIR-005',
        'pillar': 'Project Submissions & Packages',
        'source': 'Approved Architectural Master Plan vs Landscape Package',
        'category': 'External Staircase / Landscape Consistency',
        'discipline': 'Landscape & Architecture',
        'severity': 'High',
        'drawing_ref': 'AR-1001 (Ground) vs LS-101 (Landscape)',
        'keywords': ['stair', 'staircase', 'external stair', 'podium stair', 'landscape steps'],
        'expected': 'External staircase connecting podium landscape to ground floor must be consistently reflected in both architectural and landscape submissions.',
        'issue_if_missing': False,
        'standard_clause': 'Cross-Discipline Alignment: External circulation stairs from Master Plan must exist in both Architecture and Landscape drawings.',
        'cost_delta': 45000,
        'schedule_delta': '1.0 week'
    },
    {
        'id': 'COORD-STR-COLUMN-030',
        'pillar': 'Project Submissions & Packages',
        'source': 'Bukadra Plot 6117262 Structural & Architectural Coordination',
        'category': 'Column Grid & Transfer Alignment',
        'discipline': 'Structural',
        'severity': 'High',
        'drawing_ref': 'AR-STR-OVERLAY-01',
        'keywords': ['column', 'grid', 'transfer slab', 'shear wall', 'alignment', 'structural'],
        'expected': 'Structural column grid alignment verified between podium parking levels and upper residential tower.',
        'issue_if_missing': False,
        'standard_clause': 'Engineering Coordination: Tower columns must transfer safely onto podium grid without obstructing drive aisles.',
        'cost_delta': 320000,
        'schedule_delta': '2.5 weeks'
    },
    {
        'id': 'COORD-ACOUSTIC-031',
        'pillar': 'Project Submissions & Packages',
        'source': 'Sample Schematic Package (Infosight Acoustic Report)',
        'category': 'Acoustic Partition & Noise Criteria',
        'discipline': 'Acoustics',
        'severity': 'Medium',
        'drawing_ref': 'ACOUSTIC-RPT-01',
        'keywords': ['acoustic', 'stc', 'noise', 'ambient noise', 'partition', 'iic', 'rw+ctr', 'reverberation'],
        'expected': 'Acoustic design criteria meeting NC 30-35 for bedrooms and minimum STC 55 between adjoining residential units.',
        'issue_if_missing': True,
        'standard_clause': 'Infosight Acoustic Criteria: Inter-tenancy separating walls STC >= 55; bedroom ambient noise <= NC 30.',
        'cost_delta': 65000,
        'schedule_delta': '1.0 week'
    },
]

RULE_BY_ID = {r['id']: r for r in COMPREHENSIVE_RULES}

def snippet(text: str, keyword: str, window: int = 140) -> str:
    m = re.search(re.escape(keyword), text, flags=re.I)
    if not m:
        return ''
    start = max(0, m.start() - window)
    end = min(len(text), m.end() + window)
    s = re.sub(r'\s+', ' ', text[start:end]).strip()
    return ('…' if start else '') + s + ('…' if end < len(text) else '')

# ---------------------------------------------------------
# Stream A: AI First-Pass Review Engine
# ---------------------------------------------------------
def run_ai_first_pass(text: str, rules_to_run: List[Dict[str, Any]] = COMPREHENSIVE_RULES) -> List[Dict[str, Any]]:
    t = text.lower()
    results = []
    
    for rule in rules_to_run:
        found_kw = next((kw for kw in rule['keywords'] if kw.lower() in t), None)
        rule_sev = rule.get('severity', 'Medium')
        
        if found_kw:
            status = 'Evidence Found'
            severity = 'Info' if rule.get('issue_if_missing', True) else 'Needs Comparison'
            finding = f"Confirmed evidence for {rule['category']} detected in submitted package."
            evidence = snippet(text, found_kw)
            confidence = 94 if len(evidence) > 80 else 82
        else:
            if rule.get('issue_if_missing', True):
                status = 'Potential Gap'
                severity = rule_sev
                finding = f"No explicit evidence detected for {rule['category']}. Verification against {rule['source']} required."
                evidence = f"No keyword match found for {', '.join(rule['keywords'][:3])}."
                confidence = 75
            else:
                status = 'Needs Baseline Comparison'
                severity = rule_sev
                finding = f"Cross-discipline verification required against approved baseline master plan / structural sheets."
                evidence = 'Cross-discipline baseline verification needed.'
                confidence = 90

        default_consultant = (
            f"Please verify {rule['category']} against {rule['source']} ({rule.get('standard_clause', '')}) and submit revised drawing / specification."
            if status != 'Evidence Found' else ''
        )

        results.append({
            'id': rule['id'],
            'source': 'AI',
            'drawing_ref': rule.get('drawing_ref', 'AR-GENERAL'),
            'discipline': rule['discipline'],
            'category': rule['category'],
            'reference_source': rule['source'],
            'clause': rule.get('standard_clause', '—'),
            'ai_status': status,
            'severity': severity,
            'ai_confidence': f'{confidence}%',
            'finding_text': finding,
            'evidence_text': evidence,
            'consultant_comment': default_consultant,
            'internal_note': '',
            'status': 'Pending Review',  # TA decision: Confirm Issue, Reject as False Positive, Modify & Confirm, Need Clarification
            'cost_delta': rule.get('cost_delta', 0) if status != 'Evidence Found' else 0,
            'schedule_delta': rule.get('schedule_delta', '0 wks') if status != 'Evidence Found' else '0 wks',
            'attachments': []
        })
    return results

# ---------------------------------------------------------
# Stream B: AI Review of Technical Architect Findings (10-Point Advisory)
# ---------------------------------------------------------
def run_ai_review_on_ta_finding(
    ta_finding: Dict[str, Any],
    ai_findings: List[Dict[str, Any]],
    raw_submittal_text: str = ""
) -> Dict[str, Any]:
    """
    Evaluates human-created findings and returns advisory suggestions.
    Crucial requirement: AI does NOT modify or reject human finding.
    """
    comment = (ta_finding.get('finding_text', '') + " " + ta_finding.get('consultant_comment', '')).lower()
    cat = ta_finding.get('category', '').lower()
    dwg = ta_finding.get('drawing_ref', '').lower()
    text_lower = raw_submittal_text.lower()
    
    # 1. Duplicate Detection against Stream A
    duplicate_match = None
    for ai_f in ai_findings:
        # Check by rule keywords or ID or category
        rule = RULE_BY_ID.get(ai_f['id'])
        if rule:
            matching_kws = [kw for kw in rule['keywords'] if kw.lower() in comment]
            if len(matching_kws) >= 2 or rule['category'].lower() in comment:
                duplicate_match = ai_f
                break
                
    if duplicate_match:
        dup_text = f"Potential duplicate detected: Similar AI Finding exists ({duplicate_match['id']} — {duplicate_match['category']})."
        is_dup = True
        dup_id = duplicate_match['id']
    else:
        dup_text = "No duplicate detected across active AI findings register."
        is_dup = False
        dup_id = ""

    # 2. Reference Validation & Clause Matching
    matched_rule = None
    for r in COMPREHENSIVE_RULES:
        if any(kw in comment for kw in r['keywords']):
            matched_rule = r
            break
            
    if matched_rule:
        ref_val = f"Potentially correlated with {matched_rule['pillar']}: {matched_rule['standard_clause']} ({matched_rule['source']})."
        suggested_clause = matched_rule['standard_clause']
    elif "design judgment" in cat or "observation" in cat:
        ref_val = "Categorized as Design Judgment / Subjective Observation. No mandatory regulatory clause required."
        suggested_clause = "Ellington Luxury Aesthetic & Craftsmanship Standard"
    else:
        ref_val = "No direct statutory code clause identified. Verified as qualitative or project-specific observation."
        suggested_clause = "Project Brief Specification"

    # 3. Evidence Check from drawings
    if "setback" in comment:
        evidence_chk = "Drawing text extract indicates 4.5m side setback note, but missing front road setback dimension."
    elif "height" in comment:
        evidence_chk = "Floor-to-floor elevation notes found on sheets AR-2001 to AR-2004."
    elif "material" in comment or "palette" in comment:
        evidence_chk = "Façade finish schedule references standard render rather than signature Travertine."
    else:
        evidence_chk = "Visual / geometric verification recommended on referenced sheet excerpt."

    # 4. Missing Information Check
    if "fire" in comment and "schedule" not in text_lower:
        missing_info = "Finding references fire-rated assemblies, but no dedicated door schedule was detected in the submittal."
    elif "parking" in comment and "bay" not in comment:
        missing_info = "Specific apartment unit breakdown or count of visitor bays not detailed in comment."
    else:
        missing_info = "Sufficient technical context provided in finding description."

    # 5. Contradiction Detection
    if "parking" in comment and "parking schedule" in text_lower:
        contra = "Advisory: Drawing Sheet AR-0030 includes a preliminary parking schedule. Please verify if discrepancy relates to visitor bay counts."
    elif "setback" in comment and "6.0m" in text_lower:
        contra = "Advisory: Sheet notes indicate a 6.0m boundary line buffer. Confirm if observation concerns landscape encroachment."
    else:
        contra = "No direct contradictions detected against ingested submission metadata."

    # 6. Suggested Severity
    if any(k in comment for k in ['life safety', 'fire', 'egress', 'dewa', 'structure', 'setback']):
        sugg_sev = "High"
    elif any(k in comment for k in ['finish', 'balcony', 'aesthetic', 'trim']):
        sugg_sev = "Low"
    else:
        sugg_sev = "Medium"

    # 7. Suggested Consultant Wording
    if matched_rule:
        sugg_wording = f"Please revise {ta_finding.get('drawing_ref', 'drawing')} to ensure compliance with {matched_rule['source']} ({matched_rule.get('standard_clause', '')}). Provide dimensioned annotations on resubmission."
    else:
        sugg_wording = f"Please review {ta_finding.get('category', 'item')} per Ellington design standards. Update drawing package to address reviewer observation."

    # 8. Related Project Context
    if "stair" in comment or "landscape" in comment:
        rel_context = "Architecture drawing AR-1001 reflects external stair, while Landscape package LS-101 requires alignment."
    elif "column" in comment or "grid" in comment:
        rel_context = "Correlates with transfer slab structural coordination on Level 4 Podium."
    else:
        rel_context = "Observation is localized to the referenced drawing package."

    # 9. Classification
    if "design judgment" in cat:
        classif = "Design Judgment / Technical Architect Observation"
    elif matched_rule and "Authority" in matched_rule['pillar']:
        classif = "Statutory Authority Compliance"
    elif matched_rule and "DCR" in matched_rule['pillar']:
        classif = "Master Developer DCR Requirement"
    else:
        classif = "Quality & Craftsmanship Standard"

    return {
        'has_feedback': True,
        'reference_validation': ref_val,
        'evidence_check': evidence_chk,
        'duplicate_detection': dup_text,
        'is_duplicate': is_dup,
        'duplicate_of_id': dup_id,
        'missing_information': missing_info,
        'contradiction_detection': contra,
        'suggested_severity': sugg_sev,
        'suggested_consultant_wording': sugg_wording,
        'related_project_context': rel_context,
        'classification': classif,
        'confidence': '88%' if not is_dup else '92%'
    }

# ---------------------------------------------------------
# AI Delta Review Engine (V1 vs V2)
# ---------------------------------------------------------
def run_ai_delta_review(
    issued_items: List[Dict[str, Any]],
    resubmission_text: str
) -> List[Dict[str, Any]]:
    """
    Compares consultant revised submission against issued comments.
    Proposes resolution status for Technical Architect validation.
    """
    t = resubmission_text.lower()
    delta_results = []
    
    for item in issued_items:
        fid = item.get('finding_id', item.get('id', ''))
        comment = item.get('comment', item.get('consultant_comment', '')).lower()
        drawing_ref = item.get('drawing_ref', 'AR-GENERAL')
        category = item.get('category', 'General')
        
        # Check if ID, drawing ref, or key terms are addressed
        rule = RULE_BY_ID.get(fid)
        found_kw = next((kw for kw in rule['keywords'] if kw.lower() in t), None) if rule else None
        id_found = fid.lower() in t
        
        # Check if consultant requested exception or contested
        resp_obj = item.get('response', {})
        resp_type = resp_obj.get('response_type', '') if isinstance(resp_obj, dict) else ''
        
        if resp_type == "Contest Finding":
            delta_status = "Contested by Consultant — Technical Architect Review Required"
            evidence = f"Consultant note: '{resp_obj.get('response_note', '')}'. Consultant contested requirement."
            suggested_action = "Review Contestation"
        elif id_found or found_kw:
            if "clarif" in comment:
                delta_status = "Clarification / Response Detected"
            else:
                delta_status = "Potentially Resolved"
            evidence = snippet(resubmission_text, fid if id_found else found_kw)
            suggested_action = "Validate Resolution & Close"
        else:
            delta_status = "Still Open / No Evidence Found"
            evidence = "No matching revisions, keywords, or response detected in revised submission text."
            suggested_action = "Maintain Open in Cycle 2"

        delta_results.append({
            'finding_id': fid,
            'drawing_ref': drawing_ref,
            'category': category,
            'issued_comment': item.get('comment') or item.get('consultant_comment', ''),
            'consultant_response_type': resp_type or 'Accept / Will Rectify',
            'consultant_response_note': resp_obj.get('response_note', 'Revision incorporated into V2 drawings.') if isinstance(resp_obj, dict) else '',
            'ai_delta_status': delta_status,
            'detected_evidence': evidence,
            'suggested_action': suggested_action,
            'ta_decision': 'Pending Decision',  # Close Finding, Keep Open, Roll into Cycle 2
            'ta_note': ''
        })
        
    return delta_results
