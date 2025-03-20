"""Command-line interface for the Python-to-R module conversion script."""

import argparse


def validate_python_module(input_py_package: str) -> str:
    """
    Validates that the given Python module exists.

    Parameters
    ----------
    input_py_package :
        The name of the Python module to validate.

    Raises
    ------
    argparse.ArgumentTypeError
        If the module does not exist.
    """
    if not importlib.util.find_spec(input_py_package):
        raise argparse.ArgumentTypeError(f"The Python module '{input_py_package}' does not exist.")
    return input_py_package


def validate_output_r_package(path: str, overwrite: bool) -> str:
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
        The parsed arguments mapping to their values.
    """
    parser = argparse.ArgumentParser(description="Convert a Python module to an R script.")
    parser.add_argument(
        "input_py_package",
        type=validate_python_module,
        help="The name of the Python module to convert to R.",
    )
    parser.add_argument("output_r_package", type=str, help="The path to the output R file.")
    parser.add_argument(
        "--allow_overwrite",
        action="store_false",
        help="Overwrite the output file if it already exists.",
    )

    args = parser.parse_args()

    # Validate output path with overwrite option
    validate_output_r_package(args.output_r_package, not args.allow_overwrite)

    args = vars(args)

    return args


def main():
    """The main function for the Python-to-R module conversion script. It parses command-line \
        arguments and calls the conversion function.
    """
    try:
        args = parse_arguments()
        all_parts_main(args["input_py_package"], args["output_r_package"], args["allow_overwrite"])
    except argparse.ArgumentTypeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    print("Importing modules and starting R...", end = "\r")
    print("                                   ", end = "\r")
    import importlib.util, os, sys
    from .convert import all_parts_main

    main()
