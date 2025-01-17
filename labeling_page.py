import streamlit as st
import pandas as pd
import json

def get_value_from_path(data, path):
    """Extract value from nested JSON using dot notation path"""
    try:
        # Split the path into parts
        parts = path.split('.')
        current = data
        
        # Handle the special case where first element is 'data'
        if parts[0] == 'data':
            current = current['data'][0]  # Get first item from data array
            parts = parts[1:]  # Remove 'data' from parts
            
        # Navigate through the path
        for part in parts:
            current = current[part]
        return current
    except (KeyError, IndexError, TypeError):
        return None

def get_nested_value(obj, path_parts):
    """
    Safely navigate nested structures (both dicts and lists) and return all
    matched items if a path leads into a list of objects. 
    """
    # We'll collect intermediate matches as a list so we can gather multiple values
    current = [obj]
    for part in path_parts:
        next_values = []
        for element in current:
            if isinstance(element, dict):
                # If dict, try to get the child by key.
                val = element.get(part, None)
                if val is not None:
                    # If val is a list, expand it into next_values; else just append
                    if isinstance(val, list):
                        next_values.extend(val)
                    else:
                        next_values.append(val)
            elif isinstance(element, list):
                # If we already have a list, flatten it so we can keep looking
                next_values.extend(element if isinstance(element, list) else [])
            # If something is None or not dict/list, we skip it
        current = next_values
        # If we have an empty list here, no need to keep going
        if not current:
            return None
    
    # If at the end we only have one item in current, return it directly
    if len(current) == 1:
        return current[0]
    return current

def filter_redundant_paths(selected_paths):
    """
    Given a list of path_info dicts like:
        [{"text": "doc_id", "path": "doc_id"}, {"text": "id", "path": "sentence.NE.id"}, ...]
    Remove any paths that are children of a parent path that is also selected.
    A path A is parent of path B if B starts with A + ".".
    """
    # Convert them to list of (text, path) for easier handling
    sp_list = [(p["text"], p["path"]) for p in selected_paths]
    # Sort shorter paths first so we remove children last
    sp_list.sort(key=lambda x: len(x[1]))

    final_paths = []
    for text_i, path_i in sp_list:
        # Check if path_i has a parent in final_paths
        is_child = False
        for text_j, path_j in final_paths:
            if path_i.startswith(path_j + "."):
                # path_j is a parent of path_i
                is_child = True
                break
        if not is_child:
            final_paths.append((text_i, path_i))

    # Convert back to the original "text/path" dict format
    return [{"text": t, "path": p} for t, p in final_paths]

def create_dataframe_from_json(json_data, selected_paths):
    """Create a DataFrame from JSON data using selected paths"""
    if isinstance(selected_paths, str):
        selected_paths = json.loads(selected_paths)

    # Filter selections to avoid duplicates while maintaining order
    filtered_paths = filter_redundant_paths(selected_paths)
    
    records = []
    for item in json_data['data']:
        record = {}
        # Use OrderedDict or maintain order in regular dict (Python 3.7+)
        for path_info in filtered_paths:
            column_name = path_info['text']
            
            path_parts = path_info['path'].split('.')
            if path_parts and path_parts[0] == 'data':
                path_parts = path_parts[1:]  # Remove 'data' prefix
                
            value = get_nested_value(item, path_parts)
            record[column_name] = value
        records.append(record)
    
    # Create DataFrame with explicit column order
    df = pd.DataFrame(records)
    
    # Reorder columns to match the order in filtered_paths
    ordered_columns = [path_info['text'] for path_info in filtered_paths]
    df = df[ordered_columns]
    
    return df

def format_value(value):
    """Format a single value for display."""
    if isinstance(value, dict):
        formatted_lines = []
        for k, v in value.items():
            if isinstance(v, (dict, list)):
                formatted_lines.append(f"{k}:")
                formatted_lines.extend("    " + line for line in format_value(v).split("\n"))
            else:
                formatted_lines.append(f"{k}:{v}")
        return "\n".join(formatted_lines)
    elif isinstance(value, list):
        # For list of dictionaries, format each item
        if value and isinstance(value[0], dict):
            formatted_items = []
            for item in value:
                item_lines = []
                for k, v in item.items():
                    item_lines.append(f'"{k}" : {json.dumps(v, ensure_ascii=False)}')
                formatted_items.append("\n".join(item_lines))
            return "\n\n".join(formatted_items)
        else:
            return ", ".join(map(str, value))
    return str(value)

