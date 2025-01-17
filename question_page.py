import streamlit as st
from labeling_page import create_dataframe_from_json

@st.fragment
def display_question_page():


    # Initialize session state variables
    if "questions" not in st.session_state:
        st.session_state.questions = []
    if "selected_question_type" not in st.session_state:
        st.session_state.selected_question_type = "Label"  # Default to Label

    # Initialize form-related session state variables
    if "form_data_title" not in st.session_state:
        st.session_state.form_data_title = ""
    if "form_data_description" not in st.session_state:
        st.session_state.form_data_description = ""
    if "form_data_labels" not in st.session_state:
        st.session_state.form_data_labels = ""
    if "labels_input_key" not in st.session_state:
        st.session_state.labels_input_key = "labels_input_0"
    
    # Get the JSON data and selected columns from session state
    json_data = st.session_state.get("json_data")  # Make sure to store the original JSON data
    selected_columns = st.session_state.get("selected_columns", [])
    # Create DataFrame if not already created
    if "dataset" not in st.session_state and json_data and selected_columns:
        st.session_state.dataset = create_dataframe_from_json(json_data, selected_columns)

    st.markdown("### Dataset Preview:")
    st.write(st.session_state.dataset.head(5))
    st.markdown("### Add Questions and Related Information")

    # Dropdown for selecting question type (outside the form)
    st.markdown("**Select question type:**")
    selected_question_type = st.selectbox(
        "Choose the type of question",
        ["Label", "Multi-label", "Rating","TextQuestion","SpanQuestion","Ranking"],
        index=["Label", "Multi-label", "Rating","TextQuestion","SpanQuestion","Ranking"].index(st.session_state.selected_question_type)
    )

    # Update session state when the user changes the question type
    st.session_state.selected_question_type = selected_question_type

    # Input fields for adding a question within a form
    question_title = st.text_input(
        "Describe Question Title (e.g., overall Quality):",
        value=st.session_state.form_data_title,
        key="question_title"
    )
    label_description = st.text_input(
        "Describe Question information (optional):",
        value=st.session_state.form_data_description,
        key="label_description"
    )

    # Initialize span_field in session state if not exists
    if "span_field" not in st.session_state:
        st.session_state.span_field = {}

    # Conditionally show labels input and field selection for span questions
    labels = []
    selected_field = None
    if st.session_state.selected_question_type in ["Label", "Multi-label", "SpanQuestion","Ranking"]:
        st.markdown(f"**Define possible {st.session_state.selected_question_type.lower()} options (comma-separated):**")
        labels_input_key = st.session_state.labels_input_key
        labels_input = st.text_input(
            "Example: Good, Average, Bad",
            value=st.session_state.form_data_labels,
            key=labels_input_key
        )
        labels = [label.strip() for label in labels_input.split(",") if label.strip()]

        # Add field selection for span questions
        if st.session_state.selected_question_type == "SpanQuestion":
            st.markdown("**Select field for span annotation:**")
            field_options = [col["text"] for col in st.session_state.get("selected_columns", [])]
            if field_options:
                selected_field = st.selectbox(
                    "Choose field to annotate",
                    options=field_options,
                    key=f"span_field_{question_title}"
                )
            else:
                st.warning("No fields available for span annotation. Please select fields in the upload page first.")
    
    submit_button = st.button("Add Question")

    # Handle form submission
    if submit_button:
        if not question_title.strip():
            st.warning("Please provide a question title.")
        elif st.session_state.selected_question_type in ["Label", "Multi-label", "SpanQuestion", "Ranking"] and not labels:
            st.warning("Please define at least one label.")
        elif st.session_state.selected_question_type == "SpanQuestion" and not selected_field:
            st.warning("Please select a field for span annotation.")
        else:
            # Add question details to session state
            question_data = {
                'question_title': question_title,
                "label_description": label_description,
                "question_type": st.session_state.selected_question_type,
                "labels": labels if st.session_state.selected_question_type in ["Label", "Multi-label", "SpanQuestion", "Ranking"] else None,
            }
            
            # Add selected field for span questions
            if st.session_state.selected_question_type == "SpanQuestion":
                question_data["span_field"] = selected_field
                # Store in session state for later use
                st.session_state.span_field[question_title] = selected_field

            st.session_state.questions.append(question_data)
            st.success("Question added successfully!")
            
            # Clear form fields
            st.session_state.form_data_title = ""
            st.session_state.form_data_description = ""
            st.session_state.form_data_labels = ""
            st.rerun()

    # If validation fails, retain the data in the form
    else:
        # Store the current form inputs in session state if user hasn't clicked submit
        st.session_state.form_data_title = question_title
        st.session_state.form_data_description = label_description
        st.session_state.form_data_labels = ", ".join(labels)

    # Display the list of added questions
    if st.session_state.questions:
        st.markdown("### Added Questions")
        for idx, question in enumerate(st.session_state.questions, start=1):
            st.markdown(f"**{idx}. Question title:** {question['question_title']}")
            st.markdown(f"**Question Description:** {question['label_description']}")
            st.markdown(f"**Question Type:** {question['question_type']}")
            if question['question_type'] in ["Label", "Multi-label", "SpanQuestion"]:
                st.markdown(f"**Labels:** {', '.join(question['labels'])}")
                if question['question_type'] == "SpanQuestion":
                    st.markdown(f"**Field for Span Annotation:** {question.get('span_field')}")
            st.markdown("---")

    # Show "Next" button to navigate to the labeling page (third page)
    if st.button("Next"):
        if st.session_state.questions:
            st.session_state.page = 3  # Move to the labeling page
            st.rerun()  # Re-run the app to update page state
        else:
            st.warning("Please add at least one question before proceeding.")
