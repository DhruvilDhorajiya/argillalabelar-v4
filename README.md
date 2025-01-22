# ArgillaLabeler

ArgillaLabeler is an interactive data labeling tool that provides a streamlined interface for creating custom labeling workflows and seamlessly uploading labeled datasets to Argilla. It supports various question types and flexible data structures, making it ideal for diverse annotation tasks.

## Features

- **Flexible Data Input**: Support for both JSON and JSONL file formats
- **Interactive Field Selection**: Tree-view interface for selecting fields to label
- **Multiple Question Types**:
  - Label (Single choice)
  - Multi-label
  - Rating (1-10 scale)
  - Text (Free form)
  - Span (Text annotation)
  - Ranking
- **Metadata Support**: Separate handling of display and metadata fields
- **Argilla Integration**: Direct upload to Argilla servers (HuggingFace Space or Custom)
- **User-friendly Interface**: Built with Streamlit for a smooth user experience

## Data Format Support

ArgillaLabeler accepts any valid JSON/JSONL structure. Here are some example formats that can be handled:

### Simple Flat Structure
```json
{
  "data": [
    {
      "text": "Sample text",
      "category": "A"
    }
  ]
}
```

### Complex Nested Structure
```json
{
  "data": [
    {
      "document": {
        "content": {
          "title": "Example",
          "paragraphs": [
            {"text": "First paragraph"},
            {"text": "Second paragraph"}
          ]
        },
        "metadata": {
          "author": {
            "name": "John",
            "id": 123
          }
        }
      }
    }
  ]
}
```

The tool provides an interactive tree-view interface that allows you to:
- Navigate and select fields from any nested level
- Separate display fields from metadata
- Handle arrays and nested objects
- Process any valid JSON structure

> **Note**: While the tool accepts any JSON structure, it expects the data to be wrapped in a "data" array at the root level. The tool will automatically handle this conversion if needed.

## Example Data Formats

### JSON Format
```json
{
  "data": [
    {
      "id": "1",
      "text": "This product is amazing!",
      "metadata": {
        "source": "amazon",
        "category": "electronics"
      }
    },
    {
      "id": "2",
      "text": "The quality could be better",
      "metadata": {
        "source": "reviews",
        "category": "clothing"
      }
    }
  ]
}
```

### JSONL Format
```jsonl
{"id": "1", "text": "This product is amazing!", "metadata": {"source": "amazon", "category": "electronics"}}
{"id": "2", "text": "The quality could be better", "metadata": {"source": "reviews", "category": "clothing"}}
```

### Nested Data Example
```json
{
  "data": [
    {
      "document": {
        "id": "1",
        "content": {
          "title": "Product Review",
          "body": "Great product, highly recommended!",
          "ratings": {
            "quality": 5,
            "price": 4
          }
        },
        "user": {
          "id": "user123",
          "country": "US"
        }
      }
    }
  ]
}
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/argillalabeler.git
cd argillalabeler
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
streamlit run main.py
```

2. Follow the workflow:
   - Upload your JSON/JSONL file
   - Select fields for labeling and metadata
   - Create custom questions
   - Label your data(Playground) 
   - Upload to Argilla

## Workflow Steps

1. **Upload Page**
   - Upload JSON/JSONL file
   - Select fields for display and metadata
   - Interactive tree view for nested data structures

2. **Question Page**
   - Create custom questions
   - Configure question types and options
   - Add descriptions and guidelines

3. **Labeling Page(Playground)**
   - Interactive labeling interface
   - Preview of data fields
   - Navigation between records

4. **Argilla Upload Page**
   - Configure Argilla server settings
   - Add labeling guidelines
   - Upload dataset with metadata

## Requirements

- Python 3.9+
- Streamlit
- Argilla
- Pandas
- Other dependencies listed in requirements.txt

## Configuration

The application supports two types of Argilla server configurations:

1. **HuggingFace Space**:
   - Default URL: https://your-space.hf.space/
   - Requires API key

2. **Custom Server**:
   - Custom URL configuration
   - API key authentication
   - Workspace customization

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Integrates with [Argilla](https://argilla.io/)

## Question Types Guide

### Label Question Type
Label questions allow users to select a single option from predefined choices.

#### Required Fields:
- **Question Title**: (Required)
  - Example: "Sentiment Analysis"
  - Must be unique across all questions
  - Used as field name in Argilla

- **Labels**: (Required)
  - Format: Comma-separated values
  - Example: "Positive, Negative, Neutral"
  - At least one label required
  - Each label must be unique

#### Optional Fields:
- **Question Description**: (Optional)
  - Example: "Select the overall sentiment of this review"
  - Provides context to annotators
  - Helps maintain consistent labeling

#### Example Configuration:
```
Question Title: Product Quality Assessment
Description: Rate the quality of the product based on the review
Labels: High Quality, Average Quality, Low Quality
```

#### Use Cases:
1. **Sentiment Analysis**
   - Title: "Review Sentiment"
   - Labels: "Positive, Negative, Neutral"
   - Description: "Choose the sentiment expressed in the review"

2. **Content Classification**
   - Title: "Content Category"
   - Labels: "News, Opinion, Advertisement"
   - Description: "Select the type of content"

3. **Intent Classification**
   - Title: "Customer Intent"
   - Labels: "Purchase, Question, Complaint"
   - Description: "Identify the primary intent of the customer"

#### Best Practices:
1. Keep labels clear and mutually exclusive
2. Use consistent label terminology
3. Provide clear description for edge cases
4. Limit number of labels (3-7 recommended)

#### Notes:
- Labels cannot contain commas
- Question title must be unique
- Changes cannot be made after question creation
