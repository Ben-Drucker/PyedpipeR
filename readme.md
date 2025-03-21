### Link to full API specification: [API](https://ben-drucker.github.io/PyedpipeR/)

### Tool Usage
Using CLI:
```sh
$ python[3] -m pyedpiper input_python_package output_R_package [--allow_overwrite]
```

CLI Help Page:

```raw
Convert a Python module to an R script.

positional arguments:
  input_py_package   The name of the Python module to convert to R.
  output_r_package   The path to the output R file.

options:
  -h, --help         show this help message and exit
  --allow_overwrite  Overwrite the output file if it already exists.
```
