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

import sys
import os
from pathlib import Path

# Ensure application root directory is always on Python path (critical for Streamlit Community Cloud)
_APP_ROOT = str(Path(__file__).resolve().parent)
if _APP_ROOT not in sys.path:
    sys.path.insert(0, _APP_ROOT)

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
    CONSULTANT_RESPONSE_OPTIONS,
    ACTION_KEY_1_OPEN,
    ACTION_KEY_2_PENDING,
    ACTION_KEY_3_CLOSED,
    ELLINGTON_ACTION_KEYS,
    ACTION_KEY_COLORS
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
    build_ellington_spreadsheet_tracker_html,
    BASE_DIR,
    UPLOADS_DIR
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
        padding: 12px 18px;
        border-radius: 8px;
        margin-bottom: 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Action Key Bar */
    .action-key-bar {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 16px;
        display: flex;
        gap: 20px;
        align-items: center;
        font-size: 0.82rem;
    }
    
    .action-pill-red {
        background: #FEF2F2;
        color: #991B1B;
        border: 1px solid #EF4444;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
    }
    
    .action-pill-amber {
        background: #FFFBEB;
        color: #92400E;
        border: 1px solid #F59E0B;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
    }
    
    .action-pill-green {
        background: #F0FDF4;
        color: #065F46;
        border: 1px solid #10B981;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
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
    
    .gap-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
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
        help="Switch between Technical Architect (internal authorization) and Lead Design Consultant (external review & resubmission)."
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
            "📋 Review Register & Gap Responses",
            "📤 Submit Formal Resubmission (V2.0+)",
            "📜 Consultant Review History"
        ]
        if 'cons_nav' not in st.session_state or st.session_state['cons_nav'] not in CONS_PAGES:
            st.session_state['cons_nav'] = CONS_PAGES[0]
        active_page = st.radio("Consultant Navigation", CONS_PAGES, key="cons_nav", label_visibility="collapsed")

    st.divider()
    st.markdown(f"**Current Milestone:** `{st.session_state['stage']}`")
    st.markdown(f"**Review Cycle:** `Cycle {st.session_state['current_cycle_num']}`")
    st.caption("🔒 **Human Authority Gate: Active**")

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
        
        # Ellington Action Key Legend Bar
        st.markdown("""
        <div class='action-key-bar'>
            <b>Ellington Action Key:</b>
            <div><span class='action-pill-red'>Action 1 - OPEN</span> Requires response/correction before acceptance</div>
            <div><span class='action-pill-amber'>Action 2 - PENDING</span> Requires response during next design stage</div>
            <div><span class='action-pill-green'>Action 3 - CLOSED</span> Record comment (accepted)</div>
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
                    details=f"Evaluated against Meydan Horizon DCR Vol II and Authority rules."
                )
                upsert_stage_status(
                    project=st.session_state['project'],
                    stage=st.session_state['stage'],
                    discipline=st.session_state['discipline'],
                    status='Technical Architect Review',
                    reviewer='Technical Architect'
                )
                st.rerun()

        # Studio Tabs
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
            st.caption("AI-generated against Meydan Horizon DCR Vol II, Dubai Municipality DBC 2021, and UAE Fire Code 2018.")

            if not st.session_state['stream_a_findings']:
                st.info("Run AI First-Pass Review above to populate Stream A findings.")
            else:
                # Ensure ta_comment is populated
                for item in st.session_state['stream_a_findings']:
                    if 'ta_comment' not in item or not item['ta_comment']:
                        item['ta_comment'] = item.get('consultant_comment') or item.get('finding_text', '')
                
                df_a = pd.DataFrame(st.session_state['stream_a_findings'])
                
                open_count = int(df_a['action_key'].str.startswith('1').sum())
                pending_count = int(df_a['action_key'].str.startswith('2').sum())
                closed_count = int(df_a['action_key'].str.startswith('3').sum())

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total AI Findings", len(df_a))
                m2.markdown(f"<div class='metric-card'><div class='card-label'>🔴 Action 1 - OPEN</div><div class='card-value' style='color:#DC2626;'>{open_count}</div></div>", unsafe_allow_html=True)
                m3.markdown(f"<div class='metric-card'><div class='card-label'>🟡 Action 2 - PENDING</div><div class='card-value' style='color:#D97706;'>{pending_count}</div></div>", unsafe_allow_html=True)
                m4.markdown(f"<div class='metric-card'><div class='card-label'>🟢 Action 3 - CLOSED</div><div class='card-value' style='color:#059669;'>{closed_count}</div></div>", unsafe_allow_html=True)

                st.markdown("""
                <div class='human-box'>
                    <b>Technical Architect Governance:</b> Assign the Ellington Action Key (1-Open, 2-Pending, 3-Closed). Only Action 1 and 2 will require consultant response.
                </div>
                """, unsafe_allow_html=True)

                edited_a = st.data_editor(
                    df_a,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'id': st.column_config.TextColumn('Finding ID', width='small', disabled=True),
                        'drawing_ref': st.column_config.TextColumn('Drawing Ref', width='small', disabled=True),
                        'category': st.column_config.TextColumn('Category', width='medium', disabled=True),
                        'reference_source': st.column_config.TextColumn('Authority / DCR Source', width='medium', disabled=True),
                        'action_key': st.column_config.SelectboxColumn('Ellington Action Key *', options=ELLINGTON_ACTION_KEYS, width='medium', required=True),
                        'ta_comment': st.column_config.TextColumn('TA Review Comments', width='large'),
                    },
                    key="editor_stream_a_v1"
                )
                
                if st.button("💾 Save Stream A Decisions & Action Keys", key="save_stream_a_btn", type="primary"):
                    records = edited_a.to_dict('records')
                    for r in records:
                        if 'ta_comment' in r:
                            r['consultant_comment'] = r['ta_comment']
                    st.session_state['stream_a_findings'] = records
                    log_audit_event(
                        action="Stream A Action Keys Updated",
                        user="Technical Architect",
                        role="Technical Architect",
                        review_cycle=f"Cycle {st.session_state['current_cycle_num']}",
                        details="TA updated Action Keys per Ellington spreadsheet standard."
                    )
                    st.success("Decisions saved successfully!")
                    st.rerun()

        # -------------------------------------------------
        # TAB 2: My Findings (Stream B - Manual TA Review)
        # -------------------------------------------------
        with tab2:
            st.markdown("### Stream B: Technical Architect Independent Findings")
            st.caption("Add subjective observations, spatial qualities, craftsmanship standards, or regulatory gaps identified through human expertise.")

            with st.expander("➕ Add New Technical Architect Finding", expanded=False):
                with st.form("add_ta_finding_form", clear_on_submit=True):
                    f_c1, f_c2 = st.columns([1, 1])
                    dwg_ref = f_c1.text_input("Drawing / Document Reference *", placeholder="e.g. AR-1002 / Detail Section D-04")
                    finding_cat = f_c2.selectbox("Finding Category", FINDING_CATEGORIES, index=0)

                    f_c3, f_c4, f_c5 = st.columns(3)
                    disc = f_c3.selectbox("Discipline", ['Architecture & Planning', 'Brand & Finishes', 'Structural', 'MEP', 'Landscape'])
                    sev = f_c4.selectbox("Severity *", SEVERITIES, index=2)
                    act_key = f_c5.selectbox("Action Key *", ELLINGTON_ACTION_KEYS, index=0)

                    finding_desc = st.text_area("Finding Description / Observation *", placeholder="e.g. Balcony soffit finish detail lacks drip groove; risk of rainwater staining on champagne bronze panels.")
                    cons_comment = st.text_area("Consultant-Facing Action Required *", placeholder="e.g. Provide continuous architectural drip profile detail on Sheet AR-3004.")
                    
                    f_c6, f_c7 = st.columns(2)
                    ref_source = f_c6.text_input("Reference Standard (optional for design judgments)", placeholder="e.g. Meydan Horizon Vol II / Ellington Façade Standard")
                    clause_ref = f_c7.text_input("Clause / Section (optional)", placeholder="e.g. Clause 8.2 or Qualitative Intent")

                    internal_note = st.text_input("Internal Note (strictly hidden from consultant)", placeholder="e.g. Discuss with Senior Project Director.")

                    # Visual Drawing Crop / Sketch Upload (Dual Method)
                    st.markdown("##### 📎 Attach Drawing Excerpt Thumbnail / Sketch (The Dual Method)")
                    att_c1, att_c2 = st.columns([1.5, 1])
                    uploaded_att = att_c1.file_uploader("Upload PNG / JPG / PDF (Drawing Excerpt, Sketch, Markup)", type=['pdf', 'png', 'jpg', 'jpeg'], key="ta_att_uploader")
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
                                'reference_source': ref_source or 'Design Judgment / Professional Opinion',
                                'clause': clause_ref or '—',
                                'finding_text': finding_desc,
                                'evidence_text': 'Manual Human Review Finding',
                                'severity': sev,
                                'action_key': act_key,
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
                                details=f"Action Key: {act_key[:10]}, Category: {finding_cat}."
                            )
                            st.success(f"Finding `{new_id}` saved as Draft!")
                            st.rerun()

            st.markdown("#### Registered Technical Architect Findings")
            if not st.session_state['stream_b_findings']:
                st.info("No manual findings added yet. Click **'+ Add New Technical Architect Finding'** above.")
            else:
                for idx, tf in enumerate(st.session_state['stream_b_findings']):
                    with st.container():
                        act_badge = "<span class='action-pill-red'>1 - OPEN</span>" if tf.get('action_key', '').startswith('1') else ("<span class='action-pill-amber'>2 - PENDING</span>" if tf.get('action_key', '').startswith('2') else "<span class='action-pill-green'>3 - CLOSED</span>")
                        st.markdown(f"""
                        <div class='gap-card' style='border-left: 5px solid #0B315E;'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <div>
                                    <span style='font-size: 1.1rem; font-weight: 700; color: #0F172A;'>`{tf['id']}` — {tf['category']}</span>
                                    <span style='margin-left: 10px;'>{act_badge}</span>
                                    <span style='margin-left: 6px; background: #E0E7FF; color: #3730A3; font-size: 0.72rem; padding: 3px 8px; border-radius: 4px; font-weight: 700;'>Source: {tf['source']}</span>
                                </div>
                                <div style='font-size: 0.82rem; color: #64748B;'>Dwg: <b>{tf['drawing_ref']}</b></div>
                            </div>
                            <div style='margin-top: 8px; font-size: 0.90rem; color: #1E293B;'>
                                <b>Observation:</b> {tf['finding_text']}
                            </div>
                            <div style='margin-top: 4px; font-size: 0.88rem; color: #0369A1;'>
                                <b>Consultant Action:</b> {tf['consultant_comment']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        btn_c1, btn_c2 = st.columns([1, 1])
                        if btn_c1.button(f"🗑️ Delete", key=f"del_tf_{idx}"):
                            st.session_state['stream_b_findings'].pop(idx)
                            st.rerun()
                        if btn_c2.button(f"✅ Mark Finalized", key=f"fin_tf_{idx}"):
                            tf['status'] = 'Finalized'
                            st.rerun()

                st.divider()
                if st.button("🚀 Run AI Advisory Review on My Findings", type="primary", use_container_width=True):
                    raw_text = st.session_state.get('raw_submittal_text', '')
                    for f in st.session_state['stream_b_findings']:
                        f['ai_feedback'] = run_ai_review_on_ta_finding(f, st.session_state['stream_a_findings'], raw_text)
                        f['status'] = 'AI Reviewed'
                    st.success("AI Advisory Review completed! View feedback in **Tab 3**.")

        # -------------------------------------------------
        # TAB 3: AI Feedback on My Findings
        # -------------------------------------------------
        with tab3:
            st.markdown("### AI Advisory Feedback on Technical Architect Findings")
            st.caption("AI acts solely as a specialized assistant. Review AI suggestions, accept refinements, or keep your findings exactly as written.")

            reviewed = [f for f in st.session_state['stream_b_findings'] if f.get('ai_feedback')]
            if not reviewed:
                st.info("No findings reviewed yet. Go to **Tab 2** and click **'Run AI Advisory Review on My Findings'**.")
            else:
                for idx, tf in enumerate(st.session_state['stream_b_findings']):
                    fb = tf.get('ai_feedback')
                    if not fb:
                        continue
                    with st.container():
                        st.markdown(f"#### Finding `{tf['id']}` — {tf['category']}")
                        st.markdown(f"""
                        <div style='background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 14px 18px; margin: 10px 0;'>
                            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem;'>
                                <div><b>1. Reference Check:</b> {fb.get('reference_validation')}</div>
                                <div><b>2. Duplicate Check:</b> {fb.get('duplicate_detection')}</div>
                                <div><b>3. Drawing Evidence:</b> {fb.get('evidence_check')}</div>
                                <div><b>4. Contradiction Check:</b> {fb.get('contradiction_detection')}</div>
                                <div style='grid-column: span 2;'><b>7. Suggested Phrasing:</b> <i>"{fb.get('suggested_consultant_wording')}"</i></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        a1, a2 = st.columns(2)
                        if a1.button("✅ Accept AI Wording & Clause", key=f"acc_fb_{idx}"):
                            tf['consultant_comment'] = fb.get('suggested_consultant_wording', tf['consultant_comment'])
                            tf['status'] = 'Finalized'
                            st.rerun()
                        if a2.button("✋ Ignore & Finalize", key=f"ign_fb_{idx}"):
                            tf['status'] = 'Finalized'
                            st.rerun()
                        st.divider()

        # -------------------------------------------------
        # TAB 4: Final Review & Issue Package (Convergence)
        # -------------------------------------------------
        with tab4:
            st.markdown("### Final Review & Review Cycle Lock")
            st.caption("Convergence of confirmed AI findings and finalized Technical Architect findings into Ellington's official Comments Tracker.")

            stream_a_confirmed = [f for f in st.session_state['stream_a_findings'] if f.get('status') in ['Confirm Issue', 'Modify & Confirm', 'Need Clarification', 'Confirmed']]
            stream_b_finalized = [f for f in st.session_state['stream_b_findings'] if f.get('status') in ['Finalized', 'Ready for Consultant', 'AI Reviewed']]
            all_finalized = stream_a_confirmed + stream_b_finalized

            score, score_summary = calculate_dynamic_compliance_score(all_finalized)
            threshold = score_summary['threshold']
            is_above = score_summary['is_compliant']

            s1, s2, s3, s4 = st.columns(4)
            score_col = "#059669" if is_above else "#DC2626"
            s1.markdown(f"<div class='metric-card'><div class='card-label'>Compliance Score</div><div class='card-value' style='color:{score_col};'>{score}%</div></div>", unsafe_allow_html=True)
            s2.markdown(f"<div class='metric-card'><div class='card-label'>Total Action Items</div><div class='card-value'>{len(all_finalized)}</div></div>", unsafe_allow_html=True)
            s3.markdown(f"<div class='metric-card'><div class='card-label'>🔴 Action 1 (Open)</div><div class='card-value' style='color:#DC2626;'>{sum(1 for f in all_finalized if f.get('action_key', '').startswith('1'))}</div></div>", unsafe_allow_html=True)
            s4.markdown(f"<div class='metric-card'><div class='card-label'>🟡 Action 2 (Pending)</div><div class='card-value' style='color:#D97706;'>{sum(1 for f in all_finalized if f.get('action_key', '').startswith('2'))}</div></div>", unsafe_allow_html=True)

            if all_finalized:
                rows_conv = []
                for item in all_finalized:
                    rows_conv.append({
                        'No.': len(rows_conv) + 1,
                        'Finding ID': item['id'],
                        'Source': "Design Review Finding" if item.get('source') == 'AI' else "Technical Architect Comment",
                        'Discipline': item.get('discipline', st.session_state['discipline']),
                        'Drawing Ref': item.get('drawing_ref', 'AR-GENERAL'),
                        'Category': item.get('category', 'General'),
                        'Action Key': item.get('action_key', '1 - OPEN'),
                        'Comment Details': item.get('consultant_comment') or item.get('finding_text', '')
                    })
                st.dataframe(pd.DataFrame(rows_conv), use_container_width=True, hide_index=True)

            st.divider()
            st.markdown("#### 🔒 Point-in-Time Issuance Authority Gate")
            lock_col1, lock_col2 = st.columns([2, 1])
            with lock_col1:
                confirm_lock = st.checkbox(
                    "I confirm authorization to lock Review Cycle 1 and formally issue comments to the Lead Design Consultant.",
                    key="confirm_lock_chk"
                )
            with lock_col2:
                if st.button("📤 Finalize & Issue to Consultant (Lock Cycle 1)", type="primary", disabled=not confirm_lock or not all_finalized, use_container_width=True):
                    raw_submittal = st.session_state.get('raw_submittal_text', '')
                    submittal_name = st.session_state.get('submittal_filename', '015-24_Bukadra_Plot_6117262_Schematic_Architecture_V1.txt')
                    
                    cycle_rec = lock_and_issue_cycle_package(
                        project=st.session_state['project'],
                        stage=st.session_state['stage'],
                        discipline=st.session_state['discipline'],
                        cycle_num=st.session_state['current_cycle_num'],
                        submittal_version=st.session_state.get('submittal_ver', 'V1.0'),
                        finalized_findings=all_finalized,
                        compliance_score=score,
                        issued_by="Technical Architect",
                        submittal_text=raw_submittal,
                        submittal_filename=submittal_name
                    )
                    st.success("🎉 Review Cycle 1 officially LOCKED and ISSUED to the Consultant!")
                    st.rerun()

    # -----------------------------------------------------
    # TA VIEW 3: Delta Review & Sign-Off
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
            
            # Download Ellington Spreadsheet Tracker HTML
            tracker_html = build_ellington_spreadsheet_tracker_html(cycle_rec)
            st.download_button(
                "📥 Download Ellington Design Comments Tracker (Official Spreadsheet HTML)",
                tracker_html,
                file_name=f"ellington_comments_tracker_{cycle_rec['stage'].replace(' ', '_')}.html",
                mime="text/html",
                use_container_width=True
            )

            st.markdown("#### Ingest Consultant Resubmission (V2.0)")
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
                    upsert_stage_status(
                        project=st.session_state['project'],
                        stage=st.session_state['stage'],
                        discipline=st.session_state['discipline'],
                        status='Delta Review'
                    )
                    st.rerun()

            if 'delta_results' in st.session_state:
                st.markdown("#### AI Delta Review Results (Validation Gate)")
                df_delta = pd.DataFrame(st.session_state['delta_results'])
                
                edited_delta = st.data_editor(
                    df_delta,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'finding_id': st.column_config.TextColumn('ID', width='small', disabled=True),
                        'drawing_ref': st.column_config.TextColumn('Drawing Ref', width='small', disabled=True),
                        'issued_comment': st.column_config.TextColumn('Issued Comment', width='large', disabled=True),
                        'consultant_response_note': st.column_config.TextColumn('Consultant Response (Date-Stamped)', width='medium', disabled=True),
                        'ai_delta_status': st.column_config.TextColumn('AI Delta Proposal', width='medium', disabled=True),
                        'ta_decision': st.column_config.SelectboxColumn('TA Decision *', options=['Pending Decision', 'Close Finding', 'Keep Open', 'Roll into Cycle 2'], width='medium', required=True),
                        'ta_note': st.column_config.TextColumn('TA Validation Note', width='medium')
                    },
                    key="delta_editor_v1"
                )
                
                st.session_state['delta_results'] = edited_delta.to_dict('records')
                f_closed = int((edited_delta['ta_decision'] == 'Close Finding').sum())
                f_open = int((edited_delta['ta_decision'].isin(['Keep Open', 'Roll into Cycle 2'])).sum())

                d1, d2 = st.columns(2)
                d1.metric("Validated & Closed (Action 3)", f_closed)
                d2.metric("Remaining Open (Action 1 / 2)", f_open)

                st.divider()
                signoff_user = st.text_input("Authorizing Technical Architect", "Senior Technical Architect — Ellington Properties")
                signoff_note = st.text_area("Sign-Off Justification", f"All material statutory and brand comments validated in V2.0 submittal. Stage authorized.")

                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    complete_allowed = (f_open == 0 and len(edited_delta) > 0)
                    if st.button("✅ Complete Stage", type="primary", disabled=not complete_allowed, use_container_width=True):
                        upsert_stage_status(
                            project=st.session_state['project'],
                            stage=st.session_state['stage'],
                            discipline=st.session_state['discipline'],
                            status='Completed',
                            reviewer=signoff_user,
                            note=signoff_note
                        )
                        st.success(f"🎉 Stage '{st.session_state['stage']}' marked as COMPLETED!")
                        st.rerun()

                with col_c2:
                    with st.popover("⚠️ Complete Stage with Outstanding Minor Items"):
                        deferred_items = st.multiselect(
                            "Select Items to Defer to Next Stage",
                            options=[f['finding_id'] for f in st.session_state['delta_results'] if f.get('ta_decision') != 'Close Finding'],
                            default=[f['finding_id'] for f in st.session_state['delta_results'] if f.get('ta_decision') != 'Close Finding']
                        )
                        target_stage = st.selectbox("Target Resolution Stage", ['Detailed Design', 'Tender Package', 'IFC / Construction'])
                        comp_reason = st.text_area("Technical Justification for Deferral", placeholder="e.g. Non-statutory façade trim approved for deferral to Detailed Design.")
                        if st.button("Authorize Completion with Open Items", type="primary", disabled=not comp_reason):
                            upsert_stage_status(
                                project=st.session_state['project'],
                                stage=st.session_state['stage'],
                                discipline=st.session_state['discipline'],
                                status='Completed with Outstanding Items',
                                reviewer=signoff_user,
                                note=f"Deferred items {deferred_items} to {target_stage}. Reason: {comp_reason}",
                                deferred_items=deferred_items
                            )
                            st.success("Authorized with Outstanding Items!")
                            st.rerun()

    # -----------------------------------------------------
    # TA VIEW 4: Audit Trail
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
            st.dataframe(df_audit, use_container_width=True, hide_index=True)
            st.download_button(
                "📥 Download Audit Trail (CSV)",
                df_audit.to_csv(index=False),
                file_name=f"ellington_audit_trail_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    # -----------------------------------------------------
    # TA VIEW 5: Drawing Scale Analysis Feasibility
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
        **Client Query:** *"Can AI analyze drawings where dimensions are missing but a graphic scale bar is provided?"*
        - **Feasibility:** High Feasibility in Phase 2 for vector PDFs / CAD (±0.01mm–1.0mm). High risk on scanned rasters (±50–150mm distortion).
        - **Roadmap:** Implement Optical Scale Bar Calibration (PPM matrix), polygon segmentation, and mandatory human overlay verification.
        """)

# =========================================================
# CONSULTANT WORKSPACE (STRICTLY ISOLATED & EMPOWERED)
# =========================================================
else:
    st.markdown("""
    <div class='role-banner'>
        <div>
            <span style='font-size: 1.15rem; font-weight: 700; color: #0B315E;'>Lead Design Consultant Collaboration Portal</span>
            <span style='background: #0284C7; color: white; padding: 3px 10px; border-radius: 5px; font-size: 0.72rem; font-weight: 700; margin-left: 8px;'>EXTERNAL ACCESS</span>
        </div>
        <div style='font-size: 0.85rem; color: #64748B;'>
            Authorized Submittal Partner: <b>Lead Architectural & Engineering Consultant</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    cycle_rec = get_active_or_latest_cycle(st.session_state['project'], st.session_state['stage'])

    if not cycle_rec:
        st.info("ℹ️ No official review comments have been issued to the Consultant yet. The Technical Architect is currently reviewing the submittal package.")
    else:
        cons_items = cycle_rec.get('consultant_package', [])

        # Ellington Action Key Legend Bar
        st.markdown("""
        <div class='action-key-bar'>
            <b>Ellington Action Key:</b>
            <div><span class='action-pill-red'>Action 1 - OPEN</span> Requires response/correction before acceptance</div>
            <div><span class='action-pill-amber'>Action 2 - PENDING</span> Requires response during next design stage</div>
            <div><span class='action-pill-green'>Action 3 - CLOSED</span> Record comment (accepted)</div>
        </div>
        """, unsafe_allow_html=True)

        pkg_name = cycle_rec.get('submittal_filename', '015-24_Bukadra_Plot_6117262_Schematic_Architecture_V1.txt')
        pkg_text = cycle_rec.get('submittal_text', '')
        if not pkg_text:
            sample_p = BASE_DIR / "sample_schematic_arch.txt"
            pkg_text = sample_p.read_text(encoding='utf-8') if sample_p.exists() else ""

        # Submittal Package Viewer & Download
        with st.container():
            st.markdown(f"""
            <div style='background: #F8FAFC; border: 1px solid #CBD5E1; border-left: 5px solid #D4AF37; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='font-size: 1.05rem; font-weight: 700; color: #0F172A; font-family: Outfit, sans-serif;'>
                            📂 Submittal Design Package & Reference Drawings (The Dual Method)
                        </div>
                        <div style='font-size: 0.82rem; color: #64748B; margin-top: 3px;'>
                            <b>Project:</b> {cycle_rec['project']} &nbsp;|&nbsp; 
                            <b>Stage:</b> {cycle_rec['stage']} &nbsp;|&nbsp; 
                            <b>Cycle:</b> <span style='background:#E0E7FF; color:#3730A3; padding:2px 6px; border-radius:4px; font-weight:bold;'>{cycle_rec['cycle_id']}</span> &nbsp;|&nbsp;
                            <b>File:</b> <code>{pkg_name}</code>
                        </div>
                    </div>
                    <span style='background: #10B981; color: white; padding: 4px 12px; border-radius: 6px; font-size: 0.72rem; font-weight: 700;'>
                        LOCKED REVIEW CYCLE
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            d_c1, d_c2 = st.columns([1, 1])
            with d_c1:
                with st.expander("👁️ View Full Drawing Package Text, Annotations & Schedules", expanded=False):
                    st.text(pkg_text[:12000] + ("\n... [Truncated for preview]" if len(pkg_text) > 12000 else ""))
            with d_c2:
                tracker_html = build_ellington_spreadsheet_tracker_html(cycle_rec)
                st.download_button(
                    "📥 Download Official Spreadsheet Comments Tracker (HTML)",
                    tracker_html,
                    file_name=f"ellington_comments_tracker_{cycle_rec['stage'].replace(' ', '_')}.html",
                    mime="text/html",
                    use_container_width=True
                )

        # -------------------------------------------------
        # VIEW 1: Review Register & Gap Responses (Combined & Empowered)
        # -------------------------------------------------
        if active_page == "📋 Review Register & Gap Responses":
            st.markdown("### Official Review Comments & Consultant Response Actions")

            total_gaps = len(cons_items)
            responded_count = sum(1 for it in cons_items if it.get('response', {}).get('response_type') not in ['Pending Response', '', None])
            open_count = sum(1 for it in cons_items if it.get('action_code') == '1' or it.get('action_key', '').startswith('1'))
            pending_count = sum(1 for it in cons_items if it.get('action_code') == '2' or it.get('action_key', '').startswith('2'))

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Review Comments", total_gaps)
            m2.metric("Responses Recorded", responded_count, delta="Completed" if responded_count == total_gaps else None)
            m3.markdown(f"<div class='metric-card'><div class='card-label'>🔴 Action 1 - OPEN</div><div class='card-value' style='color:#DC2626;'>{open_count}</div></div>", unsafe_allow_html=True)
            m4.markdown(f"<div class='metric-card'><div class='card-label'>🟡 Action 2 - PENDING</div><div class='card-value' style='color:#D97706;'>{pending_count}</div></div>", unsafe_allow_html=True)

            st.divider()

            for idx, it in enumerate(cons_items):
                fid = it['finding_id']
                cat = it['category']
                dwg = it['drawing_ref']
                sev = it['severity']
                src = it['source_display']
                comment = it['comment']
                curr_resp = it.get('response', {})
                resp_status = curr_resp.get('response_type', 'Pending Response')
                is_responded = resp_status != 'Pending Response'
                act_key_str = it.get('action_key', '1 - OPEN')

                act_badge = "<span class='action-pill-red'>Action 1 - OPEN</span>" if act_key_str.startswith('1') else ("<span class='action-pill-amber'>Action 2 - PENDING</span>" if act_key_str.startswith('2') else "<span class='action-pill-green'>Action 3 - CLOSED</span>")

                with st.container():
                    st.markdown(f"""
                    <div class='gap-card' style='border-left: 5px solid {("#10B981" if is_responded else ("#EF4444" if act_key_str.startswith("1") else "#F59E0B"))};'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <span style='font-size: 1.15rem; font-weight: 800; color: #0F172A;'>Item #{idx+1}: `{fid}`</span>
                                <span style='margin-left: 10px;'>{act_badge}</span>
                                <span style='margin-left: 6px; background: #E0E7FF; color: #3730A3; padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700;'>{src}</span>
                            </div>
                            <span style='background: {("#ECFDF5" if is_responded else "#FFFBEB")}; color: {("#047857" if is_responded else "#B45309")}; padding: 4px 12px; border-radius: 6px; font-size: 0.80rem; font-weight: 700;'>
                                {("✅ Response Saved (" + resp_status + ")") if is_responded else "⏳ Response Required"}
                            </span>
                        </div>
                        <div style='margin-top: 8px; font-size: 0.90rem; color: #334155;'>
                            <b>Drawing / Sheet Reference:</b> <code>{dwg}</code> &nbsp;|&nbsp; <b>Category:</b> {cat}
                        </div>
                        <div style='margin-top: 8px; font-size: 0.95rem; color: #0F172A; background: #F1F5F9; padding: 12px 16px; border-radius: 6px;'>
                            <b>Ellington Required Action:</b><br>{comment}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Technical Architect Visual Markup / Attachments Display
                    ta_atts = it.get('attachments', [])
                    if ta_atts:
                        st.markdown(f"**📎 Drawing Crop / Visual Markup (The Dual Method):**")
                        for a_idx, att in enumerate(ta_atts):
                            att_path = Path(att.get('stored_path', ''))
                            a_col1, a_col2 = st.columns([2, 1])
                            with a_col1:
                                st.caption(f"📄 **{att.get('file_type', 'File')}:** `{att.get('filename')}`")
                                if att_path.exists() and att_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                                    st.image(str(att_path), caption=f"Visual Markup: {att.get('filename')}", use_container_width=True)
                            with a_col2:
                                if att_path.exists():
                                    st.download_button(
                                        f"📥 Download {att.get('filename')}",
                                        att_path.read_bytes(),
                                        file_name=att.get('filename'),
                                        key=f"dl_ta_att_{idx}_{a_idx}",
                                        use_container_width=True
                                    )

                    # Interactive Response and File Upload
                    with st.expander(f"✍️ Update Consultant Response & Upload Revised Drawing for `{fid}`", expanded=not is_responded):
                        c1, c2 = st.columns([1, 1.2])
                        with c1:
                            r_type_idx = CONSULTANT_RESPONSE_OPTIONS.index(resp_status) if resp_status in CONSULTANT_RESPONSE_OPTIONS else 1
                            new_r_type = st.selectbox(
                                "Your Response / Action Type *",
                                CONSULTANT_RESPONSE_OPTIONS[1:],
                                index=r_type_idx - 1 if r_type_idx > 0 else 0,
                                key=f"resp_type_sel_{idx}"
                            )
                            rev_dwg = st.text_input(
                                "Revised Drawing / Sheet Reference *",
                                value=curr_resp.get('revised_drawing_ref', dwg + " Rev B"),
                                key=f"rev_dwg_input_{idx}",
                                placeholder="e.g. Revised on Sheet AR-1001 Rev B"
                            )
                        with c2:
                            raw_note = curr_resp.get('response_note', '')
                            # Strip existing prefix for editing if present
                            clean_note = re.sub(r'^\[CONSULTANT [^\]]+\]:\s*', '', raw_note)
                            resp_note = st.text_area(
                                "Consultant Explanation / Technical Justification *",
                                value=clean_note,
                                key=f"resp_note_input_{idx}",
                                placeholder="e.g. Noted. Front setback dimension updated to 6.0m per Meydan Horizon DCR Cl. 4.2."
                            )

                        st.markdown("##### 📎 Upload Supporting Document / Drawing for this Gap")
                        u_col1, u_col2 = st.columns([1.5, 1])
                        cons_gap_file = u_col1.file_uploader(
                            f"Upload PDF / PNG / JPG / DWG for {fid}",
                            type=['pdf', 'png', 'jpg', 'jpeg', 'txt'],
                            key=f"cons_file_{idx}"
                        )
                        cons_file_desc = u_col2.text_input("Drawing / Document Title", value=f"Revised_{fid}", key=f"cons_file_desc_{idx}")

                        if st.button(f"💾 Save & Submit Response for {fid}", key=f"save_btn_{idx}", type="primary"):
                            resp_atts = curr_resp.get('attachments', [])
                            if cons_gap_file:
                                att_res = save_uploaded_file(cons_gap_file, "Consultant Revised Drawing", "Consultant Visible", uploaded_by="Lead Design Consultant")
                                resp_atts.append(att_res)

                            # Format date-stamped note matching Ellington spreadsheet standard
                            today_str = datetime.now().strftime("%d-%m-%Y")
                            user_note_text = resp_note or "Noted. Revision acknowledged and incorporated."
                            stamped_note = f"[CONSULTANT {today_str}]: {user_note_text}"

                            it['response'] = {
                                'response_type': new_r_type,
                                'response_note': stamped_note,
                                'revised_drawing_ref': rev_dwg,
                                'attachments': resp_atts,
                                'responded_at': datetime.now().strftime("%Y-%m-%d %H:%M")
                            }

                            cycles = load_review_cycles()
                            for c in cycles:
                                if c.get('cycle_id') == cycle_rec['cycle_id']:
                                    c['consultant_package'] = cons_items
                                    break
                            save_review_cycles(cycles)

                            log_audit_event(
                                action=f"Consultant Logged Response for {fid}",
                                user="Lead Design Consultant",
                                role="Consultant",
                                finding_id=fid,
                                review_cycle=cycle_rec['cycle_id'],
                                new_value=new_r_type,
                                details=f"Note: '{stamped_note}'."
                            )
                            st.success(f"🎉 Response recorded successfully for `{fid}` in Ellington format: '{stamped_note}'")
                            st.rerun()

                        if curr_resp.get('attachments'):
                            st.markdown(f"**Uploaded Consultant Files:**")
                            for c_att in curr_resp.get('attachments', []):
                                st.info(f"📄 `{c_att.get('filename')}` ({c_att.get('size_display')}) — Uploaded at {c_att.get('timestamp')}")

                    st.divider()

        # -------------------------------------------------
        # VIEW 2: Formal Resubmission Package Submission (V2.0+)
        # -------------------------------------------------
        elif active_page == "📤 Submit Formal Resubmission (V2.0+)":
            st.markdown(f"### Formal Package Resubmission — `{cycle_rec['cycle_id']}`")
            st.caption("Once you have updated your comments for all gaps, submit your complete revised submittal package (V2.0+) to notify the Technical Architect.")

            with st.form("formal_resub_form"):
                pkg_ver = st.text_input("Submittal Revision Version", "V2.0")
                cover_summary = st.text_area(
                    "Executive Cover Letter / Transmittal Summary",
                    value="We submit herewith Revision B (V2.0) of the Schematic Design package incorporating all Ellington design comments, dimensioned setbacks per Meydan Horizon DCR Vol II, updated parking allocations, and fire egress analysis.",
                    height=120
                )

                st.markdown("##### 📁 Upload Complete Revised Design Package (Drawings & Specifications)")
                c_up1, c_up2 = st.columns([1.5, 1])
                rev_package_file = c_up1.file_uploader("Upload Master Revised PDF / TXT / DOCX Package", type=['pdf', 'txt', 'docx'], key="master_v2_upload")
                quick_sample = c_up2.checkbox("Or use pre-indexed Bukadra V2.0 Sample Resubmission", value=True)

                submitted_master = st.form_submit_button("🚀 Submit Formal Resubmission Package to Ellington", type="primary", use_container_width=True)
                if submitted_master:
                    upsert_stage_status(
                        project=cycle_rec['project'],
                        stage=cycle_rec['stage'],
                        discipline=cycle_rec['discipline'],
                        status='Resubmission Received',
                        reviewer='Lead Design Consultant',
                        note=cover_summary
                    )
                    log_audit_event(
                        action=f"Consultant Resubmission Package {pkg_ver} Submitted",
                        user="Lead Design Consultant",
                        role="Consultant",
                        review_cycle=cycle_rec['cycle_id'],
                        previous_value="Issued to Consultant",
                        new_value=f"Resubmission {pkg_ver} Received",
                        details=f"Cover Letter: '{cover_summary[:120]}...'"
                    )
                    st.success(f"🎉 Resubmission Package {pkg_ver} successfully submitted to Ellington! Technical Architect has been alerted for AI Delta Review.")

        # -------------------------------------------------
        # VIEW 3: Historical Review Cycles
        # -------------------------------------------------
        elif active_page == "📜 Consultant Review History":
            st.markdown("### Historical Review Cycle Submittals")
            cycles = load_review_cycles()
            if not cycles:
                st.info("No prior review cycles found.")
            else:
                for c in cycles:
                    with st.expander(f"📁 {c['cycle_id']} — {c['stage']} ({c['issued_at']})", expanded=True):
                        st.markdown(f"**Project:** {c['project']} | **Discipline:** {c['discipline']}")
                        st.markdown(f"**Submittal Version:** {c['submittal_version']} | **Status:** {c['status']}")
                        st.markdown(f"**Total Review Comments:** {c['total_findings']}")
