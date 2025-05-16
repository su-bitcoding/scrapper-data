# from flask import Flask, render_template_string, request
# import json
# import re

# app = Flask(__name__)

# json_data = {}
# selected_fields = []


# @app.route("/", methods=["GET", "POST"])
# def upload_and_select():
#     global json_data
#     if request.method == "POST":
#         file = request.files.get("json_file")
#         if file and file.filename.endswith(".json"):
#             json_data = json.load(file)

#             if isinstance(json_data, list):
#                 # If the JSON is a list, flatten it to a dictionary
#                 json_data = {f"array_{i}": item for i, item in enumerate(json_data)}

#             field_options = list(flatten_keys(json_data))
#             return render_template_string(
#                 SELECT_FIELDS_TEMPLATE, field_options=field_options
#             )
#     return render_template_string(UPLOAD_TEMPLATE)


# @app.route("/generate_form", methods=["POST"])
# def generate_form():
#     global selected_fields

#     selected_fields = request.form.getlist("fields")
#     selected_data = extract_fields(json_data, selected_fields)
#     form_html = generate_form_html(selected_data)
#     return render_template_string(FORM_TEMPLATE, form_html=form_html)


# @app.route("/submit_form", methods=["POST"])
# def submit_form():
#     form_data = request.form.to_dict()
#     result = {}

#     for full_key, val in form_data.items():
#         # Try to infer the original type
#         if val.isdigit() and not val.startswith("0"):
#             detected_type = "int"
#             typed_val = int(val)
#         else:
#             try:
#                 if "." in val:
#                     typed_val = float(val)
#                     detected_type = "float"
#                 else:
#                     raise ValueError  # Force string if not a float
#             except ValueError:
#                 typed_val = val
#                 detected_type = "string"

#         result[full_key] = {"value": typed_val, "type": detected_type}

#     return f"<h3>Selected Data Submitted!</h3><pre>{json.dumps(result, indent=2)}</pre>"


# # ----------------------------
# # Utilities
# # ----------------------------


# def extract_fields(data, selected_keys, parent_key=""):
#     result = {}

#     for key, value in data.items():
#         full_key = f"{parent_key}.{key}" if parent_key else key

#         if isinstance(value, dict):
#             nested = extract_fields(value, selected_keys, full_key)
#             if nested:
#                 result[key] = nested
#         elif isinstance(value, list):
#             if full_key in selected_keys:
#                 result[key] = value
#             else:
#                 result_list = []
#                 for idx, item in enumerate(value):
#                     indexed_key = f"{full_key}[{idx}]"
#                     if isinstance(item, dict):
#                         nested = extract_fields(item, selected_keys, indexed_key)
#                         if nested:
#                             result_list.append(nested)
#                     else:
#                         if indexed_key in selected_keys:
#                             result_list.append(item)
#                 if result_list:
#                     result[key] = result_list

#         else:
#             if full_key in selected_keys:
#                 result[key] = value
#     return result


# def flatten_keys(data, parent_key=""):
#     keys = []
#     if isinstance(data, dict):
#         for key, value in data.items():
#             full_key = f"{parent_key}.{key}" if parent_key else key
#             if isinstance(value, dict):
#                 keys.extend(flatten_keys(value, full_key))
#             elif isinstance(value, list):
#                 keys.append(full_key)  # just add the list key itself, e.g., "roles"
#             else:
#                 keys.append(full_key)
#     if isinstance(data, list):
#         for idx, item in enumerate(data):
#             indexed_key = f"{parent_key}[{idx}]"
#             if isinstance(item, dict):
#                 keys.extend(flatten_keys(item, indexed_key))
#             else:
#                 keys.append(indexed_key)
#     return keys


