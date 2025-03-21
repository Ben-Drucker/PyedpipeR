"""Functions that run R code to create an R package and document it."""

import re
from importlib import metadata as meta
from rpy2.robjects import r


def create_package_skeleton(package_root_path: str, pkg_name: str, pkg_name_rnorm: str):
    """Create an R package skeleton and takes into account the metadata of the Python package.

    Parameters
    ----------
    ``package_root_path`` :
        _description_
    ``pkg_name`` :
        _description_
    ``pkg_name_rnorm`` :
        _description_

    Returns
    -------
        _description_
    """
    metadata_dict = dict(meta.metadata(pkg_name).__dict__["_headers"])
    r_desc_to_pyproj_mapping = {
        "Title": "Name",
        "Version": "Version",
        "Description": "Description",
        "License": "License-File",
    }

    def processor(x):
        x = re.sub(r"[\n\t]", " ", x)
        x = re.sub(r"[^A-Za-z0-9_+\-/%\.:\s!\(\),\"\"\'\'=\[\]\{\}\<\>@&\?]", " ", x)
        x = re.sub(r"   (raw|python|r)", " ", x)
        x = re.sub(r"\[*\!\[.*?\]\(.*?\)\]*(\(.*?\))*", " ", x)
        x = re.sub("  *", " ", x)
        x = x.strip()
        return f'"{x}"'

    def authoReR(auth):
        # fn, ln, em = auth.split(" ")
        return f'"Maintainer" = "{auth}"'

        em = re.sub(r"[<>]", "", em)
        personhood = f'person(given="{fn}", family="{ln}", email = "{em}", role = c("aut"))'
        return personhood

    raw_vector_list = [
        f'"{k}" = {processor(metadata_dict[v])}' for k, v in r_desc_to_pyproj_mapping.items()
    ]
    raw_vector_list.append(f'"Name" = "{pkg_name_rnorm}"')
    raw_vector_list.append(authoReR(metadata_dict["Author-email"]))

    r_vector = f"list({', '.join(raw_vector_list)})"

    r_to_execute = (
        f'options("needs.promptUser = FALSE)"); usethis::create_package("{package_root_path}",'
        f" fields = {r_vector})"
    )
    r(r_to_execute)


def do_roxygen(package_root: str):
    r_to_execute = f'devtools::document("{package_root}")'
    r('options("needs.promptUser = FALSE)")')
    r(r_to_execute)
