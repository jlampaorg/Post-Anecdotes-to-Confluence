# README: Utilizing the Script for Data Integration with Confluence

## Note:
Use the script referenced in this document at your own discretion. The author takes no responsibility for the output from this script used in different organizations. Please review the code and understand the risks and subsequent changes.

## Overview

This script integrates data from multiple APIs and updates a Confluence page with the processed information. It uses a configuration CSV file to specify API endpoints and other required parameters. The script processes and maps controls, framework categories, requirements, and other metadata before formatting and pushing the content to Confluence.

### Key Features:

- Fetches and processes control data from Anecdotes APIs.
- Maps controls to framework categories using API responses.
- Replaces placeholders in a Confluence template with dynamic data.
- Updates the specified Confluence page.

## Requirements

1. **Python 3.x**

2. **Libraries**: Install the following dependencies using `pip install`:

   - `requests`
   - `beautifulsoup4`

3. **Configuration CSV**: The script requires a CSV file containing API endpoint URLs and other configuration values.

4. **Environment Variables**: Set the following environment variables:

   - `ANECDOTES_API_KEY`: API key for authentication (read-only API token from Anecdotes Admin UI).
   - `DEV_API_TOKEN`: API token for Confluence authentication.
  
5.	Update any instances of <CUSTOM_FIELD_VALUE> with the applicable values for your Anecdotes instance.
   
7.	Use your favorite API explorer (e.g. Postman) to understand what fields are required for your instance of this script.

---

## Process Documentation

### Steps to Utilize the Script

#### 1. **Prepare the Configuration CSV**

The configuration CSV should include the following columns:

| Column Name                       | Description                                                                                                                        |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `ANECDOTES_AUTH_URL`              | Endpoint to fetch the authentication token from Anecdotes.                                                                         |
| `API_ENDPOINT`                    | Endpoint to fetch control data.                                                                                                    |
| `FIELDS_API_ENDPOINT`             | Endpoint to fetch field values for controls.                                                                                       |
| `CUSTOM_FIELDS_API_ENDPOINT`      | Endpoint to fetch custom field values for controls.                                                                                |
| `TAGS_API_ENDPOINT`               | Endpoint to fetch tags associated with controls.                                                                                   |
| `REQUIREMENTS_API_ENDPOINT`       | Endpoint to fetch requirement data.                                                                                                |
| `FRAMEWORK_CATEGORY_API_ENDPOINT` | Endpoint to fetch framework categories (maps `category_id` to `category_name`).                                                    |
| `CONFLUENCE_URL`                  | Base URL for the Confluence instance.                                                                                              |
| `CONFLUENCE_USERNAME`             | Username for Confluence authentication.                                                                                            |
| `control_framework_id`            | ID of the framework to filter controls.                                                                                            |
| `template_page_id`                | ID of the Confluence template page to be used for updating content. (Ensure you have set your placeholders in the Confluence page) |
| `page_id`                         | ID of the Confluence page to update.                                                                                               |

#### 2. **Set Up Environment Variables**

Ensure the following environment variables are set:

- **`ANECDOTES_API_KEY`**: The Anecdotes API key for authentication (use the read-only API token from Anecdotes Admin UI).
- **`DEV_API_TOKEN`**: The API token for Confluence.

#### 3. **Run the Script**

1. Ensure the required Python libraries are installed.
2. Place the CSV file in the correct path (update the `CONFIG_CSV` variable in the script if needed).
3. **Test the script in a sandbox environment before moving to production.**
4. Double-check the Confluence `page_id` in the CSV to ensure you're updating the correct page.
5. Run the script:
   ```bash
   python your_script_name.py
   ```

#### 4. **Output**

- The script fetches data from the APIs and processes it.
- The Confluence page (specified by `page_id`) is updated with dynamic content, replacing placeholders in the template.

---

## Placeholder Syntax Examples for the Confluence Template page

When creating the Confluence template, use the following placeholder syntax for dynamic content:

| Placeholder Syntax                                                | Description                                                                 |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `{{CategoryName_control_framework_category_1}}`                   | Replaced with the name of the control framework category (e.g., "Finance"). |
| `{{CategoryName_control_name_1}}`                                 | Replaced with the name of the first control in the category.                |
| `{{CategoryName_control_description_1}}`                          | Replaced with the description of the first control in the category.         |
| `{{CategoryName_control_custom_fields.Control implementation_1}}` | Replaced with custom field values like "Control implementation."            |
| `{{CategoryName_control_requirements_1}}`                         | Replaced with requirements related to the first control in the category.    |
| `{{CategoryName_control_fields_value_1}}`                         | Replaced with the field value from the fields API for the first control.    |
| `{{CategoryName_control_tags_1}}`                                 | Replaced with tags associated with the first control.                       |
| `{{CategoryName_control_scoped_systems_1}}`                       | Replaced with scoped systems for the first control.                         |

Repeat the above placeholders for subsequent controls (e.g., `_2`, `_3`) in the same category.

---

## Script Workflow

#### Step 1: Fetch Authentication Token

- The script calls the `ANECDOTES_AUTH_URL` endpoint using the API key to fetch a bearer token for subsequent API requests.

#### Step 2: Fetch Data from APIs

- **Control Data**: Pulled from `API_ENDPOINT`.
- **Framework Categories**: Mapped from `FRAMEWORK_CATEGORY_API_ENDPOINT`.
- **Requirements Data**: Pulled from `REQUIREMENTS_API_ENDPOINT`.
- **Field Values**: OOTB Anecdotes' fields pulled from `FIELDS_API_ENDPOINT`.
- **Custom Fields**: Custom fields for your Anecdotes' instance, pulled from `CUSTOM_FIELDS_API_ENDPOINT`.
- **Tags**: Pulled from `TAGS_API_ENDPOINT`.

#### Step 3: Map and Process Data

- Controls are grouped by `category_name` (mapped from `category_id` using framework categories API).
- Requirements are mapped to controls.
- Field values, tags, and custom fields are processed and associated with their respective controls.

#### Step 4: Replace Placeholders in Template

- The script fetches the template content from the Confluence page (`template_page_id`).
- Placeholders are replaced with processed data (e.g., `category_name`, `control_name`, etc.).

#### Step 5: Update Confluence Page

- The updated content is pushed to the Confluence page (`page_id`) using a PUT request.

---

## Error Handling

1. **Missing Environment Variables**:
   - Ensure both `ANECDOTES_API_KEY` and `DEV_API_TOKEN` are set.
2. **CSV Not Found**:
   - Confirm the `CONFIG_CSV` path is correct.
3. **API Errors**:
   - Check for valid responses from the APIs and update the endpoints if needed.

---

## Key Points

- Ensure accurate mapping of `category_id` to `category_name` for proper grouping.
- Validate API endpoints and credentials before running the script.
- Test with a sample Confluence page/template before using production pages.
- **Always test in sandbox environments before moving to production.**
- **Double-check the Confluence `page_id` in the CSV to avoid unintended updates.**
- For custom-fields, please review function **map_scoped_systems** and update with the necessary object architecture for your **custom-fields** JSON format. Also, replace the field# with the applicable values for your instance.
