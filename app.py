import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import json
from pathlib import Path
import re

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    from docx import Document
except Exception:
    Document = None

# Import V1 modular engines & configs
from config import (
    ROLE_TECHNICAL_ARCHITECT,
    ROLE_CONSULTANT,
    ROLES,
    ROLE_DESCRIPTIONS,
    STAGE_ORDER,
    STAGE_STATUSES,
    DEFAULT_SCORING_CONFIG,
    ATTACHMENT_TYPES,
    VISIBILITY_INTERNAL_ONLY,
    VISIBILITY_CONSULTANT_VISIBLE,
    ATTACHMENT_VISIBILITY_OPTIONS,
    FINDING_CATEGORIES,
    SEVERITIES,
    TA_AI_DECISIONS,
    CONSULTANT_RESPONSE_OPTIONS
)
from storage_manager import (
    load_audit_trail,
    save_audit_trail,
    log_audit_event,
    load_stage_history,
    save_stage_history,
    upsert_stage_status,
    load_review_cycles,
    save_review_cycles,
    get_active_or_latest_cycle,
    lock_and_issue_cycle_package,
    save_uploaded_file,
    BASE_DIR
)
from rule_engine import (
    COMPREHENSIVE_RULES,
    RULE_BY_ID,
    run_ai_first_pass,
    run_ai_review_on_ta_finding,
    run_ai_delta_review,
    snippet
)
from scoring import calculate_dynamic_compliance_score

