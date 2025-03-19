import importlib, inspect, os, pkgutil, re, shutil, textwrap, types


def extract_docstrings(module_name):
    """
    Extract docstrings from a Python module.

    Args:
        module_name (str): The name of the module to extract docstrings from.

    Returns:
        dict: A dictionary with function names as keys and their docstrings as values.
    """
    module = importlib.import_module(module_name)
    docstrings: dict[str, str] = {}
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and obj.__module__ == module_name:
            docstrings[name] = str(inspect.getdoc(obj))
        if (
            inspect.isclass(obj)
            and obj.__module__ == module_name
            and "no_convert" not in obj.__dict__
        ):
            for class_name, class_obj in inspect.getmembers(obj):
                if not re.match(r"^_", class_name) and inspect.isfunction(class_obj):
                    docstrings[class_name] = str(inspect.getdoc(class_obj))
    replaced = {k: v.replace("None", "") for k, v in docstrings.items()}
    return replaced


def to_roxygen(docstring: str):
    if not docstring:
        return "", []
    ds_without_header = re.sub(r"Parameters\n\-+", "", docstring)
    ds_with_params = re.sub(
        r"\s+``([a-zA-Z_][a-zA-Z0-9_]*)``\s*:\n\s*([.\n]*)", r"\n@param \1 ", ds_without_header
    )
    ds_with_value = re.sub(r"Returns\n\-+\n", "@returns ", ds_with_params)
    ds_with_examples = re.sub(r"Examples\n\-+\n", "@examples ", ds_with_value)
    ds_with_export = ds_with_examples + "@export"
    ds_with_throws = re.sub(r"Raises\n\-+\n", r"", ds_with_export)
    ds_with_throws_2 = re.sub(r"`(.*)` :\n\s*(.*)", r"\n@throws \1 \2", ds_with_throws)
    ds_with_notes = re.sub(r"Notes\n\-+\n", r"@details ", ds_with_throws_2)
    # ds_with_comments = re.sub(r"^(.)", r"#' \1", ds_with_throws)
    ds_no_tabs = re.sub(r"\s{2}", "", ds_with_notes)
    sections = re.split(r"@", ds_no_tabs)
    sections = [sections[0]] + [f"@{s}" for s in sections[1:]]
    ds_fill = [
        (
            textwrap.fill(
                s,
                width=70,
                initial_indent="#' ",
                subsequent_indent="#'   ",
            )
            if not re.match(r"^@examples", s)
            else "#' @examples\n#'"
        )
        for s in sections
    ]
    ds_fill_2 = []
    for i in range(len(ds_fill)):
        if main_search := re.search("@(param|returns|throws|export)", ds_fill[i]):
            if not re.search(main_search.group(1), ds_fill[i - 1]):
                ds_fill_2.append("#'\n" + ds_fill[i])
            else:
                ds_fill_2.append(ds_fill[i])
        else:
            ds_fill_2.append(ds_fill[i])

    out_str = "\n".join(ds_fill_2)
    if out_str.startswith("\n#'\n"):
        out_str = out_str[3:]
    if out_str.endswith("#'\n"):
        out_str = out_str[:-3]

    return out_str, re.findall(r"@param ([^\s]*)", out_str)


def main_convert(root_module_name: str):
    module_structure = {}
    root_module = importlib.import_module(root_module_name)

    def recurse_in_module(module_obj: types.ModuleType, level):
        nonlocal module_structure
        # Base case
        if not hasattr(module_obj, "__path__"):
            r_fns = create_R_functions(module_obj.__name__)
            module_structure[module_obj.__name__] = r_fns
            return r_fns
        else:
            package_walk = list(pkgutil.walk_packages(module_obj.__path__))
            results = []
            for _, module_name, _ in package_walk:
                if not re.search(r"^__", module_name) and not re.search(r"tests\.", module_name):
                    module_str = module_obj.__name__ + "." + module_name
                    print(
                        f"{f'Working on {module_str} at level {level}':{' '}<{shutil.get_terminal_size().columns}}"
                    )
                    module_obj_inner = importlib.import_module(module_str)
                    results.append(recurse_in_module(module_obj_inner, level + 1))
            # module_structure[module_obj.__name__] = results

    recurse_in_module(root_module, 0)
    return module_structure


def create_R_files(module_structure, root_dir="R", exclude_top_level=True, overwrite=False):
    for module_name, r_fns in module_structure.items():
        if exclude_top_level:
            start_idx = 1
        else:
            start_idx = 0
        module_folders = module_name.split(".")[start_idx:-1]
        module_folders_joined = os.path.join(root_dir, *module_folders)
        if not os.path.exists(module_folders_joined) or overwrite:
            os.makedirs(module_folders_joined, exist_ok=True)

        full_file_path = os.path.join(module_folders_joined, module_name.split(".")[-1] + ".R")
        if not os.path.exists(full_file_path) or overwrite:
            with open(full_file_path, "w") as f:
                f.write(f'py_pkg <- reticulate::import("{module_name}")\n\n')
                f.write("\n\n\n\n".join(r_fns))


def create_R_functions(module_name: str):
    docstrings = extract_docstrings(module_name)
    roxygenized = {name: to_roxygen(docstring) for name, docstring in docstrings.items()}
    fn_strings: list[str] = []
    for name, (ds, params) in roxygenized.items():
        if re.search("^_", name):
            new_name = f"`{name}`"
        else:
            new_name = name
        if not params:
            param_section = "()"
        else:
            param_section = (
                f"(\n                {',\n                '.join(params)}\n            )"
            )
        fn_string = f"""{ds}\n{new_name} <- function{re.sub("    $", "", param_section)} {{
        return(
            py_pkg${new_name}{param_section}
        )
  }}"""
        fn_strings.append(fn_string)

    return fn_strings


if __name__ == "__main__":
    module_structure = main_convert("uniprot_tools")
    create_R_files(module_structure, overwrite=True, root_dir="../R")
    pass
