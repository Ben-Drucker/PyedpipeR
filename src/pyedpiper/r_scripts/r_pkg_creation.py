from importlib import metadata as meta
from rpy2.robjects import r
import re


def create_package_skeleton(package_root_path: str, pkg_name: str):
    metadata_dict = dict(meta.metadata(pkg_name).__dict__["_headers"])
    r_desc_to_pyproj_mapping = {
        "Package": "Name",
        "Title": "Name",
        "Version": "Version",
        "Description": "Description",
        "License": "License-File",
        "Authors@R": "Author-email",
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
        fn, ln, em = auth.split(" ")
        em = re.sub(r"[<>]", "", em)
        personhood = f'person(given="{fn}", family="{ln}", email = "{em}", role = c("aut"))'
        return personhood

    r_vector = (
        f"list({', '.join([f'"{k}" = {processor(metadata_dict[v]) if v != "Author-email" else authoReR(metadata_dict[v])}' for k, v in r_desc_to_pyproj_mapping.items()])})"
    )

    r_to_execute = f'usethis::create_package("{package_root_path}", fields = {r_vector})'
    r('options("needs.promptUser = FALSE)")')
    r(r_to_execute)


def do_roxygen(package_root: str):
    r_to_execute = f'devtools::document("{package_root}")'
    r('options("needs.promptUser = FALSE)")')
    r(r_to_execute)
