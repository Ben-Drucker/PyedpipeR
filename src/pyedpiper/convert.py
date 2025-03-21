import collections.abc, importlib, inspect, os, pkgutil, re, shutil, textwrap, types
from .r_scripts.r_pkg_creation import create_package_skeleton, do_roxygen
from typing import Any, Sequence, Union

# Define new type "convertable types"
convertable_types = Union[
    str,
    int,
    float,
    bool,
    None,
    tuple,
    list,
    set,
    dict,
    inspect._empty,  # type: ignore
]


def convert_default_args(default_args: list[convertable_types]) -> Sequence[convertable_types]:
    """Convert default arguments to string format.

    Parameters
    ----------
    ``default_args`` :
        The default arguments to convert. Can be either a "singleton" (i.e. a single value) or a \
            list of values.


    Returns
    -------
        If returning a singleton, returns the converted default argument in string format. If \
            returning a list, returns a list of converted default arguments in string format. \
            One exception is if the default argument is `inspect._empty`, i.e., no default \
            argument is provided, in which case it returns `inspect._empty` instead of a string.
    """
    result = recurse_in_convert_default_args(default_args)
    assert isinstance(result, list)
    return result


def recurse_in_convert_default_args(
    default_args: convertable_types | list[convertable_types],
) -> str | inspect._empty | list[str | inspect._empty]:  # type: ignore
    """Sister function to `convert_default_args` that recursively converts default arguments.

    Parameters
    ----------
    ``default_args`` :
        The default arguments to convert. Can be either a "singleton" (i.e. a single value) or a \
            list of values.

    Returns
    -------
        If returning a singleton, returns the converted default argument in string format. If \
            returning a list, returns a list of converted default arguments in string format. \
            One exception is if the default argument is `inspect._empty`, i.e., no default \
            argument is provided, in which case it returns `inspect._empty` instead of a string.
    Raises
    ------
        ValueError: If the default argument type is not supported.
    """
    r_args = []
    singleton = False
    if not isinstance(default_args, collections.abc.Collection):
        default_args = [default_args]
        singleton = True
    for a in default_args:
        conversion: str | None | inspect._empty = None  # type: ignore
        if a == inspect._empty:  # type: ignore
            conversion = inspect._empty()  # type: ignore
        if isinstance(a, str):
            conversion = f'"{a}"'
        if isinstance(a, float):
            conversion = f"{a}"
        if isinstance(a, int):
            conversion = f"{a}L"
        if isinstance(a, bool):
            conversion = str(a).upper()
        if a is None:
            conversion = "NULL"
        if isinstance(a, (tuple, list, set)):
            all_converted = recurse_in_convert_default_args(a)
            assert isinstance(all_converted, list) and all(
                isinstance(x, str) for x in all_converted
            ), f"Expected all elements to be strings, got {all_converted}"
            conversion = f"list({', '.join([str(x) for x in all_converted])})"
        if isinstance(a, dict):
            conversion = (
                f"list({', '.join([f'"{k}" = {convert_default_args(v)}' for k, v in a.items()])})"
            )

        if conversion is None:
            raise ValueError(f"Unsupported default argument type for '{a}': {type(a)}")

        assert conversion is not None
        if singleton:
            return conversion
        else:
            r_args.append(conversion)

    return r_args


# test_args = [1, 2.0, "a", True, None, (1, 2), [1, 2], {1: 2, 3: 4}, {1, 2}, [((1, 2), 3)]]


def extract_docstrings_and_default_args(
    module_name,
) -> tuple[dict[str, str], dict[str, dict[str, convertable_types]]]:
    """
    Extract docstrings from a Python module.

    Parameters
    ----------
        module_name : The name of the module to extract docstrings from.

    Returns
    -------
        A tuple of (1) a dictionary of function names mapped to their docstrings and \
            (2) a dictionary of function names mapped to sub-dicts, each of which map argument \
            names to their default values.

    """
    module = importlib.import_module(module_name)
    docstrings: dict[str, str] = {}
    default_args: dict[str, Any] = {}
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and obj.__module__ == module_name:

            docstrings[name] = str(inspect.getdoc(obj))

            param_names = []
            param_values = []
            for parameter_name, parameter in dict(inspect.signature(obj).parameters).items():
                param_names.append(parameter_name)
                param_values.append(parameter.default)

            param_values_converted = convert_default_args(param_values)
            assert isinstance(param_values_converted, list)
            default_args[name] = dict(zip(param_names, param_values_converted))

        # TODO: Add class support

        # if (
        #     inspect.isclass(obj)
        #     and obj.__module__ == module_name
        #     and "no_convert" not in obj.__dict__
        # ):
        #     for class_name, class_obj in inspect.getmembers(obj):
        #         if not re.match(r"^_", class_name) and inspect.isfunction(class_obj):
        #             docstrings[class_name] = str(inspect.getdoc(class_obj))
    replaced = {k: v.replace("None", "") for k, v in docstrings.items()}
    return replaced, default_args


