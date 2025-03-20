COVERAGE_PROCESS_START="/Users/druc594/Desktop/NeedleallPy/.coveragerc" \
    pytest -s PkgContainer/tests/tests.py &&
    coverage combine &&
    coverage html \
        --skip-empty \
        --rcfile="/Users/druc594/Desktop/NeedleallPy/.coveragerc" \
        --omit "/**/*site-packages*/**"
