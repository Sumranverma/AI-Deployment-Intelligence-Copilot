import os
import sys
import pandas as pd
import streamlit as st

# ============================================================
# PATH SETUP
# ============================================================

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(APP_DIR)

if APP_DIR not in sys.path:
    sys.path.append(APP_DIR)

os.chdir(PROJECT_DIR)

# ============================================================
# IMPORTS
# ============================================================

from rag_engine import retrieve_relevant_sections
from llm_engine import generate_llm_response

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Deployment Intelligence Copilot",
    page_icon="🤖",
    layout="wide"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #f7f9fc;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .hero {
        padding: 1.8rem 2rem;
        border-radius: 16px;
        background: linear-gradient(
            135deg,
            #111827 0%,
            #1e3a8a 100%
        );
        color: white;
        margin-bottom: 1.5rem;
    }

    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }

    .hero-subtitle {
        font-size: 1rem;
        opacity: 0.88;
    }

    .metric-card {
        background: white;
        padding: 1.2rem;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .metric-title {
        font-size: 0.85rem;
        color: #6b7280;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #111827;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        margin-top: 1rem;
        margin-bottom: 0.8rem;
        color: #111827;
    }

    .copilot-box {
        background: white;
        padding: 1.5rem;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        line-height: 1.6;
    }

    .knowledge-box {
        background: #f8fafc;
        padding: 1rem 1.2rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 0.8rem;
    }

    .footer-note {
        text-align: center;
        color: #6b7280;
        font-size: 0.8rem;
        padding-top: 2rem;
        padding-bottom: 1rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def render_html(html):
    st.markdown(html, unsafe_allow_html=True)


def metric_card(title, value):
    render_html(
        f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
        </div>
        """
    )


def get_status_counts(df):
    return df["Overall_Status"].value_counts()


def generate_rule_based_response(question, df):
    """
    Fallback operational copilot.

    This is used when the OpenAI API is unavailable or has no credits.
    """

    question_lower = question.lower().strip()

    # --------------------------------------------------------
    # Specific deployment question
    # --------------------------------------------------------

    deployment_id = None

    for dep_id in df["Deployment_ID"].astype(str):
        if dep_id.lower() in question_lower:
            deployment_id = dep_id
            break

    if deployment_id:

        row = df[
            df["Deployment_ID"].astype(str) == deployment_id
        ].iloc[0]

        status = row["Overall_Status"]
        region = row["Region"]
        milestone = row["Milestone"]
        risk = row["Risk_Level"]
        network = row["Network_Readiness"]
        hardware = row["Hardware_Readiness"]
        dependency = row["Dependency_Status"]
        blocker = row["Blocker"]
        owner = row["Owner"]

        reasons = []

        if network != "Ready":
            reasons.append(
                f"network readiness is {network.lower()}"
            )

        if hardware != "Ready":
            reasons.append(
                f"hardware readiness is {hardware.lower()}"
            )

        if dependency != "Completed":
            reasons.append(
                f"dependency status is {dependency.lower()}"
            )

        if blocker != "None":
            reasons.append(
                f"there is a {blocker.lower()}"
            )

        if reasons:
            reason_text = "; ".join(reasons) + "."
        else:
            reason_text = (
                "The deployment has completed the major "
                "readiness requirements."
            )

        actions = [
            "Resolve the identified readiness gap.",
            f"Follow up with {owner} on the identified issue.",
            "Track resolution progress.",
            "Reassess deployment readiness after resolution."
        ]

        response = f"""
### Status

**{deployment_id} is currently {status}.**

### Why is this happening?

The deployment requires attention because {reason_text}

### Operational Impact

The identified readiness gap may delay deployment execution if it is not resolved or monitored.

### Key Findings

• Region: {region}  
• Milestone: {milestone}  
• Risk level: {risk}  
• Network readiness: {network}  
• Hardware readiness: {hardware}  
• Dependency status: {dependency}  
• Blocker: {blocker}  
• Owner: {owner}

### Recommended Actions

1. {actions[0]}
2. {actions[1]}
3. {actions[2]}
4. {actions[3]}
"""

        return response.strip()

    # --------------------------------------------------------
    # Blocked deployments
    # --------------------------------------------------------

    if (
        "blocked" in question_lower
        and (
            "which" in question_lower
            or "what" in question_lower
            or "deployment" in question_lower
        )
    ):

        blocked = df[
            df["Overall_Status"] == "Blocked"
        ]

        if len(blocked) == 0:
            return """
### Status

No deployments are currently blocked.

### Key Findings

All deployments have progressed beyond the blocked state.

### Recommended Actions

Continue monitoring deployment readiness and dependencies.
"""

        lines = []

        for _, row in blocked.iterrows():
            lines.append(
                f"• **{row['Deployment_ID']}** — "
                f"{row['Region']} — "
                f"Blocker: {row['Blocker']} — "
                f"Owner: {row['Owner']}"
            )

        return f"""
### Status

**{len(blocked)} deployment(s) are currently blocked.**

### Why is this happening?

These deployments have a significant blocker or dependency preventing progress.

### Operational Impact

Blocked deployments require resolution before they can progress toward final readiness.

### Key Findings

{chr(10).join(lines)}

### Recommended Actions

1. Identify the blocking dependency.
2. Confirm the responsible owner.
3. Track resolution progress.
4. Revalidate deployment readiness after resolution.
""".strip()

    # --------------------------------------------------------
    # At risk deployments
    # --------------------------------------------------------

    if (
        "at risk" in question_lower
        or "risk" in question_lower
    ):

        at_risk = df[
            df["Overall_Status"] == "At Risk"
        ]

        if len(at_risk) == 0:
            return """
### Status

No deployments are currently marked At Risk.
"""

        lines = []

        for _, row in at_risk.iterrows():
            lines.append(
                f"• **{row['Deployment_ID']}** — "
                f"{row['Region']} — "
                f"{row['Blocker']} — "
                f"Owner: {row['Owner']}"
            )

        return f"""
### Status

**{len(at_risk)} deployment(s) are currently At Risk.**

### Why is this happening?

These deployments have one or more readiness conditions requiring attention.

### Operational Impact

The identified readiness gaps may affect deployment timelines if not monitored or resolved.

### Key Findings

{chr(10).join(lines)}

### Recommended Actions

1. Identify the specific readiness gap.
2. Confirm the responsible owner.
3. Monitor the dependency.
4. Track resolution progress.
5. Reassess readiness after resolution.
""".strip()

    # --------------------------------------------------------
    # Network questions
    # --------------------------------------------------------

    if "network" in question_lower:

        network_issues = df[
            df["Network_Readiness"] != "Ready"
        ]

        lines = []

        for _, row in network_issues.iterrows():
            lines.append(
                f"• **{row['Deployment_ID']}** — "
                f"{row['Region']} — "
                f"Network: {row['Network_Readiness']} — "
                f"Blocker: {row['Blocker']}"
            )

        if not lines:
            return """
### Status

All deployments currently show Ready network readiness.

### Recommended Actions

Continue monitoring network validation and configuration dependencies.
"""

        return f"""
### Status

**{len(network_issues)} deployment(s) have network readiness concerns.**

### Why is this happening?

The affected deployments have pending or incomplete network readiness activities.

### Operational Impact

Pending network readiness should be monitored before deployment execution.

### Key Findings

{chr(10).join(lines)}

### Recommended Actions

1. Review the network readiness gap.
2. Confirm the responsible owner.
3. Complete required validation activities.
4. Reassess network readiness before deployment execution.
""".strip()

    # --------------------------------------------------------
    # Hardware questions
    # --------------------------------------------------------

    if "hardware" in question_lower:

        hardware_issues = df[
            df["Hardware_Readiness"] != "Ready"
        ]

        lines = []

        for _, row in hardware_issues.iterrows():
            lines.append(
                f"• **{row['Deployment_ID']}** — "
                f"{row['Region']} — "
                f"Hardware: {row['Hardware_Readiness']} — "
                f"Blocker: {row['Blocker']}"
            )

        return f"""
### Status

**{len(hardware_issues)} deployment(s) have hardware readiness concerns.**

### Why is this happening?

The affected deployments have pending hardware readiness or validation activities.

### Operational Impact

Pending hardware readiness can prevent a deployment from reaching its final readiness milestone.

### Key Findings

{chr(10).join(lines)}

### Recommended Actions

1. Identify the hardware readiness gap.
2. Confirm the responsible owner.
3. Track hardware validation progress.
4. Reassess deployment readiness after validation.
""".strip()
     

    # --------------------------------------------------------
    # Regional questions
    # --------------------------------------------------------

    if "region" in question_lower:

        regional = (
            df.groupby("Region")
            .agg(
                Deployments=("Deployment_ID", "count"),
                At_Risk=(
                    "Overall_Status",
                    lambda x: (x == "At Risk").sum()
                ),
                Blocked=(
                    "Overall_Status",
                    lambda x: (x == "Blocked").sum()
                )
            )
            .reset_index()
        )

        lines = []

        for _, row in regional.iterrows():
            lines.append(
                f"• **{row['Region']}** — "
                f"{row['Deployments']} deployment(s), "
                f"{row['At_Risk']} At Risk, "
                f"{row['Blocked']} Blocked"
            )

        return f"""
### Status

Regional deployment readiness varies across the current portfolio.

### Key Findings

{chr(10).join(lines)}

### Recommended Actions

1. Review regions with At Risk or Blocked deployments.
2. Identify recurring readiness gaps.
3. Follow up with responsible deployment owners.
4. Reassess readiness after dependencies are resolved.
""".strip()

    # --------------------------------------------------------
    # General question
    # --------------------------------------------------------

    return f"""
### Status

The deployment portfolio contains **{len(df)} deployments**.

### Why is this happening?

The current portfolio includes Ready, At Risk, and Blocked deployments with different readiness conditions.

### Operational Impact

Readiness gaps involving network, hardware, or dependencies may affect deployment progress.

### Key Findings

• Ready: {(df["Overall_Status"] == "Ready").sum()}  
• At Risk: {(df["Overall_Status"] == "At Risk").sum()}  
• Blocked: {(df["Overall_Status"] == "Blocked").sum()}  
• High Risk: {(df["Risk_Level"] == "High").sum()}  
• Network Issues: {(df["Network_Readiness"] != "Ready").sum()}  
• Hardware Issues: {(df["Hardware_Readiness"] != "Ready").sum()}

### Recommended Actions

1. Review At Risk deployments.
2. Investigate Blocked deployments.
3. Monitor network and hardware readiness.
4. Track dependency resolution.
5. Reassess deployment readiness after issue resolution.
""".strip()


# ============================================================
# LOAD DATA
# ============================================================

DATA_FILE = os.path.join(
    PROJECT_DIR,
    "data",
    "deployment_data.csv"
)

if not os.path.exists(DATA_FILE):

    st.error(
        "deployment_data.csv was not found in the data folder."
    )

    st.stop()

df = pd.read_csv(DATA_FILE)

# ============================================================
# VALIDATE DATA
# ============================================================

required_columns = [
    "Deployment_ID",
    "Region",
    "Environment",
    "Milestone",
    "Deployment_Date",
    "Overall_Status",
    "Network_Readiness",
    "Hardware_Readiness",
    "Dependency_Status",
    "Risk_Level",
    "Blocker",
    "Owner"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    st.error(
        f"Missing columns in deployment_data.csv: "
        f"{', '.join(missing_columns)}"
    )

    st.stop()

# ============================================================
# DATA PREPARATION
# ============================================================

df["Deployment_Date"] = pd.to_datetime(
    df["Deployment_Date"],
    errors="coerce"
)

total_deployments = len(df)

ready_count = (
    df["Overall_Status"] == "Ready"
).sum()

at_risk_count = (
    df["Overall_Status"] == "At Risk"
).sum()

blocked_count = (
    df["Overall_Status"] == "Blocked"
).sum()

readiness_percentage = (
    ready_count / total_deployments * 100
    if total_deployments > 0
    else 0
)

high_risk_count = (
    df["Risk_Level"] == "High"
).sum()

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🤖 Deployment Copilot")

st.sidebar.markdown(
    """
    **AI-Powered Deployment Intelligence**

    Monitor deployment readiness, identify risks,
    analyze blockers, and ask operational questions.
    """
)

page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Deployment Analysis",
        "AI Copilot"
    ]
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "Synthetic deployment data • Portfolio prototype"
)

# ============================================================
# HEADER
# ============================================================

render_html(
    """
    <div class="hero">
        <div class="hero-title">
            AI-Powered Deployment Intelligence & Operations Copilot
        </div>
        <div class="hero-subtitle">
            Deployment readiness monitoring, operational intelligence,
            RAG-assisted knowledge retrieval, and AI decision support.
        </div>
    </div>
    """
)

# ============================================================
# OVERVIEW
# ============================================================

if page == "Overview":

    st.markdown(
        '<div class="section-title">Executive Overview</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card(
            "Total Deployments",
            total_deployments
        )

    with col2:
        metric_card(
            "Ready",
            ready_count
        )

    with col3:
        metric_card(
            "At Risk",
            at_risk_count
        )

    with col4:
        metric_card(
            "Blocked",
            blocked_count
        )

    st.markdown("")

    col1, col2, col3 = st.columns(3)

    with col1:
        metric_card(
            "Readiness",
            f"{readiness_percentage:.0f}%"
        )

    with col2:
        metric_card(
            "High Risk",
            high_risk_count
        )

    with col3:
        metric_card(
            "Network Issues",
            (df["Network_Readiness"] != "Ready").sum()
        )

    st.markdown(
        '<div class="section-title">Deployment Status</div>',
        unsafe_allow_html=True
    )

    status_counts = (
        df["Overall_Status"]
        .value_counts()
        .reindex(
            ["Ready", "At Risk", "Blocked"],
            fill_value=0
        )
    )

    st.bar_chart(status_counts)

    st.markdown(
        '<div class="section-title">Risk Distribution</div>',
        unsafe_allow_html=True
    )

    risk_counts = (
        df["Risk_Level"]
        .value_counts()
        .reindex(
            ["Low", "Medium", "High"],
            fill_value=0
        )
    )

    st.bar_chart(risk_counts)

    st.markdown(
        '<div class="section-title">Deployment Portfolio</div>',
        unsafe_allow_html=True
    )

    display_columns = [
        "Deployment_ID",
        "Region",
        "Milestone",
        "Overall_Status",
        "Risk_Level",
        "Network_Readiness",
        "Hardware_Readiness",
        "Dependency_Status",
        "Owner"
    ]

    st.dataframe(
        df[display_columns],
        width="stretch",
        hide_index=True
    )

# ============================================================
# DEPLOYMENT ANALYSIS
# ============================================================

elif page == "Deployment Analysis":

    st.markdown(
        '<div class="section-title">Deployment Analysis</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Filter deployments to identify readiness gaps, risks, "
        "and operational blockers."
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        status_filter = st.multiselect(
            "Overall Status",
            options=sorted(
                df["Overall_Status"].unique()
            ),
            default=sorted(
                df["Overall_Status"].unique()
            )
        )

    with col2:

        risk_filter = st.multiselect(
            "Risk Level",
            options=sorted(
                df["Risk_Level"].unique()
            ),
            default=sorted(
                df["Risk_Level"].unique()
            )
        )

    with col3:

        region_filter = st.multiselect(
            "Region",
            options=sorted(
                df["Region"].unique()
            ),
            default=sorted(
                df["Region"].unique()
            )
        )

    filtered_df = df[
        df["Overall_Status"].isin(status_filter)
        &
        df["Risk_Level"].isin(risk_filter)
        &
        df["Region"].isin(region_filter)
    ]

    st.markdown("")

    col1, col2, col3 = st.columns(3)

    with col1:
        metric_card(
            "Filtered Deployments",
            len(filtered_df)
        )

    with col2:
        metric_card(
            "Filtered At Risk",
            (
                filtered_df["Overall_Status"]
                == "At Risk"
            ).sum()
        )

    with col3:
        metric_card(
            "Filtered Blocked",
            (
                filtered_df["Overall_Status"]
                == "Blocked"
            ).sum()
        )

    st.markdown(
        '<div class="section-title">Filtered Deployments</div>',
        unsafe_allow_html=True
    )

    st.dataframe(
        filtered_df[
            required_columns
        ],
        width="stretch",
        hide_index=True
    )

    st.markdown(
        '<div class="section-title">Readiness Analysis</div>',
        unsafe_allow_html=True
    )

    readiness_data = pd.DataFrame(
        {
            "Readiness Area": [
                "Network Ready",
                "Hardware Ready",
                "Dependencies Completed"
            ],
            "Count": [
                (
                    filtered_df["Network_Readiness"]
                    == "Ready"
                ).sum(),
                (
                    filtered_df["Hardware_Readiness"]
                    == "Ready"
                ).sum(),
                (
                    filtered_df["Dependency_Status"]
                    == "Completed"
                ).sum()
            ]
        }
    )

    st.bar_chart(
        readiness_data.set_index(
            "Readiness Area"
        )
    )

    st.markdown(
        '<div class="section-title">Blockers</div>',
        unsafe_allow_html=True
    )

    blockers = (
        filtered_df[
            filtered_df["Blocker"] != "None"
        ][
            [
                "Deployment_ID",
                "Region",
                "Blocker",
                "Risk_Level",
                "Owner"
            ]
        ]
    )

    if blockers.empty:

        st.success(
            "No active blockers in the current filter."
        )

    else:

        st.dataframe(
            blockers,
            width="stretch",
            hide_index=True
        )

# ============================================================
# AI COPILOT
# ============================================================

elif page == "AI Copilot":

    st.subheader("🤖 AI Deployment Operations Copilot")

    st.write(
        "Ask questions about deployment readiness, risks, "
        "blockers, dependencies, network readiness, or hardware readiness."
    )

    question = st.text_area(
        "Ask the Copilot",
        placeholder=(
            "Example: Why is DEP-005 at risk?\n"
            "Which deployments are currently blocked?\n"
            "Which deployments have network readiness issues?"
        ),
        height=120
    )

    ask_button = st.button(
        "🚀 Analyze Deployment",
        type="primary"
    )

    if ask_button and question.strip():

        # ----------------------------------------------------
        # RAG RETRIEVAL
        # ----------------------------------------------------

        retrieved_sections = retrieve_relevant_sections(
            question,
            top_k=2
        )

        # ----------------------------------------------------
        # BUILD CONTEXT
        # ----------------------------------------------------

        context_parts = []

        context_parts.append(
            "DEPLOYMENT DATA:\n"
            + df.to_string(index=False)
        )

        if retrieved_sections:

            context_parts.append(
                "\nOPERATIONAL KNOWLEDGE:\n"
            )

            for item in retrieved_sections:

                context_parts.append(
                    f"{item['section']}\n"
                    f"{item['content']}"
                )

        context = "\n\n".join(
            context_parts
        )

        # ----------------------------------------------------
        # TRY LLM
        # ----------------------------------------------------

        response = generate_llm_response(
            question,
            context
        )

        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------

        if not response:

            response = generate_rule_based_response(
                question,
                df
            )

        # ----------------------------------------------------
        # PROTECT UI FROM OLD KNOWLEDGE BLOCK
        # ----------------------------------------------------

        if "**Knowledge Used**" in response:

            response = response.split(
                "**Knowledge Used**"
            )[0].rstrip()

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        st.subheader("🤖 Copilot Response")

        st.markdown(
            response
        )

        # ----------------------------------------------------
        # OPERATIONAL KNOWLEDGE
        # ----------------------------------------------------

        if retrieved_sections:

            st.markdown("📚 Operational Knowledge")

            for item in retrieved_sections:

                st.markdown(
                    f"### {item['section']}"
                )

                st.write(
                    item["content"]
                )

                st.divider()

        else:

            st.info(
                "No directly matching operational knowledge "
                "section was retrieved."
            )

    elif ask_button:

            st.warning(
                "Please enter a deployment question first."
            )

# ============================================================
# FOOTER
# ============================================================

render_html(
    """
    <div class="footer-note">
        Portfolio prototype • Synthetic deployment data •
        AI-assisted operational intelligence
    </div>
    """
)