# def generate_form_html(data, prefix=""):
#     html = ""
#     if isinstance(data, dict):
#         for key, value in data.items():
#             full_key = f"{prefix}.{key}" if prefix else key
#             if isinstance(value, dict):
#                 html += f"<fieldset><legend>{key}</legend>{generate_form_html(value, full_key)}</fieldset>"
#             elif isinstance(value, list):
#                 for i, item in enumerate(value):
#                     index_key = f"{full_key}[{i}]"
#                     if isinstance(item, dict):
#                         html += f"<fieldset><legend>{key}[{i}]</legend>{generate_form_html(item, index_key)}</fieldset>"
#                     else:
#                         html += f'<label>{index_key}</label><input type="text" name="{index_key}" value="{item}"><br>'

#             else:
#                 html += f'<label>{full_key}</label><input type="text" name="{full_key}" value="{value}"><br>'
#     return html


# def set_deep_value(data, dotted_key, value):
#     keys = re.split(r"\.(?![^\[]*\])", dotted_key)
#     current = data

#     for i, key in enumerate(keys):
#         if "[" in key and "]" in key:
#             # Handling array key like jobs[0]
#             dict_key = key.split("[")[0]
#             index = int(key[key.find("[") + 1 : key.find("]")])
#             if dict_key not in current or not isinstance(current[dict_key], list):
#                 current[dict_key] = []

#             while len(current[dict_key]) <= index:
#                 current[dict_key].append({})  # Now safe to append

#             if i == len(keys) - 1:
#                 current[dict_key][index] = value
#             else:
#                 current = current[dict_key][index]
#         else:
#             if i == len(keys) - 1:
#                 current[key] = value
#             else:
#                 if key not in current or not isinstance(current[key], dict):
#                     current[key] = {}
#                 current = current[key]


# # ----------------------------
# # Templates
# # ----------------------------

# UPLOAD_TEMPLATE = """
# <h2>Upload a JSON File</h2>
# <form method="POST" enctype="multipart/form-data">
#     <input type="file" name="json_file" accept="application/json">
#     <button type="submit">Upload</button>
# </form>
# """

# SELECT_FIELDS_TEMPLATE = """
# <h2>Select the fields you want to include</h2>
# <form method="POST" action="/generate_form">
#     {% for field in field_options %}
#         <label><input type="checkbox" name="fields" value="{{ field }}"> {{ field }}</label><br>
#     {% endfor %}
#     <button type="submit">Generate Form</button>
# </form>
# """

# FORM_TEMPLATE = """
# <h2>Generated Form</h2>
# <form method="POST" action="/submit_form">
#     {{ form_html | safe }}
#     <button type="submit">Submit</button>
# </form>
# """

# if __name__ == "__main__":
#     app.run(debug=True)

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------

# from flask import Flask, render_template_string, request
# import json

# app = Flask(__name__)

# json_data = {}


# @app.route("/", methods=["GET", "POST"])
# def upload_and_select():
#     global json_data
#     if request.method == "POST":
#         file = request.files.get("json_file")
#         if file and file.filename.endswith(".json"):
#             json_data = json.load(file)
#             return render_template_string(
#                 SELECT_FIELDS_TEMPLATE, json_data=json.dumps(json_data)
#             )
#     return render_template_string(UPLOAD_TEMPLATE)


# @app.route("/generate_form", methods=["POST"])
# def generate_form():
#     selected_fields = request.form.getlist("fields")
#     selected_data = extract_selected_fields(json_data, selected_fields)
#     form_html = render_form_fields(selected_data)
#     return render_template_string(FORM_TEMPLATE, form_html=form_html)


# @app.route("/submit_form", methods=["POST"])
# def submit_form():
#     form_data = request.form.to_dict(flat=False)
#     return f"<h3>Form Submitted</h3><pre>{json.dumps(form_data, indent=2)}</pre>"


# def extract_selected_fields(data, selected_keys, prefix=""):
#     result = {}
#     for key, val in data.items():
#         full_key = f"{prefix}.{key}" if prefix else key
#         if full_key in selected_keys:
#             result[key] = val
#         elif isinstance(val, dict):
#             nested = extract_selected_fields(val, selected_keys, full_key)
#             if nested:
#                 result[key] = nested
#         elif isinstance(val, list):
#             if val and isinstance(val[0], dict):
#                 result[key] = [
#                     extract_selected_fields(item, selected_keys, full_key)
#                     for item in val
#                 ]
#             elif full_key in selected_keys:
#                 result[key] = val
#     return result