# ---------------------------------------------------------
# Page Configuration & Brand Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title='Ellington AI Design Review — V1 Governance',
    page_icon='🏗️',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    h1, h2, h3, .brand-font {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 3.5rem;
    }
    
    /* Header Banner */
    .header-banner {
        background: linear-gradient(135deg, #0A192F 0%, #0E2A47 60%, #173B61 100%);
        padding: 22px 26px;
        border-radius: 12px;
        color: #FFFFFF;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(10, 25, 47, 0.15);
        border: 1px solid rgba(212, 175, 55, 0.35);
    }
    
    .header-banner .title {
        font-size: 1.75rem;
        font-weight: 800;
        color: #F8FAFC;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .header-banner .gold-badge {
        background: linear-gradient(135deg, #D4AF37 0%, #AA820A 100%);
        color: #0A192F;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .header-banner .subtitle {
        color: #94A3B8;
        font-size: 0.88rem;
        margin-top: 6px;
        margin-bottom: 0;
    }
    
    /* Role Indicator Box */
    .role-banner {
        background: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-left: 5px solid #0B315E;
        padding: 10px 16px;
        border-radius: 6px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Process Bar */
    .process-container {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px;
    }
    
    .process-step {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #475569;
    }
    
    .process-step.active {
        color: #0B315E;
        font-weight: 700;
    }
    
    .step-num {
        background: #E2E8F0;
        color: #334155;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
    }
    
    .process-step.active .step-num {
        background: #0B315E;
        color: #FFFFFF;
    }
    
    /* Metric Cards */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .card-label {
        font-size: 0.75rem;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    
    .card-value {
        font-size: 1.5rem;
        font-weight: 800;
        color: #0F172A;
        margin-top: 4px;
        font-family: 'Outfit', sans-serif;
    }
    
    .notice-box {
        background: #F0F9FF;
        border-left: 4px solid #0284C7;
        padding: 12px 16px;
        border-radius: 6px;
        color: #0C4A6E;
        font-size: 0.86rem;
        margin: 12px 0;
    }
    
    .human-box {
        background: #FFFBEB;
        border-left: 4px solid #F59E0B;
        padding: 12px 16px;
        border-radius: 6px;
        color: #78350F;
        font-size: 0.86rem;
        margin: 12px 0;
    }
    
    .client-box {
        background: #F0FDF4;
        border-left: 4px solid #10B981;
        padding: 12px 16px;
        border-radius: 6px;
        color: #064E3B;
        font-size: 0.86rem;
        margin: 12px 0;
    }
    
    .warning-box {
        background: #FEF2F2;
        border-left: 4px solid #EF4444;
        padding: 12px 16px;
        border-radius: 6px;
        color: #991B1B;
        font-size: 0.86rem;
        margin: 12px 0;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
def extract_text_from_file(uploaded_file):
    name = uploaded_file.name.lower()
    data = uploaded_file.read()
    uploaded_file.seek(0)
    if name.endswith('.txt'):
        return data.decode('utf-8', errors='ignore')
    if name.endswith('.pdf') and PdfReader:
        try:
            reader = PdfReader(BytesIO(data))
            return '\n'.join((p.extract_text() or '') for p in reader.pages)
        except Exception as e:
            return f"Error reading PDF: {e}"
    if name.endswith('.docx') and Document:
        try:
            doc = Document(BytesIO(data))
            return '\n'.join(p.text for p in doc.paragraphs)
        except Exception as e:
            return f"Error reading DOCX: {e}"
    return ''

# ---------------------------------------------------------
# Global State Initialization
# ---------------------------------------------------------
if 'active_role' not in st.session_state:
    st.session_state['active_role'] = ROLE_TECHNICAL_ARCHITECT

if 'project' not in st.session_state:
    st.session_state['project'] = 'Ellington Bukadra Tower (Plot 6117262)'

if 'stage' not in st.session_state:
    st.session_state['stage'] = 'Schematic Design'

if 'discipline' not in st.session_state:
    st.session_state['discipline'] = 'Architecture & Planning'

if 'stream_a_findings' not in st.session_state:
    st.session_state['stream_a_findings'] = []

if 'stream_b_findings' not in st.session_state:
    st.session_state['stream_b_findings'] = []

if 'current_cycle_num' not in st.session_state:
    st.session_state['current_cycle_num'] = 1

# ---------------------------------------------------------
# Sidebar: Role Switcher & Navigation
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 10px 0 14px 0;'>
        <div style='font-size: 1.4rem; font-weight: 800; color: #0A192F; font-family: Outfit, sans-serif; letter-spacing: 0.05em;'>ELLINGTON</div>
        <div style='font-size: 0.70rem; color: #AA820A; font-weight: 700; letter-spacing: 0.15em;'>AI DESIGN REVIEW V1</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 👤 User Persona / Role")
    selected_role = st.selectbox(
        "Active Application Role",
        ROLES,
        index=ROLES.index(st.session_state['active_role']),
        key="role_selector",
        help="Switch between Technical Architect (internal authorization) and Lead Design Consultant (external resubmission)."
    )
    if selected_role != st.session_state['active_role']:
        st.session_state['active_role'] = selected_role
        st.rerun()

    st.caption(f"**Permissions:** {ROLE_DESCRIPTIONS[selected_role]}")
    st.divider()

    # Role-Specific Navigation Menu
    if selected_role == ROLE_TECHNICAL_ARCHITECT:
        TA_PAGES = [
            "📊 Executive Dashboard",
            "🏗️ Design Review Studio (Dual Stream)",
            "🔄 Delta Review & Sign-Off",
            "📜 Audit Trail & Stage History",
            "📐 Drawing Scale Analysis Feasibility"
        ]
        if 'ta_nav' not in st.session_state or st.session_state['ta_nav'] not in TA_PAGES:
            st.session_state['ta_nav'] = TA_PAGES[0]
        active_page = st.radio("TA Navigation", TA_PAGES, key="ta_nav", label_visibility="collapsed")
    else:
        CONS_PAGES = [
            "📋 Issued Comments Register",
            "💬 Submit Responses & Contestations",
            "📤 Upload Revised Submittal (V2.0+)",
            "📜 Consultant Review History"
        ]
        if 'cons_nav' not in st.session_state or st.session_state['cons_nav'] not in CONS_PAGES:
            st.session_state['cons_nav'] = CONS_PAGES[0]
        active_page = st.radio("Consultant Navigation", CONS_PAGES, key="cons_nav", label_visibility="collapsed")

    st.divider()
    st.markdown(f"**Current Milestone:** `{st.session_state['stage']}`")
    st.markdown(f"**Review Cycle:** `Cycle {st.session_state['current_cycle_num']}`")
    st.caption("🔒 **Human Authority Gate: Strictly Enforced**")

# =========================================================
# TECHNICAL ARCHITECT WORKSPACE
# =========================================================
if st.session_state['active_role'] == ROLE_TECHNICAL_ARCHITECT:

    # -----------------------------------------------------
    # TA VIEW 1: Executive Dashboard
    # -----------------------------------------------------
    if active_page == "📊 Executive Dashboard":
        st.markdown("""
        <div class='header-banner'>
            <div class='title'>
                <span>Executive Design Review Dashboard</span>
                <span class='gold-badge'>V1 Architecture</span>
            </div>
            <div class='subtitle'>Portfolio-wide tracking across Concept, Schematic, Detailed Design, and Tender Package milestones.</div>
        </div>
        """, unsafe_allow_html=True)
        
        records = load_stage_history()
        projects = sorted(list(set(r.get('project') for r in records if r.get('project'))))
        default_projects = ['Ellington Bukadra Tower (Plot 6117262)', 'Ellington Beach House (Palm Jumeirah)', 'Mercer House (Uptown)']
        for p in default_projects:
            if p not in projects:
                projects.append(p)
                
        sel_proj = st.selectbox("Select Project Portfolio", projects)
        st.session_state['project'] = sel_proj
        
        # Stage metrics
        rows = []
        for s in STAGE_ORDER:
            m = next((r for r in records if r.get('project') == sel_proj and r.get('stage') == s), None)
            if m:
                rows.append({
                    'Stage': s,
                    'Status': m.get('status', 'Not Started'),
                    'Review Cycle': m.get('review_cycle', 'Cycle 1'),
                    'Discipline': m.get('discipline', '—'),
                    'Compliance Score': f"{m.get('compliance_score', 100)}%",
                    'Reviewer': m.get('reviewer', '—'),
                    'Last Updated': m.get('updated_at', '—')
                })
            else:
                rows.append({
                    'Stage': s,
                    'Status': 'Not Started',
                    'Review Cycle': 'Cycle 1',
                    'Discipline': '—',
                    'Compliance Score': '—',
                    'Reviewer': '—',
                    'Last Updated': '—'
                })
                
        df_dash = pd.DataFrame(rows)
        comp_count = int(df_dash['Status'].astype(str).str.startswith('Completed').sum())
        act_count = int(df_dash['Status'].isin(['In Review', 'Technical Architect Review', 'Issued to Consultant', 'Resubmission Received', 'Delta Review']).sum())
        not_start = int((df_dash['Status'] == 'Not Started').sum())
        
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='metric-card'><div class='card-label'>Total Milestones</div><div class='card-value'>{len(STAGE_ORDER)}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><div class='card-label'>Stages Completed</div><div class='card-value' style='color:#059669;'>{comp_count}</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><div class='card-label'>Active in Review</div><div class='card-value' style='color:#0284C7;'>{act_count}</div></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='metric-card'><div class='card-label'>Not Started</div><div class='card-value' style='color:#64748B;'>{not_start}</div></div>", unsafe_allow_html=True)
        
        st.markdown("### Stage Progression Matrix")
        st.dataframe(df_dash, use_container_width=True, hide_index=True)
        
        prog = comp_count / len(STAGE_ORDER) if STAGE_ORDER else 0.0
        st.progress(prog)
        st.caption(f"**{int(prog * 100)}% Milestone Completion** across active development lifecycle.")

    # -----------------------------------------------------
    # TA VIEW 2: Design Review Studio (Dual Stream)
    # -----------------------------------------------------
    elif active_page == "🏗️ Design Review Studio (Dual Stream)":
        st.markdown("""
        <div class='header-banner'>
            <div class='title'>
                <span>Technical Architect Design Review Studio</span>
                <span class='gold-badge'>Dual-Stream Review</span>
            </div>
            <div class='subtitle'>Stream A (AI First-Pass) + Stream B (Technical Architect Gaps & Judgments) with Point-in-Time AI Advisory.</div>
        </div>
        """, unsafe_allow_html=True)

        # Context Setup
        p_c1, p_c2, p_c3, p_c4 = st.columns([1.2, 1, 1, 0.8])
        p_c1.text_input("Project Name", st.session_state['project'], key="studio_proj")
        stage_choice = p_c2.selectbox("Design Stage", STAGE_ORDER, index=STAGE_ORDER.index(st.session_state['stage']) if st.session_state['stage'] in STAGE_ORDER else 1)
        st.session_state['stage'] = stage_choice
        st.session_state['discipline'] = p_c3.selectbox("Discipline", ['Architecture & Planning', 'Fire & Life Safety', 'Structural', 'MEP & Utilities', 'Acoustics'])
        st.session_state['submittal_ver'] = p_c4.text_input("Submittal Version", "V1.0")

        # Ingestion Section
        with st.expander("📥 Ingest Drawing Submittal Package (V1.0)", expanded=not bool(st.session_state['stream_a_findings'])):
            st.markdown("Select a pre-indexed sample submittal or upload a drawing text package:")
            b1, b2, b3 = st.columns(3)
            if b1.button("🏢 Load Bukadra Architecture (V1)", use_container_width=True):
                p = BASE_DIR / "sample_schematic_arch.txt"
                if p.exists():
                    st.session_state['raw_submittal_text'] = p.read_text(encoding='utf-8')
                    st.session_state['submittal_filename'] = "015-24_Bukadra_Plot_6117262_Schematic_Architecture_V1.txt"
                    st.success("Loaded Bukadra Architecture!")
            if b2.button("🚒 Load Bukadra FLS Package", use_container_width=True):
                p = BASE_DIR / "sample_schematic_fls.txt"
                if p.exists():
                    st.session_state['raw_submittal_text'] = p.read_text(encoding='utf-8')
                    st.session_state['submittal_filename'] = "01524-XYZ-B01-FLS-Egress-Strategy_V1.txt"
                    st.success("Loaded Bukadra FLS Package!")
            if b3.button("🔊 Load Acoustics & Struct", use_container_width=True):
                p = BASE_DIR / "sample_schematic_acoustics_struct.txt"
                if p.exists():
                    st.session_state['raw_submittal_text'] = p.read_text(encoding='utf-8')
                    st.session_state['submittal_filename'] = "Infosight_Acoustic_Structural_Report_V1.txt"
                    st.success("Loaded Acoustics & Struct!")
                    
            up_file = st.file_uploader("Or Upload PDF / DOCX / TXT Package", type=['pdf', 'docx', 'txt'], key="ta_pkg_upload")
            if up_file:
                st.session_state['raw_submittal_text'] = extract_text_from_file(up_file)
                st.session_state['submittal_filename'] = up_file.name

            if st.session_state.get('submittal_filename'):
                st.info(f"Active Drawing Package: **{st.session_state['submittal_filename']}**")

            if st.button("🚀 Run AI First-Pass Review", type="primary", use_container_width=True):
                raw = st.session_state.get('raw_submittal_text', '')
                if not raw:
                    sample_p = BASE_DIR / "sample_schematic_arch.txt"
                    raw = sample_p.read_text(encoding='utf-8') if sample_p.exists() else ""
                    st.session_state['raw_submittal_text'] = raw
                    st.session_state['submittal_filename'] = "015-24_Bukadra_Plot_6117262_Schematic_Architecture_V1.txt"
                    
                st.session_state['stream_a_findings'] = run_ai_first_pass(raw)
                log_audit_event(
                    action="AI First-Pass Review Executed",
                    user="AI Engine",
                    role="System",
                    review_cycle=f"Cycle {st.session_state['current_cycle_num']}",
                    new_value=f"{len(st.session_state['stream_a_findings'])} Findings Generated",
                    details=f"Evaluated against 17 rules for {st.session_state['stage']}."
                )
                upsert_stage_status(
                    project=st.session_state['project'],
                    stage=st.session_state['stage'],
                    discipline=st.session_state['discipline'],
                    status='Technical Architect Review',
                    reviewer='Technical Architect'
                )
                st.rerun()

        # -------------------------------------------------
        # Studio Tabs: The 4 Core Screens
        # -------------------------------------------------
        tab1, tab2, tab3, tab4 = st.tabs([
            "🤖 Tab 1: AI Findings (Stream A)",
            "✍️ Tab 2: My Findings (Stream B)",
            "🧠 Tab 3: AI Feedback on My Findings",
            "📦 Tab 4: Final Review & Issue Package"
        ])

        # -------------------------------------------------
        # TAB 1: AI Findings (Stream A)
        # -------------------------------------------------
        with tab1:
            st.markdown("### Stream A: AI First-Pass Compliance Findings")
            st.caption("AI-generated against DCR, Authority Codes, Brand Standards, and Cross-Discipline baseline. Technical Architect must validate each item.")

            if not st.session_state['stream_a_findings']:
                st.info("Run AI First-Pass Review above to populate Stream A findings.")
            else:
                df_a = pd.DataFrame(st.session_state['stream_a_findings'])
                
                # Metrics
                pot_gaps = int((df_a['ai_status'] == 'Potential Gap').sum())
                confirmed_a = int(df_a['status'].isin(['Confirm Issue', 'Modify & Confirm', 'Need Clarification']).sum())
                rejected_a = int((df_a['status'] == 'Reject as False Positive').sum())
                pending_a = int((df_a['status'] == 'Pending Review').sum())

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total AI Findings", len(df_a))
                m2.metric("Confirmed Action Items", confirmed_a, delta="Issued to Consultant" if confirmed_a else None)
                m3.metric("Rejected False Positives", rejected_a, delta="0 Score Deduction" if rejected_a else None, delta_color="inverse")
                m4.metric("Pending TA Decision", pending_a)

                st.markdown("""
                <div class='human-box'>
                    <b>Technical Architect Governance:</b> Confirm valid findings, reject AI noise / false positives, or adjust severity/comments. Rejected findings remain internally auditable, will NOT be shown to the consultant, and will NOT affect compliance score.
                </div>
                """, unsafe_allow_html=True)

                # Editable table
                edited_a = st.data_editor(
                    df_a,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'id': st.column_config.TextColumn('Finding ID', width='small', disabled=True),
                        'drawing_ref': st.column_config.TextColumn('Drawing Ref', width='small', disabled=True),
                        'category': st.column_config.TextColumn('Category', width='medium', disabled=True),
                        'reference_source': st.column_config.TextColumn('Authority / Source', width='medium', disabled=True),
                        'ai_status': st.column_config.TextColumn('AI Status', width='small', disabled=True),
                        'severity': st.column_config.SelectboxColumn('Severity', options=SEVERITIES, width='small'),
                        'ai_confidence': st.column_config.TextColumn('Confidence', width='small', disabled=True),
                        'status': st.column_config.SelectboxColumn('TA Decision', options=TA_AI_DECISIONS, width='medium', required=True),
                        'internal_note': st.column_config.TextColumn('TA Internal Note (Hidden from Consultant)', width='medium'),
                        'consultant_comment': st.column_config.TextColumn('Consultant-Facing Action Comment', width='large'),
                    },
                    key="editor_stream_a_v1"
                )
                
                # Check for changes and log audit
                if st.button("💾 Save Stream A Review Decisions", key="save_stream_a_btn", type="primary"):
                    st.session_state['stream_a_findings'] = edited_a.to_dict('records')
                    log_audit_event(
                        action="Stream A Review Decisions Updated",
                        user="Technical Architect",
                        role="Technical Architect",
                        review_cycle=f"Cycle {st.session_state['current_cycle_num']}",
                        new_value=f"{confirmed_a} Confirmed, {rejected_a} Rejected",
                        details="TA filtered false positives and authorized action comments."
                    )
                    st.success("Stream A decisions saved successfully!")
                    st.rerun()

        # -------------------------------------------------
        # TAB 2: My Findings (Stream B - Manual TA Findings)
        # -------------------------------------------------
        with tab2:
            st.markdown("### Stream B: Technical Architect Independent Findings")
            st.caption("Add subjective observations, spatial qualities, craftsmanship standards, or regulatory gaps identified through human expertise.")

            # Form to Add Finding
            with st.expander("➕ Add New Technical Architect Finding", expanded=False):
                with st.form("add_ta_finding_form", clear_on_submit=True):
                    f_c1, f_c2 = st.columns([1, 1])
                    dwg_ref = f_c1.text_input("Drawing / Document Reference *", placeholder="e.g. AR-1002 / Detail Section D-04")
                    finding_cat = f_c2.selectbox("Finding Category", FINDING_CATEGORIES, index=0)

                    f_c3, f_c4, f_c5 = st.columns(3)
                    disc = f_c3.selectbox("Discipline", ['Architecture & Planning', 'Brand & Finishes', 'Structural', 'MEP', 'Landscape'])
                    sev = f_c4.selectbox("Severity *", SEVERITIES, index=2)
                    loc_area = f_c5.text_input("Location / Drawing Area (optional)", placeholder="e.g. Tower North Façade, Grid 4-8")

                    finding_desc = st.text_area("Finding Description / Observation *", placeholder="e.g. Balcony soffit finish detail lacks drip groove; risk of rainwater staining on champagne bronze panels.")
                    cons_comment = st.text_area("Consultant-Facing Action Required *", placeholder="e.g. Provide continuous architectural drip profile detail on Sheet AR-3004.")
                    
                    f_c6, f_c7 = st.columns(2)
                    ref_source = f_c6.text_input("Reference Standard (optional for design judgments)", placeholder="e.g. Ellington Façade Standard 2024 / DDA")
                    clause_ref = f_c7.text_input("Clause / Section (optional)", placeholder="e.g. Clause 8.2 or Qualitative Intent")

                    internal_note = st.text_input("Internal Note (strictly hidden from consultant)", placeholder="e.g. Discuss with Senior Project Director before final sign-off.")

                    # File / Sketch Upload
                    st.markdown("##### 📎 Attach Supporting Evidence / Sketch")
                    att_c1, att_c2 = st.columns([1.5, 1])
                    uploaded_att = att_c1.file_uploader("Upload PDF / PNG / JPG / JPEG (Sketch, Markup, Screenshot)", type=['pdf', 'png', 'jpg', 'jpeg'], key="ta_att_uploader")
                    att_type = att_c2.selectbox("Attachment Type", ATTACHMENT_TYPES, index=3)
                    att_vis = att_c2.selectbox("Visibility", ATTACHMENT_VISIBILITY_OPTIONS, index=1)

                    submitted = st.form_submit_button("💾 Save Finding as Draft", type="primary", use_container_width=True)
                    if submitted:
                        if not dwg_ref or not finding_desc or not cons_comment:
                            st.error("Please fill in the required fields (*): Drawing Reference, Finding Description, and Consultant Comment.")
                        else:
                            new_id = f"TA-OBS-{len(st.session_state['stream_b_findings']) + 1:03d}"
                            
                            atts_list = []
                            if uploaded_att:
                                att_meta = save_uploaded_file(uploaded_att, att_type, att_vis, uploaded_by="Technical Architect")
                                atts_list.append(att_meta)

                            new_f = {
                                'id': new_id,
                                'source': 'Technical Architect',
                                'drawing_ref': dwg_ref,
                                'discipline': disc,
                                'category': finding_cat,
                                'location_area': loc_area,
                                'reference_source': ref_source or 'Design Judgment / Professional Opinion',
                                'clause': clause_ref or '—',
                                'finding_text': finding_desc,
                                'evidence_text': 'Manual Human Review Finding',
                                'severity': sev,
                                'ai_confidence': '—',
                                'consultant_comment': cons_comment,
                                'internal_note': internal_note,
                                'status': 'Draft',
                                'attachments': atts_list,
                                'ai_feedback': None,
                                'cost_delta': 0,
                                'schedule_delta': '0 wks'
                            }
                            st.session_state['stream_b_findings'].append(new_f)
                            log_audit_event(
                                action="Technical Architect Finding Created",
                                user="Technical Architect",
                                role="Technical Architect",
                                finding_id=new_id,
                                review_cycle=f"Cycle {st.session_state['current_cycle_num']}",
                                new_value="Draft Finding",
                                details=f"Category: {finding_cat}, Severity: {sev}."
                            )
                            st.success(f"Finding `{new_id}` saved as Draft!")
                            st.rerun()

            # Display existing Stream B findings
            st.markdown("#### Registered Technical Architect Findings")
            if not st.session_state['stream_b_findings']:
                st.info("No manual findings added yet. Click **'+ Add New Technical Architect Finding'** above.")
            else:
                for idx, tf in enumerate(st.session_state['stream_b_findings']):
                    with st.container():
                        st.markdown(f"""
                        <div style='background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #0B315E; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px;'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <div>
                                    <span style='font-size: 1.1rem; font-weight: 700; color: #0F172A;'>`{tf['id']}` — {tf['category']}</span>
                                    <span style='margin-left: 10px; background: #E0E7FF; color: #3730A3; font-size: 0.72rem; padding: 3px 8px; border-radius: 4px; font-weight: 700;'>Source: {tf['source']}</span>
                                    <span style='margin-left: 6px; background: #FEF3C7; color: #92400E; font-size: 0.72rem; padding: 3px 8px; border-radius: 4px; font-weight: 700;'>{tf['severity']}</span>
                                    <span style='margin-left: 6px; background: #F1F5F9; color: #475569; font-size: 0.72rem; padding: 3px 8px; border-radius: 4px;'>Status: {tf['status']}</span>
                                </div>
                                <div style='font-size: 0.82rem; color: #64748B;'>Dwg: <b>{tf['drawing_ref']}</b></div>
                            </div>
                            <div style='margin-top: 8px; font-size: 0.90rem; color: #1E293B;'>
                                <b>Observation:</b> {tf['finding_text']}
                            </div>
                            <div style='margin-top: 4px; font-size: 0.88rem; color: #0369A1;'>
                                <b>Consultant Action:</b> {tf['consultant_comment']}
                            </div>
                            {f"<div style='margin-top: 4px; font-size: 0.82rem; color: #78350F; background: #FFFBEB; padding: 4px 8px; border-radius: 4px;'><b>🔒 Internal Note:</b> {tf['internal_note']}</div>" if tf.get('internal_note') else ""}
                            {f"<div style='margin-top: 6px; font-size: 0.80rem; color: #475569;'>📎 <b>Attachments:</b> {', '.join([f'{a.get("file_type", "File")}: {a.get("filename", "")} [{a.get("visibility", "Visible")}]' for a in tf.get('attachments', [])])}</div>" if tf.get('attachments') else ""}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        btn_c1, btn_c2, btn_c3 = st.columns([1, 1, 2])
                        if btn_c1.button(f"🗑️ Delete", key=f"del_tf_{idx}"):
                            removed = st.session_state['stream_b_findings'].pop(idx)
                            log_audit_event(
                                action="Technical Architect Finding Deleted",
                                user="Technical Architect",
                                role="Technical Architect",
                                finding_id=removed['id'],
                                review_cycle=f"Cycle {st.session_state['current_cycle_num']}",
                                previous_value=removed['finding_text'],
                                new_value="Deleted"
                            )
                            st.rerun()
                        if btn_c2.button(f"✅ Mark Finalized", key=f"fin_tf_{idx}"):
                            st.session_state['stream_b_findings'][idx]['status'] = 'Finalized'
                            st.session_state['stream_b_findings'][idx]['is_finalized_for_issue'] = True
                            st.rerun()

                st.divider()
                st.markdown("#### 🧠 Point-in-Time AI Advisory Review")
                st.markdown("""
                <div class='notice-box'>
                    <b>Controlled Review Action:</b> AI evaluates your manual findings against the 17-rule knowledge base and Stream A to identify potential duplicates, suggest related DCR clauses, check for contradictions, and refine consultant wording.
                    <b>AI will never automatically modify, overwrite, or delete your findings.</b>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🚀 Run AI Advisory Review on My Findings", type="primary", use_container_width=True):
                    raw_text = st.session_state.get('raw_submittal_text', '')
                    for f in st.session_state['stream_b_findings']:
                        ai_fb = run_ai_review_on_ta_finding(f, st.session_state['stream_a_findings'], raw_text)
                        f['ai_feedback'] = ai_fb
                        f['status'] = 'AI Reviewed'
                    
                    log_audit_event(
                        action="AI Advisory Review Executed on TA Findings",
                        user="AI Engine",
                        role="System",
                        review_cycle=f"Cycle {st.session_state['current_cycle_num']}",
                        new_value=f"{len(st.session_state['stream_b_findings'])} Findings Evaluated",
                        details="Advisory feedback generated for reference validation, duplicate check, and consultant wording."
                    )
                    st.success("AI Advisory Review completed! View feedback in **Tab 3**.")

        # -------------------------------------------------
        # TAB 3: AI Feedback on My Findings
        # -------------------------------------------------
        with tab3:
            st.markdown("### AI Advisory Feedback on Technical Architect Findings")
            st.caption("AI acts solely as a specialized assistant. Review AI suggestions, accept refinements, or keep your findings exactly as written.")

            reviewed_findings = [f for f in st.session_state['stream_b_findings'] if f.get('ai_feedback')]
            
            if not reviewed_findings:
                st.info("No findings have been reviewed by AI yet. Go to **Tab 2** and click **'Run AI Advisory Review on My Findings'**.")
            else:
                for idx, tf in enumerate(st.session_state['stream_b_findings']):
                    fb = tf.get('ai_feedback')
                    if not fb:
                        continue
                        
                    with st.container():
                        st.markdown(f"#### Finding `{tf['id']}` — {tf['category']}")
                        st.markdown(f"**TA Original Comment:** {tf['finding_text']}")
                        st.markdown(f"**Current Consultant Action:** {tf['consultant_comment']}")

                        # 10-point feedback card
                        dup_badge = "⚠️ Potential Duplicate" if fb.get('is_duplicate') else "✅ Unique Finding"
                        dup_color = "#DC2626" if fb.get('is_duplicate') else "#059669"
                        
                        st.markdown(f"""
                        <div style='background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 14px 18px; margin: 10px 0;'>
                            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
                                <span style='font-size: 0.95rem; font-weight: 700; color: #0F172A;'>AI Advisory Analysis</span>
                                <span style='background: {dup_color}; color: #FFFFFF; font-size: 0.72rem; padding: 3px 10px; border-radius: 5px; font-weight: 700;'>
                                    {dup_badge} ({fb.get('confidence', '88%')} Confidence)
                                </span>
                            </div>
                            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem;'>
                                <div><b>1. Reference / Clause Validation:</b> {fb.get('reference_validation')}</div>
                                <div><b>2. Duplicate Detection:</b> {fb.get('duplicate_detection')}</div>
                                <div><b>3. Drawing Evidence Check:</b> {fb.get('evidence_check')}</div>
                                <div><b>4. Contradiction Detection:</b> {fb.get('contradiction_detection')}</div>
                                <div><b>5. Missing Information:</b> {fb.get('missing_information')}</div>
                                <div><b>6. Suggested Severity:</b> <span style='font-weight: bold; color: #92400E;'>{fb.get('suggested_severity')}</span> (Current: {tf['severity']})</div>
                                <div style='grid-column: span 2;'><b>7. Suggested Consultant Wording:</b> <i>"{fb.get('suggested_consultant_wording')}"</i></div>
                                <div><b>8. Cross-Discipline Context:</b> {fb.get('related_project_context')}</div>
                                <div><b>9. Suggested Classification:</b> {fb.get('classification')}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Decision buttons for TA
                        a_col1, a_col2, a_col3, a_col4 = st.columns(4)
                        if a_col1.button("✅ Accept AI Wording & Clause", key=f"accept_ai_{idx}", use_container_width=True):
                            tf['consultant_comment'] = fb.get('suggested_consultant_wording', tf['consultant_comment'])
                            if fb.get('suggested_severity'):
                                tf['severity'] = fb['suggested_severity']
                            tf['status'] = 'Finalized'
                            tf['is_finalized_for_issue'] = True
                            log_audit_event(
                                action="AI Suggestion Accepted",
                                user="Technical Architect",
                                role="Technical Architect",
                                finding_id=tf['id'],
                                details="Adopted AI consultant wording and severity suggestion."
                            )
                            st.success(f"Adopted AI suggestions for `{tf['id']}`!")
                            st.rerun()

                        if a_col2.button("✋ Ignore AI Suggestion", key=f"ignore_ai_{idx}", use_container_width=True):
                            tf['status'] = 'Finalized'
                            tf['is_finalized_for_issue'] = True
                            log_audit_event(
                                action="AI Suggestion Ignored",
                                user="Technical Architect",
                                role="Technical Architect",
                                finding_id=tf['id'],
                                details="TA maintained human observation and wording as-is."
                            )
                            st.info(f"Maintained human finding for `{tf['id']}`.")
                            st.rerun()

                        if a_col3.button("🗑️ Remove Finding", key=f"rem_ai_{idx}", use_container_width=True):
                            st.session_state['stream_b_findings'].pop(idx)
                            log_audit_event(
                                action="Technical Architect Finding Discarded",
                                user="Technical Architect",
                                role="Technical Architect",
                                finding_id=tf['id'],
                                details="Finding removed based on duplicate detection or self-correction."
                            )
                            st.rerun()

                        if a_col4.button("🔒 Finalize Finding", key=f"fin_dir_{idx}", type="primary", use_container_width=True):
                            tf['status'] = 'Finalized'
                            tf['is_finalized_for_issue'] = True
                            st.rerun()

                        st.divider()

        # -------------------------------------------------
        # TAB 4: Final Review & Issue Package (Convergence)
        # -------------------------------------------------
        with tab4:
            st.markdown("### Final Review & Review Cycle Lock")
            st.caption("Convergence of confirmed AI findings and finalized Technical Architect findings into a unified, locked submittal register.")

            # Compile all finalized items
            stream_a_confirmed = [
                f for f in st.session_state['stream_a_findings']
                if f.get('status') in ['Confirm Issue', 'Modify & Confirm', 'Need Clarification', 'Confirmed']
            ]
            stream_b_finalized = [
                f for f in st.session_state['stream_b_findings']
                if f.get('status') in ['Finalized', 'Ready for Consultant', 'AI Reviewed']
            ]
            all_finalized = stream_a_confirmed + stream_b_finalized

            # Compliance Score Calculation
            score, score_summary = calculate_dynamic_compliance_score(all_finalized)
            threshold = score_summary['threshold']
            is_above = score_summary['is_compliant']

            s1, s2, s3, s4 = st.columns(4)
            score_col = "#059669" if is_above else "#DC2626"
            s1.markdown(f"<div class='metric-card'><div class='card-label'>Compliance Score</div><div class='card-value' style='color:{score_col};'>{score}%</div></div>", unsafe_allow_html=True)
            s2.markdown(f"<div class='metric-card'><div class='card-label'>Finalized AI Items</div><div class='card-value'>{len(stream_a_confirmed)}</div></div>", unsafe_allow_html=True)
            s3.markdown(f"<div class='metric-card'><div class='card-label'>TA Manual Items</div><div class='card-value' style='color:#0284C7;'>{len(stream_b_finalized)}</div></div>", unsafe_allow_html=True)
            s4.markdown(f"<div class='metric-card'><div class='card-label'>Total Issued Comments</div><div class='card-value'>{len(all_finalized)}</div></div>", unsafe_allow_html=True)

            if not is_above:
                st.warning(f"⚠️ **Score Below Threshold:** Current compliance score ({score}%) is below the {threshold}% requirement. Resubmission is mandatory.")
            else:
                st.success(f"✅ **Score Compliant:** Current compliance score ({score}%) meets the {threshold}% requirement.")

            st.markdown("#### Unified Review Register (Preview Before Issuance)")
            if not all_finalized:
                st.warning("No findings have been confirmed in Stream A or finalized in Stream B. Please review and finalize items in Tab 1 and Tab 2.")
            else:
                rows_conv = []
                for item in all_finalized:
                    source_label = "Design Review Finding" if item.get('source') == 'AI' else "Technical Architect Comment"
                    rows_conv.append({
                        'Finding ID': item['id'],
                        'Source (Internal)': item.get('source', 'AI'),
                        'Consultant Display Source': source_label,
                        'Drawing Ref': item.get('drawing_ref', 'AR-GENERAL'),
                        'Category': item.get('category', 'General'),
                        'Severity': item.get('severity', 'Medium'),
                        'Consultant-Facing Comment': item.get('consultant_comment') or item.get('finding_text', ''),
                        'Attachments': len(item.get('attachments', []))
                    })
                st.dataframe(pd.DataFrame(rows_conv), use_container_width=True, hide_index=True)

            # Issuance Authority Gate
            st.divider()
            st.markdown("#### 🔒 Point-in-Time Issuance Authority Gate")
            st.markdown("""
            <div class='warning-box'>
                <b>Strict Review Cycle Rule:</b> Once <b>'Finalize & Issue to Consultant'</b> is confirmed, this review cycle will be <b>locked and frozen against silent edits</b>.
                The Consultant will immediately gain access to their isolated portal. Any future comments must belong to a subsequent review cycle or formal amendment.
            </div>
            """, unsafe_allow_html=True)

            lock_col1, lock_col2 = st.columns([2, 1])
            with lock_col1:
                confirm_lock = st.checkbox(
                    "I confirm that I have reviewed all comments, attachments, and severity ratings, and authorize locking Review Cycle 1 for formal issuance to the Lead Design Consultant.",
                    key="confirm_lock_chk"
                )
            with lock_col2:
                if st.button("📤 Finalize & Issue to Consultant (Lock Cycle 1)", type="primary", disabled=not confirm_lock or not all_finalized, use_container_width=True):
                    cycle_rec = lock_and_issue_cycle_package(
                        project=st.session_state['project'],
                        stage=st.session_state['stage'],
                        discipline=st.session_state['discipline'],
                        cycle_num=st.session_state['current_cycle_num'],
                        submittal_version=st.session_state.get('submittal_ver', 'V1.0'),
                        finalized_findings=all_finalized,
                        compliance_score=score,
                        issued_by="Technical Architect"
                    )
                    st.session_state['active_cycle_record'] = cycle_rec
                    st.success(f"🎉 Review Cycle {st.session_state['current_cycle_num']} is now LOCKED and officially ISSUED to the Consultant!")
                    st.rerun()

    # -----------------------------------------------------
    # TA VIEW 3: Delta Review & Stage Completion
    # -----------------------------------------------------
    elif active_page == "🔄 Delta Review & Sign-Off":
        st.markdown("""
        <div class='header-banner'>
            <div class='title'>
                <span>AI Delta Review & Stage Completion</span>
                <span class='gold-badge'>Human Sign-Off Gate</span>
            </div>
            <div class='subtitle'>Evaluate revised consultant submittals (V2.0+), validate AI delta proposals, and authorize milestone completion.</div>
        </div>
        """, unsafe_allow_html=True)

        cycle_rec = get_active_or_latest_cycle(st.session_state['project'], st.session_state['stage'])
        if not cycle_rec:
            st.info("No review cycle has been issued yet. Complete and issue a review package in the Design Review Studio first.")
        else:
            st.markdown(f"### Active Submittal: `{cycle_rec['project']}` — `{cycle_rec['stage']}` (`{cycle_rec['cycle_id']}`)")
            
            # Ingestion of V2 Resubmission
            st.markdown("#### 1. Ingest Consultant Resubmission (V2.0)")
            r_c1, r_c2 = st.columns([1.5, 1])
            with r_c1:
                resub_up = st.file_uploader("Upload Revised Package (V2.0 PDF / TXT)", type=['pdf', 'txt'], key="v2_upload_ta")
                if st.button("🏢 Load Bukadra V2.0 Sample Resubmission", use_container_width=True):
                    resub_p = BASE_DIR / "sample_schematic_resubmission_v2.txt"
                    if resub_p.exists():
                        st.session_state['v2_resub_text'] = resub_p.read_text(encoding='utf-8')
                        st.session_state['v2_resub_name'] = "015-24_Bukadra_Resubmission_Package_V2.0.txt"
                        st.success("Loaded Bukadra V2.0 Resubmission!")
            with r_c2:
                if st.session_state.get('v2_resub_name'):
                    st.info(f"Active Resubmission: **{st.session_state['v2_resub_name']}**")
                resub_ver_text = st.text_input("Resubmission Version", "V2.0")

            if st.button("🔄 Execute AI Delta Review", type="primary", use_container_width=True):
                raw_v2 = ""
                if resub_up:
                    raw_v2 = extract_text_from_file(resub_up)
                elif st.session_state.get('v2_resub_text'):
                    raw_v2 = st.session_state['v2_resub_text']
                else:
                    resub_p = BASE_DIR / "sample_schematic_resubmission_v2.txt"
                    raw_v2 = resub_p.read_text(encoding='utf-8') if resub_p.exists() else ""

                if raw_v2:
                    delta_items = run_ai_delta_review(cycle_rec['consultant_package'], raw_v2)
                    st.session_state['delta_results'] = delta_items
                    log_audit_event(
                        action="AI Delta Review Executed",
                        user="AI Engine",
                        role="System",
                        review_cycle=cycle_rec['cycle_id'],
                        new_value=f"{len(delta_items)} Items Evaluated",
                        details=f"Compared {resub_ver_text} against issued comments."
                    )
                    upsert_stage_status(
                        project=st.session_state['project'],
                        stage=st.session_state['stage'],
                        discipline=st.session_state['discipline'],
                        status='Delta Review'
                    )
                    st.rerun()

            # Display Delta Review Results
            if 'delta_results' in st.session_state:
                st.markdown("#### 2. AI Delta Review Results (Human Validation Gate)")
                st.markdown("""
                <div class='human-box'>
                    <b>Technical Architect Authority:</b> AI proposes resolution statuses based on textual and schedule evidence. Technical Architect must validate each proposal. <b>AI cannot independently close findings.</b>
                </div>
                """, unsafe_allow_html=True)

                df_delta = pd.DataFrame(st.session_state['delta_results'])
                
                edited_delta = st.data_editor(
                    df_delta,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'finding_id': st.column_config.TextColumn('ID', width='small', disabled=True),
                        'drawing_ref': st.column_config.TextColumn('Drawing Ref', width='small', disabled=True),
                        'issued_comment': st.column_config.TextColumn('Issued Comment', width='large', disabled=True),
                        'consultant_response_type': st.column_config.TextColumn('Consultant Response', width='medium', disabled=True),
                        'ai_delta_status': st.column_config.TextColumn('AI Delta Proposal', width='medium', disabled=True),
                        'detected_evidence': st.column_config.TextColumn('Detected Revision Evidence', width='large', disabled=True),
                        'ta_decision': st.column_config.SelectboxColumn(
                            'TA Final Decision *',
                            options=['Pending Decision', 'Close Finding', 'Keep Open', 'Roll into Cycle 2'],
                            width='medium',
                            required=True
                        ),
                        'ta_note': st.column_config.TextColumn('TA Validation Note', width='medium')
                    },
                    key="delta_editor_v1"
                )
                
                st.session_state['delta_results'] = edited_delta.to_dict('records')

                # Decision Summary
                f_closed = int((edited_delta['ta_decision'] == 'Close Finding').sum())
                f_open = int((edited_delta['ta_decision'].isin(['Keep Open', 'Roll into Cycle 2'])).sum())
                f_pending = int((edited_delta['ta_decision'] == 'Pending Decision').sum())

                d1, d2, d3 = st.columns(3)
                d1.metric("Validated & Closed", f_closed)
                d2.metric("Remaining Open", f_open)
                d3.metric("Pending TA Decision", f_pending)

                # Stage Completion Form
                st.divider()
                st.markdown("#### 3. Milestone Completion Authorization")
                signoff_user = st.text_input("Authorizing Technical Architect", "Senior Technical Architect — Ellington Properties")
                signoff_note = st.text_area("Sign-Off Justification & Notes", f"All material statutory and brand comments validated in V2.0 submittal. Stage authorized.")

                col_c1, col_c2 = st.columns(2)
                
                with col_c1:
                    complete_allowed = (f_open == 0 and f_pending == 0 and len(edited_delta) > 0)
                    if st.button("✅ Complete Stage", type="primary", disabled=not complete_allowed, use_container_width=True):
                        upsert_stage_status(
                            project=st.session_state['project'],
                            stage=st.session_state['stage'],
                            discipline=st.session_state['discipline'],
                            status='Completed',
                            reviewer=signoff_user,
                            note=signoff_note
                        )
                        log_audit_event(
                            action="Design Stage Completed",
                            user=signoff_user,
                            role="Technical Architect",
                            review_cycle=cycle_rec['cycle_id'],
                            previous_value="Delta Review",
                            new_value="Completed",
                            details=f"All {f_closed} findings verified and closed."
                        )
                        st.success(f"🎉 Stage '{st.session_state['stage']}' has been officially marked as COMPLETED!")
                        st.rerun()

                with col_c2:
                    with st.popover("⚠️ Complete Stage with Outstanding Minor Items"):
                        st.markdown("##### Complete with Outstanding Items (Governance Gate)")
                        st.caption("Permitted only when remaining items are non-statutory minor items deferred to the next stage.")
                        deferred_items = st.multiselect(
                            "Select Items to Defer",
                            options=[f['finding_id'] for f in st.session_state['delta_results'] if f.get('ta_decision') != 'Close Finding'],
                            default=[f['finding_id'] for f in st.session_state['delta_results'] if f.get('ta_decision') != 'Close Finding']
                        )
                        target_stage = st.selectbox("Target Future Resolution Stage", ['Detailed Design', 'Tender Package', 'IFC / Construction'])
                        comp_reason = st.text_area("Mandatory Technical Reason for Deferral", placeholder="e.g. Minor façade panel trim details approved for deferral to Detailed Design without impacting authority approvals.")
                        override_ack = st.checkbox("I formally confirm authorization to complete this milestone with deferred items.")

                        if st.button("Authorize Completion with Open Items", type="primary", disabled=not override_ack or not comp_reason):
                            upsert_stage_status(
                                project=st.session_state['project'],
                                stage=st.session_state['stage'],
                                discipline=st.session_state['discipline'],
                                status='Completed with Outstanding Items',
                                reviewer=signoff_user,
                                note=f"Deferred items {deferred_items} to {target_stage}. Reason: {comp_reason}",
                                deferred_items=deferred_items
                            )
                            log_audit_event(
                                action="Stage Completed with Outstanding Items",
                                user=signoff_user,
                                role="Technical Architect",
                                review_cycle=cycle_rec['cycle_id'],
                                new_value="Completed with Outstanding Items",
                                details=f"Deferred {len(deferred_items)} items to {target_stage}."
                            )
                            st.success("Stage authorized as 'Completed with Outstanding Items'!")
                            st.rerun()

    # -----------------------------------------------------
    # TA VIEW 4: Audit Trail & Stage History
    # -----------------------------------------------------
    elif active_page == "📜 Audit Trail & Stage History":
        st.markdown("""
        <div class='header-banner'>
            <div class='title'>
                <span>Immutable Audit Trail & Project History</span>
                <span class='gold-badge'>Enterprise Ledger</span>
            </div>
            <div class='subtitle'>Full traceable record of all actions, authorizations, consultant responses, and review cycle snapshots.</div>
        </div>
        """, unsafe_allow_html=True)

        events = load_audit_trail()
        if not events:
            st.info("No audit events recorded yet.")
        else:
            df_audit = pd.DataFrame(events)
            st.markdown(f"**Total Traceable Events:** `{len(df_audit)}`")
            st.dataframe(df_audit, use_container_width=True, hide_index=True)
            
            st.download_button(
                "📥 Download Audit Trail (CSV)",
                df_audit.to_csv(index=False),
                file_name=f"ellington_audit_trail_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    # -----------------------------------------------------
    # TA VIEW 5: Drawing Scale Feasibility Note
    # -----------------------------------------------------
    elif active_page == "📐 Drawing Scale Analysis Feasibility":
        st.markdown("""
        <div class='header-banner'>
            <div class='title'>
                <span>Technical Investigation: Scale-Based Drawing Analysis</span>
                <span class='gold-badge'>Investigation Note</span>
            </div>
            <div class='subtitle'>Feasibility, technical architecture, and risk analysis for inferring dimensions from visual scale bars.</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        ### Status: 🔍 Capability Under Investigation
        
        **Client Query:** *"Can AI analyze drawings where dimensions are missing but a scale (e.g. 1:100 or graphic scale bar) is provided?"*

        ---

        #### 1. Executive Summary & Feasibility
        - **Current Capability:** The current prototype extracts vector and textual layers (annotations, schedules, title blocks, and specifications). Direct geometric measurement from raster/scanned scale bars is **not active** in V1.
        - **Feasibility Assessment:** **High Feasibility in Phase 2**, subject to vector CAD/BIM or high-resolution PDF source submittals.

        #### 2. Required Source Formats
        | Format | Feasibility | Measurement Accuracy |
        |---|---|---|
        | **Vector PDF (AutoCAD / Revit print)** | High | **± 1.0 mm** (True coordinate vectors accessible) |
        | **DWG / DXF (Direct CAD files)** | Very High | **± 0.01 mm** (Exact native geometry) |
        | **Raster Scan / Scanned PDF** | Low / Risky | **± 50–150 mm** (DPI distortion, page scaling, rotation error) |

        #### 3. Recommended Technical Pipeline (Phase 2 Roadmap)
        1. **Graphic Scale Bar Optical Calibration:** AI detects the graphic scale bar (e.g., 0–5m), measures its exact pixel distance, and calculates the `Pixels-per-Meter (PPM)` transformation matrix.
        2. **Coordinate Normalization:** Calibrates against drawing borders to eliminate paper stretch and non-linear optical distortion.
        3. **Corridor & Room Boundary Extraction:** Runs polygon segmentation on wall centerlines to calculate clear widths and room areas.
        4. **Human Verification Overlay:** Before issuing any dimensional variance to a consultant, the system generates an annotated visual overlay for the Technical Architect to confirm the measured baseline.

        #### 4. Critical Engineering Risks & Limitations
        > **Strict Warning:** Inferring statutory life-safety dimensions (e.g. minimum 30m egress travel distance or 6.0m fire truck access) from raster drawings without vector coordinates presents legal and regulatory liability. Automated measurement must always be calibrated with a human confirmation gate.
        """)

# =========================================================
# CONSULTANT WORKSPACE (STRICTLY ISOLATED)
# =========================================================
else:
    st.markdown("""
    <div class='role-banner'>
        <div>
            <span style='font-size: 1.1rem; font-weight: 700; color: #0B315E;'>Lead Design Consultant Portal</span>
            <span style='background: #0284C7; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.70rem; font-weight: 700; margin-left: 8px;'>EXTERNAL ACCESS</span>
        </div>
        <div style='font-size: 0.85rem; color: #64748B;'>
            Authorized Submittal Partner: <b>Lead Architectural & Engineering Consultant</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    cycle_rec = get_active_or_latest_cycle(st.session_state['project'], st.session_state['stage'])

    if not cycle_rec:
        st.info("ℹ️ No official review comments have been issued to the Consultant yet. The Technical Architect is currently reviewing the package.")
    else:
        # Consultant Navigation
        cons_items = cycle_rec.get('consultant_package', [])

        if active_page == "📋 Issued Comments Register":
            st.markdown(f"### Official Review Register — `{cycle_rec['cycle_id']}`")
            st.caption(f"Issued on: **{cycle_rec['issued_at']}** by **{cycle_rec['issued_by']}** | Status: **{cycle_rec['status']}**")

            st.markdown("""
            <div class='client-box'>
                <b>Official Consultant Notice:</b> The comments below represent authorized review items from Ellington Properties. Review each item and submit your formal responses and revised drawings in the <b>'Submit Responses & Contestations'</b> tab.
            </div>
            """, unsafe_allow_html=True)

            # Display Consultant Items
            display_rows = []
            for it in cons_items:
                display_rows.append({
                    'Item ID': it['finding_id'],
                    'Source': it['source_display'],
                    'Drawing Ref': it['drawing_ref'],
                    'Category': it['category'],
                    'Severity': it['severity'],
                    'Action Required': it['comment'],
                    'Attachments': len(it.get('attachments', [])),
                    'Response Status': it.get('response', {}).get('response_type', 'Pending Response')
                })
            st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)

        elif active_page == "💬 Submit Responses & Contestations":
            st.markdown(f"### Consultant Response Form — `{cycle_rec['cycle_id']}`")
            st.caption("Respond to each comment individually. You may Accept/Rectify, Request Clarification, Contest the finding, or Request an Exception.")

            for idx, it in enumerate(cons_items):
                with st.expander(f"📌 {it['finding_id']} — {it['drawing_ref']} ({it['category']})", expanded=True):
                    st.markdown(f"**Ellington Review Comment:** {it['comment']}")
                    st.markdown(f"**Severity:** `{it['severity']}` | **Reference Source:** {it.get('reference_source', '—')}")
                    
                    if it.get('attachments'):
                        st.markdown(f"📎 **Ellington Attachments:** {', '.join([a['filename'] for a in it['attachments']])}")

                    current_resp = it.get('response', {})
                    r_type = current_resp.get('response_type', 'Pending Response')
                    r_type_idx = CONSULTANT_RESPONSE_OPTIONS.index(r_type) if r_type in CONSULTANT_RESPONSE_OPTIONS else 0

                    c_col1, c_col2 = st.columns([1, 1.5])
                    with c_col1:
                        new_r_type = st.selectbox("Action / Response Type", CONSULTANT_RESPONSE_OPTIONS, index=r_type_idx, key=f"resp_type_{idx}")
                        rev_dwg = st.text_input("Revised Drawing / Sheet Reference", value=current_resp.get('revised_drawing_ref', ''), key=f"rev_dwg_{idx}", placeholder="e.g. Revised on Sheet AR-1001 Rev B")
                    with c_col2:
                        resp_note = st.text_area("Consultant Explanation / Response Note", value=current_resp.get('response_note', ''), key=f"resp_note_{idx}", placeholder="e.g. Setback dimensions updated to 6.0m per DCR. See Sheet AR-1001.")

                    if st.button("💾 Save Item Response", key=f"save_resp_{idx}"):
                        it['response'] = {
                            'response_type': new_r_type,
                            'response_note': resp_note,
                            'revised_drawing_ref': rev_dwg,
                            'responded_at': datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        cycles = load_review_cycles()
                        for c in cycles:
                            if c.get('cycle_id') == cycle_rec['cycle_id']:
                                c['consultant_package'] = cons_items
                                break
                        save_review_cycles(cycles)
                        log_audit_event(
                            action=f"Consultant Responded to {it['finding_id']}",
                            user="Lead Design Consultant",
                            role="Consultant",
                            finding_id=it['finding_id'],
                            review_cycle=cycle_rec['cycle_id'],
                            new_value=new_r_type,
                            details=f"Response Note: '{resp_note}'"
                        )
                        st.success(f"Response saved for `{it['finding_id']}`!")

        elif active_page == "📤 Upload Revised Submittal (V2.0+)":
            st.markdown(f"### Formal Resubmission Package — `{cycle_rec['cycle_id']}`")
            st.caption("Upload your revised drawings, cover letter, and response schedules for Technical Architect delta evaluation.")

            with st.form("consultant_resub_form"):
                resub_pkg_ver = st.text_input("Resubmission Package Version", "V2.0")
                cover_note = st.text_area("Consultant Resubmission Cover Letter / Executive Summary", placeholder="e.g. We submit herewith Revision B of the Schematic Design package incorporating all Ellington design comments...")
                
                up_resub = st.file_uploader("Upload Revised Package Drawings / Specs (PDF / DOCX / TXT)", type=['pdf', 'docx', 'txt'])
                
                submitted_resub = st.form_submit_button("🚀 Submit Revised Package to Ellington", type="primary", use_container_width=True)
                if submitted_resub:
                    upsert_stage_status(
                        project=cycle_rec['project'],
                        stage=cycle_rec['stage'],
                        discipline=cycle_rec['discipline'],
                        status='Resubmission Received',
                        reviewer='Lead Design Consultant',
                        note=cover_note
                    )
                    log_audit_event(
                        action=f"Consultant Resubmission Submitted ({resub_pkg_ver})",
                        user="Lead Design Consultant",
                        role="Consultant",
                        review_cycle=cycle_rec['cycle_id'],
                        previous_value="Issued to Consultant",
                        new_value=f"Resubmission {resub_pkg_ver} Ingested",
                        details=f"Cover Summary: '{cover_note[:100]}...'"
                    )
                    st.success(f"🎉 Resubmission package {resub_pkg_ver} submitted successfully! The Technical Architect has been notified to execute the AI Delta Review.")

        elif active_page == "📜 Consultant Review History":
            st.markdown("### Historical Review Cycle Submittals")
            cycles = load_review_cycles()
            if not cycles:
                st.info("No prior review cycles found.")
            else:
                for c in cycles:
                    with st.expander(f"📁 {c['cycle_id']} — {c['stage']} ({c['issued_at']})", expanded=True):
                        st.markdown(f"**Submittal Version:** {c['submittal_version']} | **Status:** {c['status']}")
                        st.markdown(f"**Total Review Comments:** {c['total_findings']}")
