from flask import Flask, render_template_string, request
import json

app = Flask(__name__)

json_data = {}


@app.route("/", methods=["GET", "POST"])
def upload_and_select():
    global json_data
    if request.method == "POST":
        file = request.files.get("json_file")
        if file and file.filename.endswith(".json"):
            try:
                json_data = json.load(file)
                return render_template_string(
                    SELECT_FIELDS_TEMPLATE, json_data=json.dumps(json_data)
                )
            except json.JSONDecodeError as e:
                error_message = f"""
                    <div style="color: red; margin-bottom: 20px;">
                        Error: Invalid JSON format. Please ensure:
                        <ul>
                            <li>All property names are enclosed in double quotes</li>
                            <li>All strings are enclosed in double quotes</li>
                            <li>No trailing commas</li>
                            <li>Valid JSON syntax</li>
                        </ul>
                        Technical details: {str(e)}
                    </div>
                """
                return render_template_string(UPLOAD_TEMPLATE + error_message)
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
        elif isinstance(val, list) and val and isinstance(val[0], dict):
            # For arrays of objects, collect all unique keys
            unique_keys = set()
            for item in val:
                unique_keys.update(item.keys())
            
            # Create a list to store filtered items
            filtered_items = []
            for item in val:
                filtered_item = {}
                for ukey in unique_keys:
                    item_key = f"{full_key}.{ukey}"
                    if item_key in selected_keys and ukey in item:
                        filtered_item[ukey] = item[ukey]
                if filtered_item:
                    filtered_items.append(filtered_item)
            
            if filtered_items:
                result[key] = filtered_items
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
            elif isinstance(val, list) and val and isinstance(val[0], dict):
                # Get unique keys from all array items
                unique_keys = sorted(set().union(*(item.keys() for item in val)))
                
                container_id = f"{full_key.replace('.', '_')}_container"
                html += f"<fieldset><label>{key}</label><div id='{container_id}'>"
                
                # Create a template object with all possible fields
                template_obj = {k: "" for k in unique_keys}
                
                # Add fields for first item only
                item_id = f"{container_id}_0"
                html += f"<div id='{item_id}'>"
                for field_key in unique_keys:
                    input_name = f"{full_key}[0].{field_key}"
                    field_value = val[0].get(field_key, "") if val else ""
                    html += f"<label>{field_key}: <input name='{input_name}' value='{field_value}' /></label><br>"
                html += f"<button type='button' onclick='removeElement(\"{item_id}\")'>Delete</button><hr></div>"
                
                # Add button with template containing all possible fields
                html += f"</div><button type='button' onclick='addField(\"{container_id}\", \"{full_key}\", {json.dumps(template_obj)})'>Add More</button>"
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

        if (Array.isArray(val) && val.length > 0 && typeof val[0] === 'object') {
            // For arrays of objects, merge all unique keys
            const mergedObj = {};
            val.forEach(item => {
                Object.keys(item).forEach(k => {
                    mergedObj[k] = item[k];
                });
            });
            li.appendChild(buildCheckboxTree(mergedObj, fullKey));
        } else if (typeof val === 'object' && val !== null) {
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
    
    // Add all fields in the template
    for (const key in template) {
        html += `<label>${key}: <input name="${fieldPrefix}[${count}].${key}" value="" /></label><br>`;
    }
    
    html += `<button type="button" onclick="removeElement('${itemId}')">Delete</button><hr></div>`;
    container.insertAdjacentHTML('beforeend', html);
}
</script>
<style>
fieldset { margin: 10px 0; padding: 10px; border: 1px solid #ccc; }
label { display: block; margin: 5px 0; }
input { margin-left: 5px; }
button { margin: 5px 0; }
hr { margin: 10px 0; }
</style>
"""

if __name__ == "__main__":
    app.run(debug=True)