def to_roxygen(docstring: str) -> tuple[str, list[str]]:
    """Convert a Python docstring to a roxygen2-style R docstring.

    Parameters
    ----------
    ``docstring`` :
        The Python docstring to convert.

    Returns
    -------
        Tuple of (1) The converted R docstring, as an R-style comment and (2) a list of parameter \
            names.
    """
    if not docstring:
        return "", []

    ds_without_header = re.sub(r"Parameters\n\-+", "", docstring)
    ds_with_params = re.sub(
        r"\s+``([a-zA-Z_][a-zA-Z0-9_]*)``\s*:\n\s*([.\n]*)", r"\n@param \1 ", ds_without_header
    )
    ds_with_value = re.sub(r"Returns\n\-+\n", "@returns ", ds_with_params)
    ds_with_examples = re.sub(r"Examples\n\-+\n", "@examples ", ds_with_value)
    ds_with_export = ds_with_examples + "@export"
    ds_with_section = re.sub(r"Raises\n\-+\n", r"", ds_with_export)
    ds_with_section_2 = re.sub(r"`(.*)` :\n\s*(.*)", r"\n@section Throws: \1 \2", ds_with_section)
    ds_with_notes = re.sub(r"Notes\n\-+\n", r"@details ", ds_with_section_2)
    # ds_with_comments = re.sub(r"^(.)", r"#' \1", ds_with_section)
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
        if main_search := re.search("@(param|returns|section|export)", ds_fill[i]):
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

    found_all: list[str] = re.findall(r"@param ([^\s]*)", out_str)

    return out_str, found_all


def main_convert(root_module_name: str) -> dict[str, list[str]]:
    """Convert a Python module to an R script.

    Parameters
    ----------
    ``root_module_name`` :
        The name of the root Python module to convert.

    Returns
    -------
        A dictionary with the module names as keys and their R functions as values.
    """
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
                        f"{f'Working on {module_str} at level {level}':{' '}<{shutil.get_terminal_size().columns}}",
                        end="\r",
                    )
                    module_obj_inner = importlib.import_module(module_str)
                    results.append(recurse_in_module(module_obj_inner, level + 1))
            # module_structure[module_obj.__name__] = results

    recurse_in_module(root_module, 0)
    return module_structure


def create_R_files(module_structure, root_dir="RPkg", exclude_top_level=True, overwrite=False):
    root_dir_orig = root_dir
    root_dir = os.path.join(root_dir, "R")
    if os.path.exists(root_dir) or overwrite:
        shutil.rmtree(root_dir_orig)
        # os.makedirs(root_dir, exist_ok=True)
    basic_mod_name = next(iter(module_structure.keys())).split(".")[0]
    ok_r_name = re.sub(r"_", ".", basic_mod_name)
    create_package_skeleton(root_dir_orig, basic_mod_name, ok_r_name)
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
                # f.write(f'py_pkg <- reticulate::import("{module_name}")\n\n')
                f.write("\n\n".join(r_fns))
    do_roxygen(root_dir)


def create_R_functions(module_name: str):
    docstrings, default_args = extract_docstrings_and_default_args(module_name)
    roxygenized = {name: to_roxygen(docstring)[0] for (name, docstring), in zip(docstrings.items())}
    fn_strings: list[str] = []
    for name, ds in roxygenized.items():
        converted_defaults = default_args[name].values()
        converted_defaults_strings = []
        for c in converted_defaults:
            if isinstance(c, inspect._empty):  # type: ignore
                converted_default_str = ""
            else:
                converted_default_str = f" = {c}"
            converted_defaults_strings.append(converted_default_str)

        params = list(default_args[name].keys())

        assert len(converted_defaults_strings) == len(params), (
            f"Expected {len(params)} default (can be blank) arguments, got"
            f" {len(converted_defaults_strings)}"
        )

        params_with_defaults = [f"{p}{d}" for p, d in zip(params, converted_defaults_strings)]

        if re.search("^_", name):
            new_name = f"`{name}`"
        else:
            new_name = name
        if not params:
            param_section = param_section_w_parameters = "()"
        else:
            param_section = (
                f"(\n                {',\n                '.join(params)}\n            )"
            )
            param_section_w_parameters = (
                f"(\n                {',\n                '.join(params_with_defaults)}\n        "
                "    )"
            )
        fn_string = f"""{ds}\n{new_name} <- function{re.sub("    $", "", param_section_w_parameters)} {{
        py_pkg <- reticulate::import("{module_name}")
        return(
            py_pkg${new_name}{param_section}
        )
  }}"""
        fn_strings.append(fn_string)

    return fn_strings


def all_parts_main(module_name: str, output_path: str, allow_overwrite: bool):
    module_structure = main_convert(module_name)
    create_R_files(module_structure, output_path, overwrite=allow_overwrite)


if __name__ == "__main__":
    all_parts_main("uniprot_tools", "R/", True)
