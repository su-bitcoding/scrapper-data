from flask import Flask, render_template_string, request
import json

app = Flask(__name__)

json_data = {}


def get_unique_keys_from_array(arr):
    """Extract unique keys from an array of dictionaries."""
    unique_keys = set()
    for item in arr:
        if isinstance(item, dict):
            unique_keys.update(item.keys())
    return unique_keys

def merge_objects(objects):
    """Merge multiple objects into a single object with all unique keys."""
    result = {}
    for obj in objects:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key not in result:
                    if isinstance(value, list) and value and isinstance(value[0], dict):
                        result[key] = merge_objects(value)
                    elif isinstance(value, dict):
                        result[key] = process_json_data(value)
                    else:
                        result[key] = value
    return result

def process_json_data(data):
    """Process JSON data to create a template with unique keys."""
    if isinstance(data, dict):
        processed = {}
        for key, value in data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                # For arrays of objects, merge them into a single object
                processed[key] = merge_objects(value)
            elif isinstance(value, dict):
                processed[key] = process_json_data(value)
            else:
                processed[key] = value
        return processed
    elif isinstance(data, list) and data and isinstance(data[0], dict):
        return merge_objects(data)
    return data

@app.route("/", methods=["GET", "POST"])
def upload_and_select():
    global json_data
    if request.method == "POST":
        file = request.files.get("json_file")
        if file and file.filename.endswith(".json"):
            # Load and process the JSON data
            original_data = json.load(file)
            json_data = process_json_data(original_data)
            print("::::::::::::::::::::  ", json_data)
            return render_template_string(
                SELECT_FIELDS_TEMPLATE, json_data=json.dumps(json_data)
            )
    return render_template_string(UPLOAD_TEMPLATE)


@app.route("/generate_form", methods=["POST"])
def generate_form():
    selected_fields = request.form.getlist("fields")
    selected_data = extract_selected_fields(json_data, selected_fields)
    form_html = render_form_fields(selected_data)
    return render_template_string(FORM_TEMPLATE, form_html=form_html)


@app.route("/submit_form", methods=["POST"])
def submit_form():
    form_data = request.form.to_dict(flat=False)
    return f"<h3>Form Submitted</h3><pre>{json.dumps(form_data, indent=2)}</pre>"


def extract_selected_fields(data, selected_keys, prefix=""):
    result = {}
    for key, val in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if full_key in selected_keys:
            result[key] = val
        elif isinstance(val, dict):
            nested = extract_selected_fields(val, selected_keys, full_key)
            if nested:
                result[key] = nested
        elif isinstance(val, list):
            if val and isinstance(val[0], dict):
                result[key] = [
                    extract_selected_fields(item, selected_keys, full_key)
                    for item in val
                ]
            elif full_key in selected_keys:
                result[key] = val
    return result


def render_form_fields(data, prefix=""):
    html = ""
    if isinstance(data, dict):
        for key, val in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(val, dict):
                html += f"<fieldset><label>{key}</label>"
                html += render_form_fields(val, full_key)
                html += "</fieldset>"
            elif isinstance(val, list):
                container_id = f"{full_key.replace('.', '_')}_container"
                html += f"<fieldset><label>{key}</label><div id='{container_id}'>"
                for i, item in enumerate(val):
                    item_prefix = f"{full_key}[{i}]"
                    item_id = f"{container_id}_{i}"
                    html += f"<div id='{item_id}'>"
                    if isinstance(item, dict):
                        for subkey, subval in item.items():
                            input_name = f"{item_prefix}.{subkey}"
                            html += f"<label>{subkey}: <input name='{input_name}' value='{subval}' /></label><br>"
                    else:
                        html += f"<label><input name='{item_prefix}' value='{item}' /></label><br>"
                    html += f"<button type='button' onclick='removeElement(\"{item_id}\")'>Delete</button><hr></div>"
                html += f"</div><button type='button' onclick='addField(\"{container_id}\", \"{full_key}\", {json.dumps(val[0]) if val else 'null'})'>Add More</button>"
                html += "</fieldset>"
            else:
                html += f"<label>{key}: <input name='{full_key}' value='{val}' /></label><br>"
    return html


UPLOAD_TEMPLATE = """
<!doctype html>
<title>Upload JSON</title>
<h2>Upload JSON file</h2>
<form method=post enctype=multipart/form-data>
  <input type='file' name='json_file'/>
  <input type=submit value='Upload'/>
</form>
"""

SELECT_FIELDS_TEMPLATE = """
<!doctype html>
<title>Select Fields</title>
<h2>Select Fields to Include</h2>
<form method=post action="/generate_form">
  <div id="json-tree"></div>
  <input type=submit value="Generate Form"/>
</form>
<script>
const data = {{ json_data|safe }};
const container = document.getElementById('json-tree');

function buildCheckboxTree(obj, prefix = '') {
    const ul = document.createElement('ul');

    Object.entries(obj).forEach(([key, val]) => {
        const li = document.createElement('li');
        const fullKey = prefix ? `${prefix}.${key}` : key;

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.name = 'fields';
        checkbox.value = fullKey;
        checkbox.id = fullKey;
        checkbox.addEventListener('change', () => toggleNested(li, checkbox.checked));

        const label = document.createElement('label');
        label.textContent = key;
        label.htmlFor = fullKey;

        li.appendChild(checkbox);
        li.appendChild(label);

        if (typeof val === 'object' && val !== null) {
            li.appendChild(buildCheckboxTree(val, fullKey));
        }

        ul.appendChild(li);
    });

    return ul;
}

function toggleNested(li, checked) {
    const checkboxes = li.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = checked);
}

container.appendChild(buildCheckboxTree(data));
</script>
"""

FORM_TEMPLATE = """
<!doctype html>
<title>Generated Form</title>
<h2>Generated Form</h2>
<form method=post action="/submit_form">
  {{ form_html|safe }}
  <br><input type="submit" value="Submit"/>
</form>
<script>
function removeElement(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function addField(containerId, fieldPrefix, template) {
    const container = document.getElementById(containerId);
    const count = container.children.length;
    const itemId = `${containerId}_${count}`;
    let html = `<div id="${itemId}">`;

    if (typeof template === "object" && template !== null && !Array.isArray(template)) {
        for (const key in template) {
            const name = `${fieldPrefix}[${count}].${key}`;
            html += `<label>${key}: <input name="${name}" value="" /></label><br>`;
        }
    } else {
        const name = `${fieldPrefix}[${count}]`;
        html += `<label><input name="${name}" value="" /></label><br>`;
    }

    html += `<button type="button" onclick="removeElement('${itemId}')">Delete</button><hr></div>`;
    container.insertAdjacentHTML('beforeend', html);
}
</script>
"""

if __name__ == "__main__":
    app.run(debug=True, port = 5001)