def display_labeling_page():
    st.set_page_config(layout="wide")
    st.title("Playground for Labelling before uploading to Argilla")
    # Initialize session state variables
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0
    if "labels_selected" not in st.session_state:
        st.session_state.labels_selected = {}
    if "labeling_complete" not in st.session_state:
        st.session_state.labeling_complete = False
    
    # Get the JSON data and selected columns from session state
    json_data = st.session_state.get("json_data")  # Make sure to store the original JSON data
    selected_columns = st.session_state.get("selected_columns", [])

    # Create DataFrame if not already created
    if "dataset" not in st.session_state and json_data and selected_columns:
        st.session_state.dataset = create_dataframe_from_json(json_data, selected_columns)
    

    col1, col2 = st.columns([2, 1])

    # Left column: Display one dataset record at a time
    with col1:
        dataset = st.session_state.get("dataset")
        
        # Navigation buttons in a row
        col1_nav, col2_nav = st.columns([1, 1])
        with col1_nav:
            if st.button("⬅️ Previous", key="prev_btn") and st.session_state.current_index > 0:
                st.session_state.current_index -= 1
                st.session_state.form_submitted = False
                st.rerun()

        with col2_nav:
            if st.button("Next ➡️", key="next_btn") and st.session_state.current_index < len(dataset) - 1:
                st.session_state.current_index += 1
                st.session_state.form_submitted = False
                st.rerun()

        if dataset is not None and not dataset.empty:
            st.markdown("#### Dataset Records")
            
            if 0 <= st.session_state.current_index < len(dataset):
                record = dataset.iloc[st.session_state.current_index]
                
                # Get only the user-selected data columns (exclude columns that correspond to question titles)
                question_titles = [q.get('question_title', '') for q in st.session_state.get("questions", [])]
                
                # Maintain order from selected_columns
                data_columns = []
                for col_info in st.session_state.get("selected_columns", []):
                    col_name = col_info['text']
                    if col_name in dataset.columns and col_name not in question_titles:
                        data_columns.append(col_name)
                
                # Build an ordered dictionary for the current record
                record_dict = {}
                for col in data_columns:
                    record_dict[col] = record[col]
                
                # Display the chosen columns recursively with our format_value function
                st.code(format_value(record_dict), language="json")

    # Right column: Questions form
    with col2:
        st.markdown("#### User Questions")
        questions = st.session_state.get("questions", [])

        # Initialize form_submitted in session state if not exists
        if "form_submitted" not in st.session_state:
            st.session_state.form_submitted = False

        user_responses = {}
        if questions:
            # Create a form for questions
            with st.form(key=f"questions_form_{st.session_state.current_index}"):
                for idx, question in enumerate(questions, start=1):
                    st.markdown(f"**{idx}. {question['question_title']}**")

                    if question['question_type'] == "Label" or "SpanQuestion":
                        response = st.radio(
                            f"{question['label_description']}",
                            question['labels'],
                            key=f"label_{idx}_{st.session_state.current_index}",
                            horizontal=True
                        )
                        user_responses[question['question_title']] = response

                    elif question['question_type'] == "Multi-label":
                        selected_labels = []
                        for label in question['labels']:
                            if st.checkbox(
                                label, 
                                key=f"multi_label_{label}_{st.session_state.current_index}",
                                value=False  # Reset to unchecked
                            ):
                                selected_labels.append(label)
                        user_responses[question['question_title']] = ", ".join(selected_labels)

                    elif question['question_type'] == "Rating":
                        response = st.radio(
                            f"{question['label_description']}",
                            [1, 2, 3, 4, 5],
                            key=f"rating_{idx}_{st.session_state.current_index}",
                            horizontal=True
                        )
                        user_responses[question['question_title']] = response

                    elif question['question_type'] == "TextQuestion":
                        response = st.text_input(
                            question['label_description']
                        )
                        user_responses[question['question_title']] = response
                    elif question['question_type'] == "Ranking":
                        # Create a list for reordering
                        ranking_options = question['labels']
                        
                        # Use selectbox for each rank position
                        ranked_items = []
                        remaining_options = list(ranking_options)
                        
                        for rank in range(len(ranking_options)):
                            if remaining_options:
                                selected = st.selectbox(
                                    f"Rank {rank + 1}",
                                    remaining_options,
                                    key=f"rank_{rank}_{idx}_{st.session_state.current_index}"
                                )
                                ranked_items.append(selected)
                                remaining_options.remove(selected)
                        
                        # Store the complete ranking
                        user_responses[question['question_title']] = ranked_items

                    elif question['question_type'] == "SpanQuestion":
                        st.markdown(f"**Selected text field for annotation:** {question['span_field']}")
                        # Display the text that can be annotated
                        field_text = record[question['span_field']]
                        st.text_area("Text to annotate:", field_text, disabled=True)
                        
                        # For now, we'll use a simple text input for spans
                        # In a real implementation, you might want to add a more sophisticated span selection UI
                        span_text = st.text_input(
                            "Enter the text span to annotate:",
                            key=f"span_{idx}_{st.session_state.current_index}"
                        )
                        
                        if span_text:
                            # Validate that the entered span exists in the text
                            if span_text in field_text:
                                span_label = st.radio(
                                    f"Select label for span: '{span_text}'",
                                    question['labels'],
                                    key=f"span_label_{idx}_{st.session_state.current_index}",
                                    horizontal=True
                                )
                                user_responses[question['question_title']] = {
                                    'span': span_text,
                                    'label': span_label,
                                    'start': field_text.index(span_text),
                                    'end': field_text.index(span_text) + len(span_text)
                                }
                            else:
                                st.error("The entered text span was not found in the field text.")

                # Submit button inside the form
                submit_button = st.form_submit_button("Submit")
                
                if submit_button:
                    # Save responses to dataset
                    for question_title, response in user_responses.items():
                        st.session_state.dataset.loc[
                            st.session_state.current_index, question_title
                        ] = response

                    # Mark form as submitted
                    st.session_state.form_submitted = True

                    # Move to next example if not at the end
                    if st.session_state.current_index < len(dataset) - 1:
                        st.session_state.current_index += 1
                        st.rerun()
                    else:
                        st.success("🎉 All examples have been labeled!")
                        st.session_state.labeling_complete = True

        # Show completion message if all examples are labeled
        if st.session_state.labeling_complete:
            st.success("🎉 All examples have been labeled!")
            
        if st.button("➡️ Upload to Argilla"):
            st.session_state.page = 4  # Redirect to the upload page
            st.rerun()

    # Save labeled data as CSV
    if st.session_state.get("labeling_complete"):
        if st.button("Save labeled data"):
            labeled_df = pd.DataFrame(st.session_state.dataset)
            labeled_df.to_csv("labeled_data.csv", index=False)
            st.success("Labeled data saved as 'labeled_data.csv'!")
            st.rerun()