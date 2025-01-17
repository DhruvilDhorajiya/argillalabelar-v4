import streamlit as st
import pandas as pd
import argilla as rg
import json
from labeling_page import format_value

def convert_to_string(value):
    """Convert any value to a string representation suitable for Argilla"""
    if isinstance(value, (dict, list)):
        return format_value(value)  # Use your existing formatter
    return str(value) if value is not None else ""

def get_value_from_path(data: dict, path: str):
    """Extract value from nested JSON using a simple dot-notation path."""
    try:
        current = data
        for part in path.split('.'):
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and current:
                # If it's a list, assume we want the first item in that list
                current = current[0].get(part)
            else:
                return None
        return current
    except (KeyError, IndexError, AttributeError):
        return None

def sanitize_name(name: str) -> str:
    """Convert a string to a valid Argilla field name."""
    # Replace spaces and special characters with underscores
    sanitized = name.lower().replace(' ', '_')
    # Remove any non-alphanumeric characters (except underscores)
    sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '_')
    return sanitized

def display_upload_to_argilla_page():
    st.title("Upload to Argilla")
    
    # Load data from session state
    dataset = st.session_state.get("dataset", pd.DataFrame())
    selected_columns = st.session_state.get("selected_columns", [])
    metadata_columns = st.session_state.get("metadata_columns", [])
    questions = st.session_state.get("questions", [])
    json_data = st.session_state.get("json_data", {}).get("data", [])

    if dataset.empty or not questions:
        st.warning("No labeled dataset or questions found. Please ensure labeling is completed before uploading.")
        return

    # Validate columns
    recognized_cols = set(dataset.columns)
    field_cols = [col_def["text"] for col_def in selected_columns if col_def["text"] in recognized_cols]
    
    missing_field_cols = [col_def["text"] for col_def in selected_columns if col_def["text"] not in recognized_cols]
    if missing_field_cols:
        st.warning(f"Some columns are not found in the dataset: {missing_field_cols}")

    if not field_cols and not metadata_columns:
        st.warning("No valid columns found. Please select at least one field or metadata column before uploading.")
    
    st.write("Labeled Dataset Preview:")
    st.write(dataset.head())

    guidelines = st.text_area("Write labeling guidelines:", value="")
    
    # Server selection
    server_type = st.radio(
        "Select Argilla Server",
        ["HuggingFace Space", "Custom Server"]
    )

    if server_type == "HuggingFace Space":
        api_url = st.text_input("Argilla Server URL", value="https://dhruvil2004-my-argilla.hf.space/")
        api_key = st.text_input("API Key", value="0FzoksnKXf-4xYR6s6_nFYHyMbJ8s-rqGfj1IjRBPw5IkmhDa1KBzQ6cAb74-qd5BsBI6QKQ1lq749axTmet3_f2RSb-xoddBD2NgH5ld0g", type="password")
        workspace_name = st.text_input("Workspace Name", value="argilla")
    else:
        api_url = st.text_input("Argilla Server URL", value="http://34.131.42.99:6900")
        api_key = st.text_input("API Key", value="argilla.apikey", type="password")
        workspace_name = st.text_input("Workspace Name", value="argilla")

    dataset_name = st.text_input("Dataset Name", value="labeled_dataset")

    if st.button("Upload to Argilla"):
        try:
            # Initialize Argilla client
            client = rg.client.Argilla(api_url=api_url, api_key=api_key)

            # Create metadata properties
            metadata_values = {}
            for meta_def in metadata_columns:
                unique_values = set()
                for record in json_data:
                    path = meta_def["path"].replace("data.", "")
                    value = get_value_from_path(record, path)
                    if value is not None:
                        unique_values.add(str(value))
                metadata_values[meta_def["text"]] = sorted(list(unique_values))

            metadata_properties = [
                rg.TermsMetadataProperty(
                    name=meta_def["text"],
                    title=meta_def["text"],
                    options=metadata_values[meta_def["text"]]
                )
                for meta_def in metadata_columns
            ]
            # Create fields for all selected columns with sanitized names
            fields = [
                rg.TextField(
                    name=sanitize_name(col),  # Sanitize field names
                    title=col,
                    use_markdown=False
                )
                for col in field_cols
            ]

            # Build questions
            label_questions = []
            for question in questions:
                question_name = sanitize_name(question["question_title"])
                
                if question["question_type"] == "Label":
                    label_questions.append(
                        rg.LabelQuestion(
                            name=question_name,  # Use sanitized name
                            title=question["question_title"],  # Keep original title for display
                            labels=question["labels"],
                            description=question["label_description"]
                        )
                    )
                elif question["question_type"] == "Multi-label":
                    label_questions.append(
                        rg.MultiLabelQuestion(
                            name=question_name,  # Use sanitized name
                            title=question["question_title"],  # Keep original title for display
                            labels=question["labels"],
                            description=question["label_description"]
                        )
                    )
                elif question["question_type"] == "Rating":
                    label_questions.append(
                        rg.RatingQuestion(
                            name=question_name,  # Use sanitized name
                            title=question["question_title"],  # Keep original title for display
                            values=[1, 2, 3, 4, 5],
                            description=question["label_description"]
                        )
                    )
                elif question["question_type"] == "TextQuestion":
                    label_questions.append(
                        rg.TextQuestion(
                            name=question_name,
                            title=question['question_title'],
                            description=question["label_description"],
                            required = False
                            
                        )
                    )
                elif question["question_type"] == "Ranking":
                    # Make sure we have labels before creating ranking question
                    if question.get("labels"):
                        # Create a dictionary with labels as both keys and values
                        ranking_values = {
                            label.strip(): label.strip()
                            for label in question["labels"]
                        }
                        
                        label_questions.append(
                            rg.RankingQuestion(
                                name=question_name,
                                title=question['question_title'],
                                description=question["label_description"],
                                values=ranking_values  # Use dictionary format for values
                            )
                        )
                    else:
                        st.warning(f"Skipping ranking question '{question['question_title']}' because it has no labels.")
                elif question["question_type"] == "SpanQuestion":
                    field_name = question.get("span_field")
                    if field_name:
                        # Make sure to use the same sanitized field name that was used in fields
                        sanitized_field_name = sanitize_name(field_name)
                        label_questions.append(
                            rg.SpanQuestion(
                                name=question_name,
                                title=question["question_title"],
                                labels=question["labels"],
                                field=sanitized_field_name,  # Use sanitized field name
                                description=question["label_description"]
                            )
                        )
                

            # Create settings
            settings = rg.Settings(
                guidelines=guidelines,
                fields=fields,
                questions=label_questions,
                metadata=metadata_properties
            )

            # Create records with sanitized field names
            records = []
            for idx, row in dataset.iterrows():
                fields_dict = {
                    sanitize_name(col): convert_to_string(row[col])
                    for col in field_cols
                }
                
                metadata = {}
                if idx < len(json_data):
                    for meta_def in metadata_columns:
                        path = meta_def["path"].replace("data.", "")
                        value = get_value_from_path(json_data[idx], path)
                        if value is not None:
                            metadata[meta_def["text"]] = convert_to_string(value)
                
                record = rg.Record(
                    fields=fields_dict,
                    metadata=metadata
                )
                records.append(record)

            # Create and push dataset
            dataset_for_argilla = rg.Dataset(
                name=dataset_name,
                workspace=workspace_name,
                settings=settings
            )
            
            dataset_for_argilla.create()
            dataset_for_argilla.records.log(records)

            st.success("Data uploaded to Argilla successfully!")

        except Exception as e:
            st.error(f"Failed to upload to Argilla: {str(e)}")
            st.exception(e)  # This will show the full error traceback