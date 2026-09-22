import pandas as pd
import re


def generate_copilot_response(question, deployment_df, retrieved_sections):
    """
    Generate a structured operational response using
    deployment data and retrieved operational knowledge.
    """

    question_lower = question.lower()

    # ==================================================
    # DETECT SPECIFIC DEPLOYMENT ID
    # ==================================================

    deployment_match = re.search(
        r"\bDEP-\d{3}\b",
        question.upper()
    )

    deployment_id = (
        deployment_match.group(0)
        if deployment_match
        else None
    )

    situation = ""
    reason = ""
    impact = ""
    key_findings = []
    recommendations = []

    # ==================================================
    # SPECIFIC DEPLOYMENT ANALYSIS
    # ==================================================

    if deployment_id:

        deployment = deployment_df[
            deployment_df["Deployment_ID"] == deployment_id
        ]

        if not deployment.empty:

            row = deployment.iloc[0]

            # ------------------------------------------
            # STATUS
            # ------------------------------------------

            situation = (
                f"{deployment_id} is currently "
                f"{row['Overall_Status']}."
            )

            # ------------------------------------------
            # DETERMINE WHY
            # ------------------------------------------

            reasons = []

            if row["Network_Readiness"] != "Ready":
                reasons.append(
                    f"network readiness is "
                    f"{row['Network_Readiness'].lower()}"
                )

            if row["Hardware_Readiness"] != "Ready":
                reasons.append(
                    f"hardware readiness is "
                    f"{row['Hardware_Readiness'].lower()}"
                )

            if row["Dependency_Status"] != "Completed":
                reasons.append(
                    f"dependency status is "
                    f"{row['Dependency_Status'].lower()}"
                )

            if row["Blocker"] != "None":
                reasons.append(
                    f"there is a "
                    f"{row['Blocker'].lower()}"
                )

            if reasons:
                reason = (
                    "The deployment requires attention because "
                    + "; ".join(reasons)
                    + "."
                )
            else:
                reason = (
                    "The major deployment readiness requirements "
                    "are currently satisfied."
                )

            # ------------------------------------------
            # OPERATIONAL IMPACT
            # ------------------------------------------

            if row["Overall_Status"] == "Blocked":

                impact = (
                    "The current blocker is preventing the deployment "
                    "from progressing and may delay deployment execution."
                )

            elif row["Overall_Status"] == "At Risk":

                impact = (
                    "The identified readiness gap may delay deployment "
                    "execution if it is not resolved or monitored."
                )

            else:

                impact = (
                    "No major deployment blocker is currently identified. "
                    "Readiness can continue to be monitored."
                )

            # ------------------------------------------
            # KEY DEPLOYMENT DETAILS
            # ------------------------------------------

            key_findings = [
                f"Region: {row['Region']}",
                f"Milestone: {row['Milestone']}",
                f"Risk level: {row['Risk_Level']}",
                f"Network readiness: {row['Network_Readiness']}",
                f"Hardware readiness: {row['Hardware_Readiness']}",
                f"Dependency status: {row['Dependency_Status']}",
                f"Blocker: {row['Blocker']}",
                f"Owner: {row['Owner']}"
            ]

            # ------------------------------------------
            # RECOMMENDATIONS
            # ------------------------------------------

            if row["Overall_Status"] == "Blocked":

                recommendations = [
                    "Identify and resolve the blocking dependency.",
                    f"Coordinate with {row['Owner']} on resolution.",
                    "Track the resolution progress.",
                    "Revalidate deployment readiness after resolution."
                ]

            elif row["Overall_Status"] == "At Risk":

                recommendations = [
                    "Resolve the identified readiness gap.",
                    f"Follow up with {row['Owner']} on the identified issue.",
                    "Track resolution progress.",
                    "Reassess deployment readiness after resolution."
                ]

            else:

                recommendations = [
                    "Continue monitoring deployment readiness.",
                    "Validate that completed dependencies remain on track."
                ]

        else:

            situation = (
                f"I could not find deployment {deployment_id} "
                "in the available deployment data."
            )

            reason = (
                "The deployment ID is not present in the current "
                "deployment dataset."
            )

            impact = (
                "A reliable operational assessment cannot be made "
                "without the deployment information."
            )

            recommendations = [
                "Check the deployment ID and try again."
            ]

    # ==================================================
    # AT-RISK DEPLOYMENTS
    # ==================================================

    elif (
        "at risk" in question_lower
        or "risk" in question_lower
    ):

        risk_df = deployment_df[
            deployment_df["Overall_Status"] == "At Risk"
        ]

        situation = (
            f"{len(risk_df)} deployments are currently "
            f"identified as At Risk."
        )

        reason = (
            "These deployments have one or more readiness conditions "
            "that require attention before they can be considered "
            "fully ready."
        )

        impact = (
            "Unresolved readiness issues may affect deployment "
            "timelines or execution readiness."
        )

        if len(risk_df) > 0:

            regions = (
                risk_df["Region"]
                .drop_duplicates()
                .tolist()
            )

            key_findings.append(
                "Regions requiring attention: "
                + ", ".join(regions)
            )

            blockers = (
                risk_df["Blocker"]
                .dropna()
                .loc[lambda x: x != "None"]
                .drop_duplicates()
                .tolist()
            )

            if blockers:

                key_findings.append(
                    "Identified issues: "
                    + ", ".join(blockers)
                )

        recommendations = [
            "Identify the specific readiness gap for each deployment.",
            "Confirm the responsible owner.",
            "Track the dependency or issue through resolution.",
            "Reassess deployment readiness after resolution."
        ]

    # ==================================================
    # BLOCKED DEPLOYMENTS
    # ==================================================

    elif (
        "blocked" in question_lower
        or "blocker" in question_lower
    ):

        blocked_df = deployment_df[
            deployment_df["Overall_Status"] == "Blocked"
        ]

        situation = (
            f"{len(blocked_df)} deployments are currently blocked."
        )

        reason = (
            "These deployments have significant blockers or "
            "dependencies preventing deployment progress."
        )

        impact = (
            "Blocked deployments may not progress to the next "
            "deployment milestone until the blocking issue is resolved."
        )

        if len(blocked_df) > 0:

            blockers = (
                blocked_df["Blocker"]
                .dropna()
                .drop_duplicates()
                .tolist()
            )

            key_findings.append(
                "Main blockers: "
                + ", ".join(blockers)
            )

            owners = (
                blocked_df["Owner"]
                .dropna()
                .drop_duplicates()
                .tolist()
            )

            key_findings.append(
                "Responsible teams: "
                + ", ".join(owners)
            )

        recommendations = [
            "Identify the blocking dependency.",
            "Confirm the responsible owner.",
            "Track resolution progress.",
            "Revalidate deployment readiness after resolution."
        ]

    # ==================================================
    # NETWORK READINESS
    # ==================================================

    elif "network" in question_lower:

        network_df = deployment_df[
            deployment_df["Network_Readiness"] != "Ready"
        ]

        situation = (
            f"{len(network_df)} deployments currently have "
            f"network readiness concerns."
        )

        reason = (
            "The affected deployments have network readiness "
            "requirements that are still pending or incomplete."
        )

        impact = (
            "Pending network readiness can prevent or delay "
            "deployment execution."
        )

        if len(network_df) > 0:

            issues = (
                network_df["Blocker"]
                .dropna()
                .loc[lambda x: x != "None"]
                .drop_duplicates()
                .tolist()
            )

            key_findings.append(
                "Network-related issues: "
                + ", ".join(issues)
            )

        recommendations = [
            "Review pending network validation activities.",
            "Check network dependencies and configuration requirements.",
            "Monitor affected deployments before execution."
        ]

    # ==================================================
    # HARDWARE READINESS
    # ==================================================

    elif "hardware" in question_lower:

        hardware_df = deployment_df[
            deployment_df["Hardware_Readiness"] != "Ready"
        ]

        situation = (
            f"{len(hardware_df)} deployments currently have "
            f"hardware readiness concerns."
        )

        reason = (
            "The affected deployments have hardware requirements "
            "that are still pending or incomplete."
        )

        impact = (
            "Pending hardware readiness can prevent a deployment "
            "from reaching its final readiness milestone."
        )

        if len(hardware_df) > 0:

            issues = (
                hardware_df["Blocker"]
                .dropna()
                .loc[lambda x: x != "None"]
                .drop_duplicates()
                .tolist()
            )

            key_findings.append(
                "Hardware-related issues: "
                + ", ".join(issues)
            )

        recommendations = [
            "Confirm hardware availability.",
            "Validate hardware readiness requirements.",
            "Track hardware dependencies until completion."
        ]

    # ==================================================
    # DEPENDENCY ANALYSIS
    # ==================================================

    elif "dependenc" in question_lower:

        dependency_df = deployment_df[
            deployment_df["Dependency_Status"] != "Completed"
        ]

        situation = (
            f"{len(dependency_df)} deployments have "
            f"dependencies requiring attention."
        )

        reason = (
            "These deployments contain dependencies that are "
            "still in progress or blocked."
        )

        impact = (
            "Unresolved dependencies can delay deployment "
            "readiness and execution."
        )

        if len(dependency_df) > 0:

            dependency_statuses = (
                dependency_df["Dependency_Status"]
                .dropna()
                .drop_duplicates()
                .tolist()
            )

            key_findings.append(
                "Dependency states requiring attention: "
                + ", ".join(dependency_statuses)
            )

            blockers = (
                dependency_df["Blocker"]
                .dropna()
                .loc[lambda x: x != "None"]
                .drop_duplicates()
                .tolist()
            )

            if blockers:

                key_findings.append(
                    "Related issues: "
                    + ", ".join(blockers)
                )

        recommendations = [
            "Identify the responsible owner for each dependency.",
            "Track dependencies that are still in progress.",
            "Escalate blocked critical dependencies when required.",
            "Revalidate readiness after dependency completion."
        ]

    # ==================================================
    # PRE-DEPLOYMENT READINESS
    # ==================================================

    elif (
        "before deployment" in question_lower
        or "check before" in question_lower
        or "readiness" in question_lower
    ):

        situation = (
            "The deployment should be reviewed against the "
            "major readiness requirements before execution."
        )

        reason = (
            "Deployment readiness depends on infrastructure, "
            "network, hardware, dependencies, and milestone completion."
        )

        impact = (
            "Missing or incomplete readiness requirements can "
            "increase deployment risk or delay execution."
        )

        key_findings = [
            "Infrastructure readiness",
            "Network readiness",
            "Hardware readiness",
            "Dependency completion",
            "Deployment milestone completion"
        ]

        recommendations = [
            "Verify all critical readiness requirements.",
            "Resolve or track pending dependencies.",
            "Confirm responsible owners.",
            "Reassess readiness before deployment execution."
        ]

    # ==================================================
    # GENERAL QUESTION
    # ==================================================

    else:

        situation = (
            "I reviewed the available deployment information "
            "and operational knowledge."
        )

        reason = (
            "The available deployment dataset and operational "
            "knowledge were used to identify relevant information."
        )

        impact = (
            "The response should be validated against the underlying "
            "deployment information before operational decisions are made."
        )

        recommendations = [
            "Review deployment readiness requirements.",
            "Check active dependencies and blockers.",
            "Validate the response against the underlying deployment data."
        ]

    # ==================================================
    # BUILD STRUCTURED RESPONSE
    # ==================================================

    response = (
        f"**Status**\n"
        f"{situation}"
    )

    # ------------------------------------------
    # WHY
    # ------------------------------------------

    if reason:

        response += (
            "\n\n**Why is this happening?**\n"
            f"{reason}"
        )

    # ------------------------------------------
    # OPERATIONAL IMPACT
    # ------------------------------------------

    if impact:

        response += (
            "\n\n**Operational Impact**\n"
            f"{impact}"
        )

    # ------------------------------------------
    # KEY FINDINGS
    # ------------------------------------------

    if key_findings:

        response += "\n\n**Key Findings**"

        for finding in key_findings:

            response += (
                f"\n• {finding}"
            )

    # ------------------------------------------
    # RECOMMENDED ACTIONS
    # ------------------------------------------

    if recommendations:

        response += "\n\n**Recommended Actions**"

        for index, recommendation in enumerate(
            recommendations,
            start=1
        ):

            response += (
                f"\n{index}. {recommendation}"
            )

    return response