import requests
import json
import os
import csv
from bs4 import BeautifulSoup
from collections import defaultdict

# Load configuration from CSV
def load_config(csv_path):
    config = {}
    with open(csv_path, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            config.update(row)
    return config

    # Function to map requirements to controls
def map_requirements_to_controls(grouped_controls, requirements_map):
    control_requirements_map = {}
    for category, controls in grouped_controls.items():
        for control in controls:
            control_id = control.get("control_id")
            requirement_ids = control.get("control_requirement_ids", [])
            
            # Match requirement_ids to requirement_name
            requirement_names = [requirements_map.get(req_id, "Unknown") for req_id in requirement_ids]
            control_requirements_map[control_id] = ", ".join(requirement_names)
            
    return control_requirements_map

# Main logic
def main():
    # Load configuration values from the CSV
    CONFIG_CSV = r"File path to your csv file"
    if not os.path.exists(CONFIG_CSV):
        raise FileNotFoundError(f"CSV file not found at: {CONFIG_CSV}")
    else:
        print(f"CSV file found: {CONFIG_CSV}")

    config = load_config(CONFIG_CSV)
    print("Loaded configuration:", config)

    # Extract configuration values
    ANECDOTES_AUTH_URL = config.get("ANECDOTES_AUTH_URL")
    API_ENDPOINT = config.get("API_ENDPOINT")
    FIELDS_API_ENDPOINT = config.get("FIELDS_API_ENDPOINT")
    CUSTOM_FIELDS_API_ENDPOINT = config.get("CUSTOM_FIELDS_API_ENDPOINT")
    TAGS_API_ENDPOINT = config.get("TAGS_API_ENDPOINT")
    REQUIREMENTS_API_ENDPOINT = config.get("REQUIREMENTS_API_ENDPOINT")
    FRAMEWORK_CATEGORY_API_ENDPOINT = config.get("FRAMEWORK_CATEGORY_API_ENDPOINT")
    ANECDOTES_API_KEY = os.getenv("ANECDOTES_API_KEY")
    if not ANECDOTES_API_KEY:
        raise ValueError("ANECDOTES_API_KEY environment variable is not set")

    CONFLUENCE_URL = config.get("CONFLUENCE_URL")
    CONFLUENCE_USERNAME = config.get("CONFLUENCE_USERNAME")
    DEV_API_TOKEN = os.getenv("DEV_API_TOKEN")
    if not DEV_API_TOKEN:
        raise ValueError("DEV_API_TOKEN environment variable is not set")

    CONTROL_FRAMEWORK_ID = config.get("control_framework_id")
    TEMPLATE_PAGE_ID = config.get("template_page_id")
    PAGE_ID = config.get("page_id")

    # Function to fetch the bearer token
    def fetch_bearer_token():
        headers = {"x-anecdotes-api-key": ANECDOTES_API_KEY, "accept": "text/plain"}
        response = requests.get(ANECDOTES_AUTH_URL, headers=headers)
        response.raise_for_status()
        return response.text.strip()
    
    # Function to fetch requirements data from the API
    def fetch_requirements_data(requirements_api_url, token):
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(requirements_api_url, headers=headers)
        response.raise_for_status()
        requirements = response.json()


        # Map requirement_id to requirement_name
        requirements_map = {req["requirement_id"]: req["requirement_name"] for req in requirements}
        return requirements_map

    #Fetch framework categories to match with controls
    def fetch_framework_categories(api_url, token):
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        categories = response.json()
        
        # Map category_id to category_name and framework_id
        category_map = {
            category["category_id"]: {
                "name": category["category_name"],
                "framework_id": category["framework_id"]
            }
        for category in categories
        }
        return category_map
    
    # Function to fetch data from the Anecdotes API
    def fetch_api_data(api_url, framework_category_api_url, token):
        headers = {"Authorization": f"Bearer {token}"}

        # Fetch all controls from the controls API
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        all_controls = response.json()

        # Filter controls by control_framework_id
        filtered_controls = [
            control for control in all_controls
            if control.get("control_framework_id") == CONTROL_FRAMEWORK_ID
        ]

        # Fetch framework categories
        framework_categories = fetch_framework_categories(framework_category_api_url, token)

        # Group controls by category_name
        grouped_controls = defaultdict(list)
        for control in filtered_controls:
            category_id = control.get("control_framework_category_id")
            category_info = framework_categories.get(category_id, {})
            
            # Use category_name if available, else default to "Uncategorized"
            category_name = category_info.get("name", "Uncategorized")
            control["category_name"] = category_name
            grouped_controls[category_name].append(control)

        # Sort controls within each category by control_name
        for category_name, controls in grouped_controls.items():
            grouped_controls[category_name] = sorted(controls, key=lambda x: x.get("control_name", ""))

        return grouped_controls


    # Function to fetch field values from the FIELDS_API_ENDPOINT
    def fetch_field_values(fields_api_url, token):
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(fields_api_url, headers=headers)
        response.raise_for_status()
        fields_data = response.json()

        # Extract values for specific fields
        control_values = {}
        scoped_systems_map = {}

        for control_id, fields in fields_data.items():
            # Evidence field
            field_details = fields.get("<CUSTOM_FIELD_VALUE>", {})
            control_values[control_id] = field_details.get("value", "N/A")

            # Scoped systems field
            scoped_field = fields.get("<CUSTOM_FIELD_VALUE>", {}).get("value", [])
            if scoped_field:
                scoped_systems_map[control_id] = scoped_field

        return control_values, scoped_systems_map

    # Function to fetch custom field values from the CUSTOM_FIELDS_API_ENDPOINT
    def fetch_custom_field_values(custom_fields_api_url, token):
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(custom_fields_api_url, headers=headers)
        response.raise_for_status()
        return response.json()

    # Function to map scoped systems
    def map_scoped_systems(scoped_systems_map, custom_fields_data):
        # Convert the custom fields data into a dictionary for quick lookup
        custom_fields_dict = {
            field.get("id"): field.get("field_metadata", {}).get("values", {})
            for field in custom_fields_data
        }

        # Map scoped systems
        scoped_systems = {}
        for control_id, keys in scoped_systems_map.items():
            # Map each key to its value using the dictionary
            field_values = custom_fields_dict.get("<CUSTOM_FIELD_VALUE>)", {})
            if not field_values:
                scoped_systems[control_id] = "No Scoped Systems"
                continue

            values = [field_values.get(key, "Unknown") for key in keys]
            scoped_systems[control_id] = ", ".join(values)

        return scoped_systems

    # Function to fetch tag data from the TAGS_API_ENDPOINT
    def fetch_tags(tags_api_url, token):
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(tags_api_url, headers=headers)
        response.raise_for_status()
        tags_data = response.json()

        # Map tag names to control IDs
        tag_map = defaultdict(list)
        for tag in tags_data:
            tag_name = tag.get("tag_name")
            for entity in tag.get("tagged_entities", []):
                if entity.get("entity_type") == "control":
                    tag_map[entity.get("entity_id")].append(tag_name)

        return tag_map

    # Function to fetch the Confluence page content
    def get_confluence_page(page_id):
        url = f"{CONFLUENCE_URL}/content/{page_id}?expand=body.storage,version"
        response = requests.get(url, auth=(CONFLUENCE_USERNAME, DEV_API_TOKEN))
        response.raise_for_status()
        return response.json()

    # Function to fetch the template content
    def get_template_content(template_page_id):
        url = f"{CONFLUENCE_URL}/content/{template_page_id}?expand=body.storage"
        response = requests.get(url, auth=(CONFLUENCE_USERNAME, DEV_API_TOKEN))
        response.raise_for_status()
        data = response.json()

        # Extract the template content
        template_content = data.get("body", {}).get("storage", {}).get("value", "")
        if not template_content:
            raise ValueError("Failed to fetch the template content. Ensure the template page exists and has valid content.")

        return template_content

    # Function to update the Confluence page content
    def update_confluence_page(page_id, title, new_content, version_number):
        url = f"{CONFLUENCE_URL}/content/{page_id}"
        headers = {"Content-Type": "application/json"}

        payload = {
            "id": page_id,
            "type": "page",
            "title": title,
            "body": {"storage": {"value": new_content, "representation": "storage"}},
            "version": {"number": version_number + 1}
        }

        print(f"Sending updated content to Confluence page {page_id}...")

        response = requests.put(url, auth=(CONFLUENCE_USERNAME, DEV_API_TOKEN), headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            print("Error response from Confluence:")
            print(response.text)
        response.raise_for_status()
        return response.json()

    # Function to replace placeholders for grouped controls
    def replace_placeholders(content, grouped_controls, control_values, tag_map, scoped_systems, control_requirements):
        for category, controls in grouped_controls.items():
            for i, control in enumerate(controls, start=1):
                category_key = category.replace(" ", "_")  # Handle spaces in categories
                control_id = control.get("control_id", f"control_{i}")

                # Replace placeholders for grouped_controls
                content = content.replace(f"{{{{{category_key}_control_framework_category_{i}}}}}", control.get("category_name", "N/A"))
                content = content.replace(f"{{{{{category_key}_control_name_{i}}}}}", control.get("control_name", "N/A"))
                content = content.replace(f"{{{{{category_key}_control_description_{i}}}}}", control.get("control_description", "N/A"))

                # Replace placeholders for custom fields like "Control implementation"
                content = content.replace(
                    f"{{{{{category_key}_control_custom_fields.Control implementation_{i}}}}}",
                    control.get("control_custom_fields", {}).get("Control implementation", "N/A")
                )

                # Replace placeholders for requirements
                requirements = control_requirements.get(control_id, "N/A")
                if isinstance(requirements, str):  # If requirements is a single string, split it into lines
                    requirements = requirements.split(", ")
                requirements_formatted = "<br>".join(requirements)  # Format each entry on a new line using <br>
                content = content.replace(f"{{{{{category_key}_control_requirements_{i}}}}}", requirements_formatted)

                # Replace placeholders for "value" from fields API
                value = control_values.get(control_id, "N/A")
                content = content.replace(
                    f"{{{{{category_key}_control_fields_value_{i}}}}}",
                    value
                )

                # Replace placeholders for tags
                tags = ", ".join(tag_map.get(control_id, []))
                content = content.replace(
                    f"{{{{{category_key}_control_tags_{i}}}}}",
                    tags
                )

                # Replace placeholders for scoped systems
                scoped = scoped_systems.get(control_id, "N/A")
                if isinstance(scoped, list):  # If scoped is a list, join it into a string
                    scoped = ", ".join(scoped)  # Convert list to comma-separated string
                elif isinstance(scoped, str):  # If scoped is already a string, strip any unwanted characters
                    scoped = scoped.strip("{}")  # Remove curly braces if accidentally included

                content = content.replace(
                    f"{{{{{category_key}_control_scoped_systems_{i}}}}}",
                    scoped
                )

        return content

    # Function to clean and sanitize HTML
    def clean_html(content):
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup.find_all():
            tag.attrs = {k: v for k, v in tag.attrs.items() if k in ["style", "colspan", "rowspan"]}
        return str(soup)

    # Execution flow
    print("Fetching Bearer Token...")
    token = fetch_bearer_token()
    print("Bearer Token fetched successfully.")

    print("Fetching data from the Anecdotes API...")
    grouped_controls = fetch_api_data(API_ENDPOINT, FRAMEWORK_CATEGORY_API_ENDPOINT, token)

    print("Fetching field values from the fields API...")
    control_values, scoped_systems_map = fetch_field_values(FIELDS_API_ENDPOINT, token)

    print("Fetching custom field values from the custom fields API...")
    custom_fields_data = fetch_custom_field_values(CUSTOM_FIELDS_API_ENDPOINT, token)

    print("Mapping scoped systems...")
    scoped_systems = map_scoped_systems(scoped_systems_map, custom_fields_data)

    print("Fetching tags from the tags API...")
    tag_map = fetch_tags(TAGS_API_ENDPOINT, token)

    print(f"Fetching template content from page ID {TEMPLATE_PAGE_ID}...")
    try:
        base_content = get_template_content(TEMPLATE_PAGE_ID)
    except ValueError as e:
        print(str(e))
        return

    print("Template content fetched successfully.")

    print("Fetching requirements data...")
    requirements_map = fetch_requirements_data(REQUIREMENTS_API_ENDPOINT, token)

    print("Mapping requirements to controls...")
    control_requirements_map = map_requirements_to_controls(grouped_controls, requirements_map)

    print("Replacing placeholders with grouped JSON values...")
    updated_content = replace_placeholders(base_content, grouped_controls, control_values, tag_map, scoped_systems, control_requirements_map)

    print("Sanitizing updated content...")
    updated_content = clean_html(updated_content)

    print("Fetching the current version of the page...")
    current_page_data = get_confluence_page(PAGE_ID)
    current_version = current_page_data["version"]["number"]
    page_title = current_page_data["title"]

    print(f"Updating the target Confluence page, {PAGE_ID}...")
    update_confluence_page(PAGE_ID, page_title, updated_content, current_version)
    print("Dev/Sandbox Confluence page updated successfully!")

if __name__ == "__main__":
    main()
