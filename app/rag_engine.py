import os


# ============================================================
# KNOWLEDGE BASE
# ============================================================

KNOWLEDGE_FILE = "documents/deployment_operations_guide.txt"


def load_knowledge_base():
    """
    Load the deployment operations guide.
    """

    if not os.path.exists(KNOWLEDGE_FILE):
        return ""

    with open(
        KNOWLEDGE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


# ============================================================
# SPLIT KNOWLEDGE INTO SECTIONS
# ============================================================

def split_into_sections(text):
    """
    Split the operations guide into numbered sections.
    """

    sections = {}

    current_section = None
    current_content = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Detect section headings such as:
        # 1. DEPLOYMENT READINESS
        # 2. NETWORK READINESS

        if (
            len(line) > 3
            and line[0].isdigit()
            and "." in line[:3]
        ):

            if current_section is not None:

                sections[current_section] = "\n".join(
                    current_content
                )

            current_section = line
            current_content = []

        else:

            current_content.append(line)


    # Store final section

    if current_section is not None:

        sections[current_section] = "\n".join(
            current_content
        )


    return sections


# ============================================================
# SIMPLE RETRIEVAL
# ============================================================

def retrieve_relevant_sections(
    question,
    top_k=3
):
    """
    Retrieve the most relevant knowledge sections
    based on keyword matching.
    """

    knowledge = load_knowledge_base()

    if not knowledge:
        return []


    sections = split_into_sections(
        knowledge
    )


    question_words = set(
        question.lower().split()
    )


    scored_sections = []


    for section_name, content in sections.items():

        section_text = (
            section_name + " " + content
        ).lower()


        score = 0


        for word in question_words:

            cleaned_word = (
                word
                .strip(".,?!:;()[]{}")
            )

            if (
                len(cleaned_word) > 2
                and cleaned_word in section_text
            ):

                score += 1


        if score > 0:

            scored_sections.append(
                (
                    score,
                    section_name,
                    content
                )
            )


    # Highest relevance first

    scored_sections.sort(
        key=lambda x: x[0],
        reverse=True
    )


    # Return top relevant sections

    results = []

    for score, section_name, content in scored_sections[:top_k]:

        results.append(
            {
                "section": section_name,
                "content": content,
                "score": score
            }
        )


    return results