# def render_form_fields(data, prefix=""):
#     html = ""
#     if isinstance(data, dict):
#         for key, val in data.items():
#             full_key = f"{prefix}.{key}" if prefix else key
#             if isinstance(val, dict):
#                 html += f"<fieldset><legend>{key}</legend>"
#                 html += render_form_fields(val, full_key)
#                 html += "</fieldset>"
#             elif isinstance(val, list):
#                 html += f"<fieldset><legend>{key} (Add more below)</legend>"
#                 for i, item in enumerate(val):
#                     item_prefix = f"{full_key}[{i}]"
#                     if isinstance(item, dict):
#                         html += render_form_fields(item, item_prefix)
#                     else:
#                         html += f"<label>{key} {i+1}: <input name='{item_prefix}' value='{item}' /></label><br>"
#                 html += f"<button type='button' onclick='addInput(\"{full_key}\")'>Add More</button>"
#                 html += "</fieldset>"
#             else:
#                 html += f"<label>{key}: <input name='{full_key}' value='{val}' /></label><br>"
#     return html


# UPLOAD_TEMPLATE = """
# <!doctype html>
# <title>Upload JSON</title>
# <h2>Upload JSON file</h2>
# <form method=post enctype=multipart/form-data>
#   <input type=file name=json_file>
#   <input type=submit value=Upload>
# </form>
# """

# SELECT_FIELDS_TEMPLATE = """
# <!doctype html>
# <title>Select Fields</title>
# <h2>Select Fields to Include</h2>
# <form method=post action="/generate_form">
#   <div id="json-tree"></div>
#   <input type=submit value="Generate Form">
# </form>
# <script>
# const data = {{ json_data|safe }};
# const container = document.getElementById('json-tree');

# function buildCheckboxTree(obj, prefix = '') {
#     const ul = document.createElement('ul');

#     Object.entries(obj).forEach(([key, val]) => {
#         const li = document.createElement('li');
#         const fullKey = prefix ? `${prefix}.${key}` : key;

#         const checkbox = document.createElement('input');
#         checkbox.type = 'checkbox';
#         checkbox.name = 'fields';
#         checkbox.value = fullKey;
#         checkbox.id = fullKey;
#         checkbox.addEventListener('change', () => toggleNested(li, checkbox.checked));

#         const label = document.createElement('label');
#         label.textContent = key;
#         label.htmlFor = fullKey;

#         li.appendChild(checkbox);
#         li.appendChild(label);

#         if (typeof val === 'object' && val !== null) {
#             li.appendChild(buildCheckboxTree(val, fullKey));
#         }

#         ul.appendChild(li);
#     });

#     return ul;
# }

# function toggleNested(li, checked) {
#     const checkboxes = li.querySelectorAll('input[type="checkbox"]');
#     checkboxes.forEach(cb => cb.checked = checked);
# }

# container.appendChild(buildCheckboxTree(data));
# </script>
# """

# FORM_TEMPLATE = """
# <!doctype html>
# <title>Generated Form</title>
# <h2>Generated Form</h2>
# <form method=post action="/submit_form">
#   {{ form_html|safe }}
#   <br><input type=submit value="Submit">
# </form>
# <script>
# function addInput(prefix) {
#     const fieldset = document.querySelector(`legend:contains('${prefix}')`).parentElement;
#     const idx = fieldset.querySelectorAll('input').length;
#     const input = document.createElement('input');
#     input.name = `${prefix}[${idx}]`;
#     input.placeholder = 'Add value';
#     fieldset.appendChild(document.createElement('br'));
#     fieldset.appendChild(input);
# }
# </script>
# """

# if __name__ == "__main__":
#     app.run(debug=True)


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
            json_data = json.load(file)
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
    app.run(debug=True)
