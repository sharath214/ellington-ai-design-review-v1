# Ellington Properties — AI Design Review Management System (V1 Architecture)

An enterprise-grade, human-governed AI Design Review platform engineered for **Ellington Properties Development LLC**.

This repository represents the **V1 Architecture**, introducing strict role-based access control, dual-stream review workflows, point-in-time AI advisory validation, locked review cycles, and an isolated consultant collaboration portal.

---

## 🏛️ Business Overview & Core Principles

1. **Human-in-the-Loop Governance:** The Technical Architect (TA) is the sole authorizing authority. AI acts strictly as an advisory assistant and never overrides, auto-modifies, or closes findings.
2. **Dual-Stream Review:**
   - **Stream A (AI First-Pass):** Automated scanning against DCR, Authority Building Codes (DBC/DCD/DEWA/Al Safaat), Brand Standards, and Cross-Discipline Coordination.
   - **Stream B (Technical Architect Gaps & Judgments):** Independent human authoring of qualitative, aesthetic, and spatial findings (including *"Design Judgment / Technical Architect Observation"* without mandatory regulatory clauses).
3. **Point-in-Time AI Advisory on Human Findings:** Technical Architects can request on-demand AI review to detect potential duplicates, correlate standard clauses, check for drawing contradictions, and refine consultant-facing wording without live typing intrusion.
4. **Point-in-Time Review Cycle Locking:** Once the package is finalized and issued to the consultant, **Review Cycle 1 is frozen and locked**. No live commenting after issuance. Any future comments belong to a subsequent review cycle or formal amendment.
5. **Isolated Consultant Portal:** Lead Design Consultants only see officially issued, locked comments and consultant-visible attachments. Consultants can accept, request clarification, contest findings, request exceptions, and upload revised submittal packages (V2.0+).
6. **AI Delta Review:** Compares revised submittals against issued comments and consultant responses. The Technical Architect validates every delta result.
7. **Transparent Configurable Scoring:** Configurable severity deductions and pass thresholds. Only confirmed and finalized findings affect the score; rejected false positives do not.

---

## 👥 Role Permissions Matrix

| Capability / Action | Technical Architect (Internal) | Lead Design Consultant (External) |
|---|---|---|
| View Portfolio Dashboard | ✅ Full Access | ❌ Restricted |
| Run AI First-Pass Review | ✅ Yes | ❌ No |
| Confirm / Reject AI Findings | ✅ Yes (Filters False Positives) | ❌ No |
| Author Manual Findings & Upload Sketches | ✅ Yes (Stream B) | ❌ No |
| Request AI Advisory Review on Findings | ✅ Yes | ❌ No |
| View Internal Notes & Rejected AI Items | ✅ Yes | ❌ Strictly Hidden |
| Finalize & Lock Review Cycle | ✅ Yes | ❌ No |
| View Issued Comments Register | ✅ Yes | ✅ Yes (Locked Items Only) |
| Submit Item Responses & Contestations | ❌ N/A | ✅ Yes (Accept/Contest/Clarify) |
| Upload Revised Submittal Package (V2.0) | ❌ N/A | ✅ Yes |
| Run AI Delta Review | ✅ Yes | ❌ No |
| Close Finding / Sign-Off Stage | ✅ Yes | ❌ No |
| Complete with Outstanding Items | ✅ Yes (with formal deferral) | ❌ No |

---

## ⚙️ Quick Start & Local Run

### Prerequisites
- Python 3.10+
- Virtual environment with requirements installed:
```bash
pip install -r requirements.txt
```

### Running Locally
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`. Use the sidebar **"Active Application Role"** dropdown to seamlessly switch between the **Technical Architect** studio and the **Lead Design Consultant** portal.

---

## 🌐 Deploy to Streamlit Community Cloud (New V1 App)

To deploy this V1 application to its own unique live public link:
1. Go to **[share.streamlit.io](https://share.streamlit.io)** and log in with GitHub.
2. Click **Create app** > **"Yup, I have an app"**.
3. Configure:
   - **Repository:** `sharath214/ellington-ai-design-review-v1`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **Custom App Subdomain:** e.g. `ellington-design-review-v1`
4. Click **Deploy!**
