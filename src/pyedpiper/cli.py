import argparse, importlib.util, os, sys
from .convert import all_parts_main


def validate_python_module(module_name: str) -> str:
    """
    Validates that the given Python module exists.

    Parameters
    ----------
    module_name :
        The name of the Python module to validate.

    Raises
    ------
    argparse.ArgumentTypeError
        If the module does not exist.
    """
    if not importlib.util.find_spec(module_name):
        raise argparse.ArgumentTypeError(f"The Python module '{module_name}' does not exist.")
    return module_name


def validate_output_path(path: str, overwrite: bool) -> str:
    """
    Validates the output path for the R file.

    Parameters
    ----------
    path :
        The path to the output R file.
    overwrite :
        Whether overwriting is allowed.

    Raises
    ------
    argparse.ArgumentTypeError
        If the file exists and overwriting is not allowed.
    """
    if os.path.exists(path) and not overwrite:
        raise argparse.ArgumentTypeError(
            f"The file '{path}' already exists and overwriting is not allowed."
        )
    return path


def parse_arguments() -> dict:
    """
    Parses command-line arguments for the Python-to-R module conversion script.

    Returns
    -------
    argparse.Namespace
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Convert a Python module to an R script.")
    parser.add_argument(
        "module_name",
        type=validate_python_module,
        help="The name of the Python module to convert to R.",
    )
    parser.add_argument("output_path", type=str, help="The path to the output R file.")
    parser.add_argument(
        "--allow_overwrite",
        action="store_false",
        help="Overwrite the output file if it already exists.",
    )

    args = parser.parse_args()

    # Validate output path with overwrite option
    validate_output_path(args.output_path, not args.allow_overwrite)

    args = vars(args)

    return args


def main():
    try:
        args = parse_arguments()
        all_parts_main(args["module_name"], args["output_path"], args["allow_overwrite"])
    except argparse.ArgumentTypeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
